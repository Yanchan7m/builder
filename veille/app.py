"""
Bot de veille AXONE.

Se connecte à Telegram avec TON compte (session utilisateur Telethon), surveille
les canaux listés dans config.yaml, et relaie dans TON canal uniquement les
messages qui parlent de $/€, indices/actions, or, IPO ou crypto.

Tourne en service web (FastAPI) pour rester compatible avec l'hébergement gratuit
Render + le keep-alive GitHub Actions, comme le bot AXONE.
"""
import logging
import os
import re
import unicodedata
from collections import deque
from contextlib import asynccontextmanager

import httpx
import yaml
from dotenv import load_dotenv
from fastapi import FastAPI
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
)
log = logging.getLogger("veille")

load_dotenv()

# --- Secrets / réglages (variables d'environnement) ---
API_ID = int(os.environ.get("TELETHON_API_ID", "0"))
API_HASH = os.environ.get("TELETHON_API_HASH", "")
SESSION = os.environ.get("TELETHON_SESSION", "")

# Envoi des alertes : via le bot Telegram (comme AXONE).
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")  # @ton_canal ou son id numérique

# --- Config (canaux + mots-clés) ---
HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "config.yaml"), encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

SOURCES = [s.lstrip("@") for s in CONFIG.get("sources", [])]
KEYWORDS = CONFIG.get("keywords", {})
ANTI_DOUBLON = CONFIG.get("anti_doublon", True)


def fold(text: str) -> str:
    """minuscules + sans accents, pour comparer simplement."""
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text.lower()


def _is_wordy(mot: str) -> bool:
    """Vrai si le mot ne contient que des lettres/chiffres (pour le test de mot entier)."""
    return bool(re.fullmatch(r"[0-9a-zA-Zàâäéèêëîïôöùûüç ]+", mot))


def match_categories(text: str) -> list:
    """Renvoie la liste des labels de catégories détectées dans le texte."""
    folded = fold(text)
    hits = []
    for cat in KEYWORDS.values():
        label = cat.get("label", "?")
        for mot in cat.get("mots", []):
            m = fold(mot)
            if _is_wordy(m):
                # mot entier : évite que "or" matche "for", "eth" matche "ethic"...
                if re.search(rf"(?<![0-9a-z]){re.escape(m)}(?![0-9a-z])", folded):
                    hits.append(label)
                    break
            else:
                # symboles ($, €, s&p...) : simple présence
                if m in folded:
                    hits.append(label)
                    break
    return hits


# anti-doublon : on retient les derniers messages relayés
_seen = deque(maxlen=500)

# La connexion est créée au démarrage (lifespan), pas à l'import.
client: TelegramClient = None


async def handle_message(event):
    text = event.raw_text or ""
    if not text.strip():
        return
    cats = match_categories(text)
    if not cats:
        return

    chat = await event.get_chat()
    uname = getattr(chat, "username", None)
    title = getattr(chat, "title", uname or "canal")

    key = (uname, event.id)
    if ANTI_DOUBLON and key in _seen:
        return
    _seen.append(key)

    # lien vers le message original (si canal public)
    lien = f"https://t.me/{uname}/{event.id}" if uname else ""

    cats_uniques = list(dict.fromkeys(cats))  # garde l'ordre, retire doublons
    extrait = text if len(text) <= 1200 else text[:1200] + "…"

    msg = (
        f"🔔 VEILLE — {title}\n"
        f"{' · '.join(cats_uniques)}\n\n"
        f"{extrait}"
    )
    if lien:
        msg += f"\n\n🔗 {lien}"

    await send_telegram(msg)
    log.info("Relayé depuis %s (%s)", title, ", ".join(cats_uniques))


async def send_telegram(text: str) -> None:
    """Envoie un message dans le canal via l'API du bot Telegram."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True,
    }
    try:
        async with httpx.AsyncClient(timeout=15) as http:
            r = await http.post(url, json=payload)
            if r.status_code != 200:
                log.error("Telegram a refusé l'envoi : %s %s", r.status_code, r.text)
    except Exception as e:  # noqa: BLE001
        log.error("Échec d'envoi Telegram : %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global client
    if not (API_ID and API_HASH and SESSION and BOT_TOKEN and CHAT_ID):
        log.warning(
            "Variables manquantes (TELETHON_API_ID/HASH/SESSION, "
            "TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID) — le bot démarre mais ne se "
            "connecte pas."
        )
        yield
        return

    client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
    client.add_event_handler(
        handle_message, events.NewMessage(chats=SOURCES)
    )
    await client.start()
    # IMPORTANT : Telegram ne pousse les nouveaux messages en temps réel que
    # pour les canaux REJOINTS. On s'abonne donc à chaque source au démarrage.
    for src in SOURCES:
        try:
            await client(JoinChannelRequest(src))
            log.info("Abonné au canal @%s", src)
        except Exception as e:  # noqa: BLE001
            log.warning("Impossible de rejoindre @%s : %s", src, e)
    me = await client.get_me()
    log.info(
        "Connecté en tant que %s — surveille : %s -> %s",
        me.first_name, ", ".join(SOURCES), CHAT_ID,
    )
    yield
    await client.disconnect()


app = FastAPI(title="AXONE Veille", lifespan=lifespan)


@app.get("/health")
async def health():
    connecte = bool(client and client.is_connected())
    return {"ok": True, "telegram_connecte": connecte, "sources": SOURCES}


@app.get("/")
async def root():
    return {"service": "axone-veille", "sources": SOURCES, "dest": CHAT_ID}
