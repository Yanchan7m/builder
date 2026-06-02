# AXONE Veille 🔔

Bot Telegram qui surveille des canaux publics (BRICS News, Watcher Guru…) et
relaie **dans ton canal** uniquement les news qui parlent de **$ / € / indices /
or / IPO / crypto**.

## Comment ça marche

Il se connecte à Telegram avec **ton compte** (session « utilisateur » Telethon),
écoute les canaux listés dans `config.yaml`, filtre par mots-clés, et renvoie les
messages pertinents dans ton canal — avec un lien vers le message original.

## Mise en route (une seule fois)

### 1. Obtenir tes clés Telegram
- Va sur https://my.telegram.org → **API development tools**
- Crée une application (n'importe quel nom) → note `API_ID` et `API_HASH`

### 2. Créer ton canal de réception
- Dans Telegram, crée un canal (ex. « AXONE Veille »)
- Assure-toi que ton compte peut y écrire (tu en es le créateur/admin)
- Note son @nom (ex. `@axone_veille`)

### 3. Générer ta clé de session (en local)
```bash
cd veille
./.venv/bin/python login.py
```
Entre `API_ID`, `API_HASH`, ton numéro, puis le code reçu sur Telegram.
Copie la **longue chaîne** affichée à la fin.

### 4. Déployer sur Render
Sur le service `axone-veille`, remplis les 4 variables :
| Variable | Valeur |
|---|---|
| `TELETHON_API_ID` | ton API_ID |
| `TELETHON_API_HASH` | ton API_HASH |
| `TELETHON_SESSION` | la longue chaîne de l'étape 3 |
| `TELEGRAM_BOT_TOKEN` | le token de ton bot (BotFather) |
| `TELEGRAM_CHAT_ID` | `@ton_canal` (le bot doit y être admin) |

## Régler les canaux et mots-clés
Tout se modifie dans **`config.yaml`** (canaux à suivre, mots-clés par catégorie).
Pas besoin de toucher au code.

## Rafraîchir la watchlist boursière (pour plus tard, Étape SEC)
```bash
./.venv/bin/python build_watchlist.py
```
Régénère `watchlist.yaml` (NASDAQ-100 + S&P 500 avec leur CIK SEC).
