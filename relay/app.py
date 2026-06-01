"""Relais TradingView → Telegram (signal-only, semi-manuel).

Reçoit le webhook de l'alerte Pine, applique le Risk Manager prop firm,
formate un message clair et l'envoie sur Telegram.

Lancer :  uvicorn app:app --host 0.0.0.0 --port 8000
Exposer publiquement (TradingView Pro+ requis pour les webhooks) :
  - ngrok http 8000   (dev)
  - ou un petit VPS / Render / Railway   (prod)
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import httpx
import yaml
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request

import risk_manager as rm
from models import AccountState, Signal

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
SECRET = os.getenv("WEBHOOK_SECRET", "CHANGE_ME")

BASE = Path(__file__).parent
CONFIG_PATH = BASE / "config.yaml"
STATE_PATH = BASE / "state.json"

app = FastAPI(title="Prop Firm Signal Relay")

EMOJI = {"long": "🟢 LONG", "short": "🔴 SHORT"}
LEVEL_EMOJI = {rm.OK: "✅", rm.WARN: "⚠️", rm.BLOCK: "⛔"}


# ---------------------------------------------------------------- état comptes
def load_accounts() -> dict[str, AccountState]:
    """État courant des comptes : state.json prioritaire, sinon config.yaml."""
    if STATE_PATH.exists():
        raw = json.loads(STATE_PATH.read_text())
    else:
        cfg = yaml.safe_load(CONFIG_PATH.read_text())
        raw = cfg.get("accounts", [])
    return {a["name"]: AccountState(**a) for a in raw}


def save_accounts(accounts: dict[str, AccountState]) -> None:
    data = [a.model_dump() for a in accounts.values()]
    STATE_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False))


# ------------------------------------------------------------------- telegram
async def send_telegram(text: str) -> None:
    if not BOT_TOKEN or not CHAT_ID:
        print("[telegram] token/chat manquant — message non envoyé :\n", text)
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(url, json={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        })
        if r.status_code != 200:
            print("[telegram] erreur:", r.status_code, r.text)


STRAT_NAME = {"S1": "Liquidité", "S2": "Pivot", "EW": "Elliott"}
PHASE_HEAD = {
    "breakeven": "🔁 PASSE AU BREAKEVEN",
    "tp": "🎯 TP ATTEINT",
    "sl": "🛑 INVALIDATION / SL",
}


def format_message(sig: Signal, verdicts: list[rm.Verdict]) -> str:
    badge = "⚙️ FUTURES" if sig.market == "futures" else "💱 FOREX"
    strat_name = STRAT_NAME.get(sig.strat, sig.strat)

    # Alertes de gestion (breakeven / tp / sl) : message court
    if sig.phase in PHASE_HEAD:
        return (
            f"<b>{PHASE_HEAD[sig.phase]}</b>  ·  {badge}\n"
            f"{sig.side.upper()} <b>{sig.sym}</b> ({strat_name})\n"
            f"Entrée <code>{sig.entry}</code>  SL <code>{sig.sl}</code>  TP <code>{sig.tp}</code>"
        )

    # Phase entrée : carte complète
    head = EMOJI.get(sig.side, sig.side.upper())
    lines = [
        f"<b>{head}  {sig.sym}</b>  · {strat_name}  ·  {badge}",
        f"Taille : <b>{sig.size}</b>   Score : <b>{sig.score}</b>   R:R <b>{sig.rr}</b>",
        "",
        f"🎯 Entrée : <code>{sig.entry}</code>",
        f"🛑 SL : <code>{sig.sl}</code>",
        f"🏁 TP : <code>{sig.tp}</code>",
    ]
    for v in verdicts:
        lines.append("")
        lines.append(f"{LEVEL_EMOJI[v.level]} <b>{v.account}</b>")
        for n in v.notes:
            lines.append(f"   • {n}")
    return "\n".join(lines)


# -------------------------------------------------------------------- routes
@app.get("/health")
async def health() -> dict:
    return {"ok": True, "accounts": list(load_accounts().keys())}


@app.post("/webhook")
async def webhook(request: Request) -> dict:
    # TradingView envoie le corps en texte brut (JSON dans le message d'alerte)
    body = (await request.body()).decode("utf-8").strip()
    try:
        sig = Signal(**json.loads(body))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"payload invalide: {exc}") from exc

    if sig.secret != SECRET:
        raise HTTPException(403, "secret invalide")

    # Risk Manager prop firm : seulement pour les futures.
    # Le Forex (CFD) part en signal pur, sans les règles de drawdown EOD.
    verdicts: list[rm.Verdict] = []
    if sig.market == "futures":
        accounts = load_accounts()
        verdicts = [rm.evaluate(acc, sig) for acc in accounts.values() if acc.enabled]

    await send_telegram(format_message(sig, verdicts))
    return {"sent": True, "market": sig.market, "phase": sig.phase,
            "verdicts": [{v.account: v.level} for v in verdicts]}


@app.post("/state")
async def update_state(request: Request) -> dict:
    """Mets à jour un compte. Body JSON : {"name": "...", "balance": ..., ...}."""
    patch = await request.json()
    name = patch.get("name")
    accounts = load_accounts()
    if name not in accounts:
        raise HTTPException(404, f"compte inconnu: {name}")
    cur = accounts[name].model_dump()
    cur.update({k: v for k, v in patch.items() if k in cur})
    accounts[name] = AccountState(**cur)
    save_accounts(accounts)
    return {"updated": name, "state": accounts[name].model_dump()}
