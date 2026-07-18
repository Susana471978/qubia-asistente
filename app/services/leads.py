from datetime import datetime, timezone

from app.models.lead import LeadRequest
from app.services import notificaciones


def validar(tenant: dict, lead: LeadRequest) -> list[str]:
    """Devuelve lista de campos obligatorios que faltan."""
    cfg = tenant.get("leads", {})
    obligatorios = cfg.get("campos_obligatorios", [])
    datos = lead.model_dump()
    return [c for c in obligatorios if not str(datos.get(c, "")).strip()]


async def registrar(db, tenant: dict, lead: LeadRequest) -> dict:
    ahora = datetime.now(timezone.utc)
    doc = {
        "tenant_id": tenant["_id"],
        "session_id": lead.session_id,
        "nombre": lead.nombre.strip(),
        "telefono": lead.telefono.strip(),
        "email": lead.email.strip(),
        "motivo": lead.motivo.strip(),
        "extra": lead.extra,
        "created_at": ahora,
        "entregado": False,
    }
    res = await db.leads.insert_one(doc)

    entregado = await notificaciones.notificar_lead(
        tenant,
        {
            "nombre": doc["nombre"],
            "telefono": doc["telefono"],
            "email": doc["email"],
            "motivo": doc["motivo"],
            "recibido": ahora.strftime("%d/%m/%Y %H:%M UTC"),
        },
    )

    if entregado:
        await db.leads.update_one(
            {"_id": res.inserted_id, "tenant_id": tenant["_id"]},
            {"$set": {"entregado": True}},
        )

    doc["_id"] = str(res.inserted_id)
    doc["entregado"] = entregado
    return doc
