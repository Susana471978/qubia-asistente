from datetime import datetime, timezone


def _hoy() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


async def contar_hoy(db, tenant_id) -> int:
    doc = await db.usage_daily.find_one(
        {"tenant_id": tenant_id, "fecha": _hoy()}, {"mensajes": 1}
    )
    return doc.get("mensajes", 0) if doc else 0


async def incrementar(db, tenant_id, nivel: int) -> None:
    await db.usage_daily.update_one(
        {"tenant_id": tenant_id, "fecha": _hoy()},
        {
            "$inc": {"mensajes": 1, f"nivel_{nivel}": 1},
            "$set": {"updated_at": datetime.now(timezone.utc)},
        },
        upsert=True,
    )


async def dentro_de_cuota(db, tenant_id, limite_dia: int) -> bool:
    if limite_dia <= 0:
        return True
    return await contar_hoy(db, tenant_id) < limite_dia
