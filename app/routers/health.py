from fastapi import APIRouter

from app.config import settings
from app.db import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    estado_db = "ok"
    try:
        await get_db().command("ping")
    except Exception:
        estado_db = "error"
    return {"status": "ok", "db": estado_db, "env": settings.app_env}
