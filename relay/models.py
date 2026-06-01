"""Modèles de données : signal entrant (webhook TradingView) + état de compte."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class Signal(BaseModel):
    """Payload JSON envoyé par l'alerte Pine via le webhook TradingView."""
    secret: str
    strat: str               # "S1" liquidité | "S2" pivot | "EW" Elliott
    sym: str                 # ex. "NQ1!", "ES1!", "EURUSD"
    side: str                # "long" | "short"
    entry: float
    sl: float
    tp: float
    score: int               # points de confluence (ou R:R arrondi pour EW)
    size: str                # "normal" | "half"
    market: str = "futures"  # "futures" (prop firm) | "forex" (CFD)
    phase: str = "entry"     # "entry" | "breakeven" | "tp" | "sl"

    @property
    def risk_points(self) -> float:
        """Distance entrée→SL en points de prix."""
        return abs(self.entry - self.sl)

    @property
    def reward_points(self) -> float:
        return abs(self.tp - self.entry)

    @property
    def rr(self) -> float:
        r = self.risk_points
        return round(self.reward_points / r, 2) if r else 0.0


class AccountState(BaseModel):
    """État d'un compte prop firm, mis à jour par toi (semi-manuel)."""
    name: str
    firm: str                       # "apex" | "lucid"
    balance: float                  # solde courant
    eod_threshold: float            # seuil de drawdown EOD courant (figé du jour)
    day_start_balance: float        # solde au début de la journée
    profit_target: float = 3000.0
    daily_loss_limit: Optional[float] = None    # Apex 50k ~1000 ; Lucid None
    consistency_pct: Optional[float] = None     # Lucid 0.50 ; Apex None
    eval_profit: float = 0.0        # profit total cumulé sur l'éval (pour consistance)
    risk_pct_normal: float = 1.0    # risque % pour une taille normale
    enabled: bool = True

    @property
    def day_pnl(self) -> float:
        return round(self.balance - self.day_start_balance, 2)

    @property
    def dd_distance(self) -> float:
        """Marge avant de toucher le seuil de drawdown EOD."""
        return round(self.balance - self.eod_threshold, 2)
