# Relais Telegram (signal-only, semi-manuel)

Reçoit les alertes TradingView → applique le Risk Manager prop firm → envoie le signal sur Telegram.
Tu reçois le signal, **tu cliques toi-même** l'ordre sur TradingView/Tradovate.

```
Pine (alerte webhook) ──► /webhook ──► Risk Manager ──► Telegram
```

## 1. Installer

```bash
cd relay
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # puis remplis .env
```

## 2. Créer le bot Telegram

1. Sur Telegram, parle à **@BotFather** → `/newbot` → récupère le **token** → `TELEGRAM_BOT_TOKEN`.
2. Démarre une conversation avec ton bot (envoie-lui « hi »).
3. Récupère ton **chat id** : ouvre
   `https://api.telegram.org/bot<TOKEN>/getUpdates` dans le navigateur, le champ
   `chat.id` → `TELEGRAM_CHAT_ID`. (Pour un canal : ajoute le bot comme admin, l'id commence par `-100…`.)
4. Choisis un `WEBHOOK_SECRET` long/aléatoire, **et reporte-le** dans le script Pine
   (remplace `CHANGE_ME` dans le message d'alerte).

## 3. Lancer

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

Test local (sans TradingView) :
```bash
curl -X POST localhost:8000/webhook -d \
 '{"secret":"mets-ton-secret","strat":"S1","sym":"NQ1!","side":"short","entry":21500,"sl":21530,"tp":21380,"score":3,"size":"normal"}'
```
→ tu dois recevoir le signal sur Telegram.

## 4. Exposer à TradingView

TradingView a besoin d'une **URL publique** (et d'un plan **Pro+** pour les webhooks) :
- Dev : `ngrok http 8000` → utilise l'URL `https://xxxx.ngrok.io/webhook`.
- Prod : déploie sur un petit VPS / Render / Railway.

Dans l'alerte TradingView : condition = « *Any alert() function call* » sur la stratégie,
et colle l'URL dans **Webhook URL**. Le message est déjà généré par le script Pine.

## 5. Mettre à jour l'état des comptes (chaque jour)

Le Risk Manager raisonne sur l'état que tu lui donnes (solde, profit du jour).
Au début de chaque journée, fige le `eod_threshold` et le `day_start_balance` :

```bash
curl -X POST localhost:8000/state -H 'Content-Type: application/json' -d \
 '{"name":"LucidFlex-50k","balance":50450,"day_start_balance":50450,"eod_threshold":48450}'
```

Le message Telegram affiche alors, pour chaque compte, la marge avant le seuil EOD,
le budget daily loss restant (Apex) et le plafond de consistance (Lucid).
