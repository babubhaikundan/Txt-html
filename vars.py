import os
from dotenv import load_dotenv

load_dotenv()

from os import environ

API_ID    = int(environ.get("API_ID", "0"))
API_HASH  = environ.get("API_HASH", "")
BOT_TOKEN = environ.get("BOT_TOKEN", "")
CREDIT    = environ.get("CREDIT", "𝕂𝕦𝕟𝕕𝕒𝕟 𝕐𝕒𝕕𝕒𝕧😎")
MONGO_URI = environ.get("MONGO_URI", "")

# Public channel username WITHOUT @ (e.g. "BabuBhaiKundan")
FORCE_SUB_CHANNEL = environ.get("FORCE_SUB_CHANNEL", "BabuBhaiKundan")

# Log channel — channel ID (e.g. "-1001234567890") ya username (e.g. "MyLogChannel")
# Bot ko us channel ka admin hona chahiye
_log_raw = environ.get("LOG_CHANNEL", "-1004489412273").strip()
if _log_raw.lstrip("-").isdigit():
    LOG_CHANNEL = int(_log_raw)
else:
    LOG_CHANNEL = _log_raw or None   # None means logging disabled
 


# Space-separated admin Telegram user IDs  e.g. "123456789 987654321"
ADMINS = [int(x) for x in environ.get("ADMINS", "5096393058").split() if x.strip().isdigit()]


# ========================================
# Proxy Configuration
# ========================================


def _is_true(value):
    if value is None:
        return False

    return str(value).strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
        "enable",
        "enabled"
    )


USE_PROXY = _is_true(os.getenv("USE_PROXY"))

PYROGRAM_PROXY = None

if USE_PROXY:

    scheme = os.getenv("PROXY_SCHEME", "socks5").strip() or "socks5"

    host = os.getenv("PROXY_HOST", "127.0.0.1").strip() or "127.0.0.1"

    try:
        port = int(os.getenv("PROXY_PORT", "9050"))
    except (ValueError, TypeError):
        port = 9050

    PYROGRAM_PROXY = {
        "scheme": scheme,
        "hostname": host,
        "port": port
    }

# ========================================