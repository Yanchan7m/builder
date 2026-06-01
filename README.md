# Signal Bot — Prop Firm Futures (Apex EOD / LucidFlex)

Bot de signaux pour valider des challenges prop firm sur **futures indices US** (NQ, ES, YM),
basé sur 2 stratégies de price-action et un système de scoring qui pilote la taille de position.

## Architecture — un bot Telegram, deux flux

```
                                        ┌─────────────────────────────┐
  ⚙️ FUTURES (NQ/ES/YM)  ──alerte──►    │                             │
  S1 Liquidité + S2 Pivot              │   Relais Python (/webhook)   │──► 📲 Telegram
                                        │   + Risk Manager (futures)   │     (AXONE bot)
  💱 FOREX (CFD)         ──alerte──►    │                             │
  S3 Elliott Level Watcher             └─────────────────────────────┘
```

- **Flux futures** : signaux S1/S2 → Risk Manager prop firm (drawdown EOD, consistance) → Telegram.
- **Flux forex** : signaux Elliott (entrée → breakeven → TP/SL) → Telegram, **sans** les règles futures.
- Le champ `market` du payload (`futures` / `forex`) route le signal.

## Phasage

- **Phase 1 — Backtest** : stratégies futures en **Pine Script v6**, validées dans le *Strategy Tester*.
- **Phase 2 — Live** : alertes Pine → **webhook** → relais **Python** → **Telegram** (signal-only, semi-manuel).

---

## Règles prop firm (compte 50k) — encodées dans le Risk Manager (phase 2)

| Paramètre            | Apex 50k (EOD)            | LucidFlex 50k              |
|----------------------|---------------------------|----------------------------|
| Profit target        | 3 000 $                   | 3 000 $                    |
| Type de drawdown     | EOD trailing              | EOD trailing               |
| Max loss / drawdown  | ~2 500 $ (trailing)       | 2 000 $                    |
| Ceiling statique     | bloque à +100 $ (50 100 $)| —                          |
| Daily loss limit     | 1 000 $ *(à confirmer)*   | aucun                      |
| Consistance          | aucune                    | **50 %** (aucun jour > 1 500 $) |
| Jours min            | 0                         | 2                          |

Le Risk Manager doit pouvoir **bloquer un signal** si :
- on approche du drawdown EOD / daily loss ;
- (Lucid) le profit du jour approche la limite de consistance.

---

## Stratégie 1 — Prise de liquidité (range Asie / Londres)

- **Instruments** : NQ, ES (indices US) · **Exécution** : M5 · **Tendance** : H1 (MA20 vs MA50)
- On trace **haut/bas du range Asie** et **haut/bas du range Londres** (4 niveaux).
- **Entrée** :
  1. Sweep d'un niveau de range (= prise de liquidité)
  2. Réintégration **rapide** dans le range (**≤ 3 bougies M5**)
  3. Entrée à la **clôture** de la bougie de réintégration (jamais sur les 5 premières min de l'open)
- **Direction** : sweep d'un *haut* → vente ; sweep d'un *bas* → achat.
- **Règle clé** : une liquidité ne se prend **qu'une fois** (même soldée en SL → setup mort).

## Stratégie 2 — Réaction sur niveau institutionnel

- **Instruments** : NQ, ES, **YM** · mêmes timeframes / scoring.
- On trace **points pivots** + **open daily**.
- **Entrée** : le prix **touche** un pivot / open daily (dépassement de quelques ticks OK) puis
  **réagit**, avec englobante/marteau + divergence RSI + SL protégé par le pivot.
- Sur un pivot, une 2e réaction est tolérée (la 1re reste la plus fiable).

## Système de scoring → taille de position (commun aux 2 stratégies)

| Confluence                                              | Points |
|--------------------------------------------------------|--------|
| Setup **dans le sens de la tendance** (continuation)   | +2     |
| **Englobante** ou **marteau**                          | +1     |
| **Divergence RSI**                                     | +1     |

- **≥ 3 pts** → taille **normale** (ex. risque 1 %)
- **2 pts** → **demi-taille** (ex. 0,5 %)
- **Contre-tendance** : autorisé **seulement** si divergence RSI **+** englobante **+** SL protégé par pivot.

### Take-profit (commun)
Premier niveau institutionnel (pivot ou open daily) donnant un **ratio ≥ 2**.
### Stop-loss
Au-delà de l'extrême du sweep (strat 1) / de l'autre côté du pivot (strat 2).

---

## ⚠️ Hypothèses à confirmer (par défaut dans le code, réglables en `input`)

1. ~~**Scoring vendredi ES**~~ ✅ **RÉSOLU** : vendredi était un short **contre-tendance**
   (cible = pivot en dessous, tendance haussière), donc pas de +2 « tendance ».
   Scoring final : continuation +2, englobante/marteau +1, divergence RSI +1, **protégé pivot +1**.
   Score ≥3 → taille normale ; =2 → demi-taille. Englobante toujours requise ; contre-tendance → divergence requise.
2. **Horaires de session** (Asie / Londres / US) en UTC — placeholders à ajuster.
3. **MA** : SMA ou EMA ? (défaut : SMA)
4. **RSI** : période 14, sur M5.
5. **Englobante / marteau / divergence** : définitions par défaut (voir code).
6. **Pivots** : journaliers classiques (PP, R1/R2, S1/S2) ; open daily = open de la session daily.
