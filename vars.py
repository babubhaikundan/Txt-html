import os
from os import environ

API_ID    = int(environ.get("API_ID", "0"))
API_HASH  = environ.get("API_HASH", "")
BOT_TOKEN = environ.get("BOT_TOKEN", "")
CREDIT    = environ.get("CREDIT", "𝕂𝕦𝕟𝕕𝕒𝕟 𝕐𝕒𝕕𝕒𝕧😎")
MONGO_URI = environ.get("MONGO_URI", "")

# Public channel username WITHOUT @ (e.g. "BabuBhaiKundan")
FORCE_SUB_CHANNEL = environ.get("FORCE_SUB_CHANNEL", "BabuBhaiKundan")

# Space-separated admin Telegram user IDs  e.g. "123456789 987654321"
ADMINS = [int(x) for x in environ.get("ADMINS", "5096393058").split() if x.strip().isdigit()]
