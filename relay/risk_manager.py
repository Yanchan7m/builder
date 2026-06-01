"""Risk Manager prop firm — couche advisory pour le signal-only.

Pour chaque signal, on évalue l'impact d'une perte (-1R) sur l'état du compte
et on renvoie un verdict : OK / WARN / BLOCK + des annotations à afficher.

NB : en signal-only le relais ne voit pas les fills automatiquement. Tu mets à
jour l'état (solde, profit du jour) via l'endpoint /state ou les commandes
Telegram. Le risk manager raisonne donc sur l'état que TU lui donnes.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from models import AccountState, Signal


OK, WARN, BLOCK = "OK", "WARN", "BLOCK"


@dataclass
class Verdict:
    account: str
    level: str = OK
    notes: list[str] = field(default_factory=list)

    def add(self, level: str, note: str) -> None:
        self.notes.append(note)
        # on garde le niveau le plus sévère
        order = {OK: 0, WARN: 1, BLOCK: 2}
        if order[level] > order[self.level]:
            self.level = level


def _risk_dollars(acc: AccountState, sig: Signal) -> float:
    """Perte en $ si le SL est touché, pour la taille demandée par le signal."""
    base = acc.balance * acc.risk_pct_normal / 100.0
    return base * (0.5 if sig.size == "half" else 1.0)


def evaluate(acc: AccountState, sig: Signal) -> Verdict:
    v = Verdict(account=acc.name)
    if not acc.enabled:
        v.add(BLOCK, "compte désactivé")
        return v

    risk = _risk_dollars(acc, sig)

    # --- Drawdown EOD (commun Apex / Lucid) ---------------------------------
    dd = acc.dd_distance
    if dd <= 0:
        v.add(BLOCK, f"seuil EOD déjà atteint (marge {dd:+.0f}$)")
    elif risk >= dd:
        v.add(BLOCK, f"une perte (-{risk:.0f}$) franchirait le seuil EOD (marge {dd:.0f}$)")
    elif risk >= 0.6 * dd:
        v.add(WARN, f"perte -{risk:.0f}$ consommerait >60% de la marge EOD ({dd:.0f}$)")
    else:
        v.add(OK, f"marge EOD {dd:.0f}$ (risque -{risk:.0f}$)")

    # --- Daily loss limit (Apex) -------------------------------------------
    if acc.daily_loss_limit is not None:
        used = max(0.0, -acc.day_pnl)              # perte déjà encaissée aujourd'hui
        remaining = acc.daily_loss_limit - used
        if risk >= remaining:
            v.add(BLOCK, f"daily loss : -{risk:.0f}$ dépasserait la limite (reste {remaining:.0f}$)")
        elif risk >= 0.6 * remaining:
            v.add(WARN, f"daily loss : reste {remaining:.0f}$ avant la limite")

    # --- Règle de consistance (Lucid 50%) ----------------------------------
    if acc.consistency_pct is not None:
        # aucun jour ne doit dépasser consistency_pct du profit total visé
        cap = acc.consistency_pct * acc.profit_target
        if acc.day_pnl >= cap:
            v.add(BLOCK, f"consistance : profit du jour {acc.day_pnl:.0f}$ ≥ plafond {cap:.0f}$ — STOP pour aujourd'hui")
        elif acc.day_pnl >= 0.8 * cap:
            v.add(WARN, f"consistance : profit du jour {acc.day_pnl:.0f}$ proche du plafond {cap:.0f}$")

    return v
