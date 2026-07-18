from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING

from app.config import settings

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("DB no inicializada. Llamar a connect() primero.")
    return _db


async def connect() -> None:
    global _client, _db
    _client = AsyncIOMotorClient(settings.mongo_uri, tz_aware=True)
    _db = _client[settings.mongo_db]
    await _ensure_indexes(_db)


async def disconnect() -> None:
    global _client, _db
    if _client is not None:
        _client.close()
    _client, _db = None, None


async def _ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    await db.tenants.create_index([("slug", ASCENDING)], unique=True)
    await db.tenants.create_index([("auth.public_key", ASCENDING)], unique=True)
    await db.tenants.create_index([("auth.key_previous", ASCENDING)], sparse=True)
    await db.tenants.create_index([("status", ASCENDING)])

    await db.conversaciones.create_index(
        [("tenant_id", ASCENDING), ("session_id", ASCENDING)], unique=True
    )
    await db.conversaciones.create_index(
        [("updated_at", ASCENDING)], expireAfterSeconds=90 * 24 * 3600
    )

    await db.leads.create_index([("tenant_id", ASCENDING), ("created_at", DESCENDING)])
    await db.usage_daily.create_index(
        [("tenant_id", ASCENDING), ("fecha", ASCENDING)], unique=True
    )
    await db.admin_users.create_index([("email", ASCENDING)], unique=True)
