from datetime import datetime, timezone


async def obtener_historial(db, tenant_id, session_id, max_turnos) -> list[dict]:
    doc = await db.conversaciones.find_one(
        {"tenant_id": tenant_id, "session_id": session_id}, {"turnos": 1}
    )
    if not doc:
        return []
    turnos = doc.get("turnos", [])
    return turnos[-(max_turnos * 2):] if max_turnos > 0 else []


async def guardar_turno(db, tenant_id, session_id, mensaje, respuesta, max_turnos) -> None:
    ahora = datetime.now(timezone.utc)
    nuevos = [
        {"role": "user", "content": mensaje},
        {"role": "assistant", "content": respuesta},
    ]
    await db.conversaciones.update_one(
        {"tenant_id": tenant_id, "session_id": session_id},
        {
            "$push": {"turnos": {"$each": nuevos, "$slice": -(max_turnos * 2)}},
            "$set": {"updated_at": ahora},
            "$setOnInsert": {"created_at": ahora},
        },
        upsert=True,
    )
