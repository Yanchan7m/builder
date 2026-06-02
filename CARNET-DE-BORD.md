# 🗂️ Carnet de bord — AXONE Capital

> Récapitulatif des projets, en clair. **Aucun secret ici** (tokens, mots de passe,
> clés) : ils restent dans les variables Render et le fichier `.env` (non partagé).
> Document sûr à partager / sauvegarder.
> Dernière mise à jour : 02/06/2026.

---

## Vue d'ensemble

Deux bots Telegram tournent en continu sur **Render** (offre gratuite), dépôt GitHub
`Yanchan7m/builder` :

| Bot | Rôle | Adresse |
|---|---|---|
| **AXONE Signal Bot** | Signaux de trading (S1/S2/Elliott) | `axone-capital-bot-26gc.onrender.com` |
| **AXONE Veille** | Surveillance news ($/€/NASDAQ/or/IPO/crypto) | `axone-veille-news.onrender.com` |

---

# 1) 🤖 AXONE Signal Bot (trading)

**But** : recevoir sur Telegram des signaux d'entrée prêts à trader, sur les indices
US futures (NQ / ES / YM) et le Forex, avec gestion des règles prop firm.

## Comment ça circule
```
TradingView (script Pine)  →  webhook  →  relais FastAPI (Render)  →  Telegram
                                              ↓
                                   Dashboard (journal des signaux, Postgres)
```

## Les stratégies

### Cadre général
- Instruments : Nasdaq (NQ), S&P 500 (ES), Dow Jones (YM).
- Exécution **M5** avec confluence **M15** (englobante + divergence sur les deux).
- Tendance **H1** via **MA20 vs MA50** : MA20 > MA50 = haussier (achats) ;
  MA20 < MA50 = baissier (ventes).
