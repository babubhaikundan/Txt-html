"""
db.py — Async MongoDB helper using Motor.
All functions silently no-op if MONGO_URI is not configured.
"""

from motor.motor_asyncio import AsyncIOMotorClient
import datetime

_client = None
_db     = None


def init_db(mongo_uri: str) -> None:
    """Call once at startup (synchronous — Motor client creation is sync)."""
    global _client, _db
    if not mongo_uri:
        print("[DB] MONGO_URI not set — running without database.")
        return
    _client = AsyncIOMotorClient(mongo_uri, serverSelectionTimeoutMS=5000)
    _db     = _client["txthtml_bot"]
    print("[DB] MongoDB connected.")


def _col(name: str):
    """Return a collection handle, or None if DB not initialised."""
    return _db[name] if _db is not None else None


# ── Users ──────────────────────────────────────────────────────────────────

async def upsert_user(user_id: int, username: str = None, full_name: str = None) -> None:
    col = _col("users")
    if col is None:
        return
    now = datetime.datetime.utcnow()
    await col.update_one(
        {"_id": user_id},
        {
            "$set":         {"username": username, "full_name": full_name, "last_seen": now},
            "$setOnInsert": {"joined_at": now},
        },
        upsert=True,
    )


async def count_users() -> int:
    col = _col("users")
    return await col.count_documents({}) if col is not None else 0


async def get_all_user_ids() -> list:
    col = _col("users")
    if col is None:
        return []
    cursor = col.find({}, {"_id": 1})
    docs   = await cursor.to_list(length=None)
    return [d["_id"] for d in docs]


# ── Conversions ────────────────────────────────────────────────────────────

async def log_conversion(user_id: int, file_name: str, lecture_count: int = 0) -> None:
    col = _col("conversions")
    if col is None:
        return
    await col.insert_one({
        "user_id":       user_id,
        "file_name":     file_name,
        "lecture_count": lecture_count,
        "at":            datetime.datetime.utcnow(),
    })


async def count_conversions_total() -> int:
    col = _col("conversions")
    return await col.count_documents({}) if col is not None else 0


async def count_conversions_today() -> int:
    col = _col("conversions")
    if col is None:
        return 0
    today = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return await col.count_documents({"at": {"$gte": today}})


async def get_user_history(user_id: int, limit: int = 7) -> list:
    col = _col("conversions")
    if col is None:
        return []
    cursor = col.find({"user_id": user_id}, sort=[("at", -1)], limit=limit)
    return await cursor.to_list(length=limit)
