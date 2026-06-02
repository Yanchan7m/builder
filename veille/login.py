"""
À LANCER UNE SEULE FOIS, sur ton ordinateur, pour connecter ton compte Telegram.

Ça crée une « clé de session » (une longue chaîne de caractères) que tu colleras
ensuite sur Render. Comme ça le bot tourne tout seul sans jamais redemander ton
code de connexion.

Avant de lancer :
  1. Va sur https://my.telegram.org  ->  "API development tools"
  2. Crée une application (n'importe quel nom) -> tu obtiens API_ID et API_HASH
  3. Lance :  python3 login.py
  4. Entre ton numéro de téléphone, puis le code reçu sur Telegram
  5. Copie la longue chaîne affichée à la fin -> ce sera TELETHON_SESSION
"""
from telethon import TelegramClient
from telethon.sessions import StringSession

print("== Connexion du compte Telegram pour le bot de veille ==\n")
api_id = int(input("API_ID    : ").strip())
api_hash = input("API_HASH  : ").strip()

with TelegramClient(StringSession(), api_id, api_hash) as client:
    me = client.get_me()
    session_str = client.session.save()
    print("\n✅ Connecté en tant que :", me.first_name, f"(@{me.username})" if me.username else "")
    print("\n================ TA CLÉ DE SESSION (copie tout) ================\n")
    print(session_str)
    print("\n===============================================================")
    print("\nColle cette valeur dans Render -> variable TELETHON_SESSION.")
    print("⚠️  Garde-la secrète : elle donne accès à ton compte Telegram.")