- Session US uniquement, jamais sur les 5 premières minutes de l'open.
- ~1 trade/jour en moyenne (parfois 0, parfois 2).
- ⏰ **Fenêtre d'entrée : 09:35–14:00 New York = 15:35–20:00 Paris.** Hors de ce
  créneau, aucun signal (c'est normal).

### S1 — Prise de liquidité (range Asie / Londres)
- On trace haut/bas des ranges Asie et Londres (4 niveaux).
- Sweep d'un niveau = prise de liquidité (sweep haut → vente ; sweep bas → achat).
- Réintégration **rapide** (≤ 3 bougies), entrée à la clôture de la bougie de réintégration.
- Une liquidité ne se prend **qu'une fois**.
- SL : juste au-delà de l'extrême du sweep.

### S2 — Réaction sur niveau institutionnel
- On trace pivots journaliers + open daily (niveaux que tout le monde voit).
- Le prix touche un pivot/open → réaction confirmée par englobante/marteau + divergence RSI.
- SL : de l'autre côté du pivot.

### S3 — Elliott Level Watcher (Forex CFD)
- Flux séparé des futures, sans les règles prop firm.
- **Toi** tu fais le comptage des vagues (1-2-3-4-5, ABC/WXY, diagonale, triangle).
- Tu donnes 3 niveaux : Confirmation (entrée) / Invalidation (SL) / Cible (TP).
- Le bot surveille et alerte : franchissement de la confirmation = ENTRÉE, puis
  gère breakeven (à 1R), TP atteint, ou invalidation.

### Scoring → taille de position
La tendance H1 est une **confirmation** (pas un veto) :
| Confluence | Points |
|---|---|
| Setup dans le sens de la tendance | +2 |
| Englobante ou marteau (toujours requis) | +1 |
| Divergence RSI | +1 |
| Protégé par le pivot | +1 |

- Score ≥ 3 → taille **normale** ; score = 2 → **demi-taille**.
- Contre-tendance autorisé **uniquement** avec divergence RSI (→ demi-taille).

### Take-profit (commun S1/S2)
- Viser le 1er niveau institutionnel donnant un ratio ≥ 2 ; sinon le pivot suivant.

### Règles prop firm 50k (Risk Manager)
| Paramètre | Apex 50k (EOD) | LucidFlex 50k |
|---|---|---|
| Profit target | 3 000 $ | 3 000 $ |
| Drawdown | EOD trailing ~2 500 $ | EOD trailing 2 000 $ |
| Daily loss limit | 1 000 $ (à confirmer) | aucune |
| Consistance | aucune | 50 % (jour < 1 500 $) |
| Jours min | 0 | 2 |

Le bot **bloque** un signal si la perte approcherait un seuil, ou si le profit du
jour (Lucid) approche le plafond de consistance.

## Côté technique
- Code : dossier `relay/` (FastAPI), scripts Pine dans `pine/`.
- Dashboard journal des signaux (Postgres) avec résultat/note par signal.
- PDF récap des stratégies : `relay/make_pdf.py` → `~/Downloads/AXONE_Strategies_Signaux.pdf`.
- Secrets (token, chat id, webhook secret) : **variables Render** du service.

## ⚠️ Limite connue
Render gratuit **endort** le service après 15 min d'inactivité. Le keep-alive
GitHub Actions est censé le réveiller toutes les 10 min, mais GitHub **bride les
tâches planifiées** (elles tournent en pratique toutes les quelques heures). Donc
le bot peut dormir et **rater un signal** pendant la session. Solutions possibles :
pinger externe fiable (cron-job.org / UptimeRobot), ou Render payant (~7 $/mois).

---

# 2) 🔔 AXONE Veille (news)

**But** : recevoir en message privé Telegram les news qui font bouger le **$, €,
NASDAQ, or, IPO et crypto**, en surveillant des canaux publics.

## Comment ça marche
- Se connecte avec **ton compte** Telegram (session « utilisateur » Telethon).
- **Rejoint** et écoute les canaux sources (obligatoire : Telegram ne pousse les
  messages en temps réel que pour les canaux rejoints).
- Filtre chaque message par mots-clés (devises / indices / or / IPO / crypto).
- Relaie les messages pertinents dans ta conversation privée avec le bot, avec un
  lien vers l'original.

## Canaux surveillés
- @bricsnews
- @WatcherGuru
- *(3e canal à confirmer — @Infositons ?)*

## Réglages
- Canaux + mots-clés : dans `veille/config.yaml` (modifiable sans toucher au code).
- **Watchlist boursière** : `veille/watchlist.yaml` = NASDAQ-100 + S&P 500
  (516 sociétés + leur CIK SEC), générée par `veille/build_watchlist.py`. Prête
  pour l'étape SEC à venir.

## Côté technique
- Code : dossier `veille/` (FastAPI + Telethon).
- Envoi via le bot **@axonecapitalnewsbot** (API Bot Telegram).
- Secrets (API_ID/HASH Telethon, clé de session, token bot, chat id) :
  **variables Render** + fichier local `veille/.env` (non commité).
- Pour reconnecter le compte un jour : `veille/login.py`.

## Prochaines étapes prévues
1. **Étape SEC** : alertes dépôts 8-K sur les 516 sociétés de la watchlist
   (résultats, rachats, IPO, démissions… le « il s'est passé un truc » officiel).
2. **Flux RSS presse** filtré sur la watchlist.
3. **Calendrier banques centrales** (BCE / Fed).
4. Ajouter le 3e canal une fois l'orthographe confirmée.

---

# ✅ À faire / points ouverts
- [ ] **Révoquer la clé API Render** (`rnd_…`) utilisée pour le déploiement — Render
      → Account Settings → API Keys. (Le bot continue sans elle.)
- [ ] Décider de la fiabilité anti-sommeil (pinger externe ou Render payant).
- [ ] Confirmer le 3e canal de veille.
- [ ] (Optionnel) Régénérer le token du bot s'il a été partagé en clair.

---

# 🔐 Où sont les secrets (rappel)
Jamais dans ce fichier. Ils vivent :
- dans les **variables d'environnement Render** de chaque service ;
- dans les fichiers **`.env`** locaux (ignorés par git, non partagés).
