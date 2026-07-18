from fastapi import APIRouter, Depends, Request, Response

from app.cascade import engine
from app.core import errors
from app.core.rate_limit import limiter
from app.db import get_db
from app.deps import get_tenant
from app.models.chat import ChatRequest, ChatResponse
from app.services import conversaciones, usage

router = APIRouter(prefix="/v1", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("20/minute")
async def chat(
    request: Request,
    response: Response,
    payload: ChatRequest,
    tenant: dict = Depends(get_tenant),
) -> ChatResponse:
    db = get_db()
    tenant_id = tenant["_id"]
    limites = tenant.get("limites", {})

    if not await usage.dentro_de_cuota(db, tenant_id, limites.get("mensajes_dia", 500)):
        raise errors.cuota_superada()

    max_turnos = limites.get("max_turnos_memoria", 6)
    historial = await conversaciones.obtener_historial(
        db, tenant_id, payload.session_id, max_turnos
    )

    respuesta, nivel, sugerir_lead = await engine.procesar(
        db, tenant, payload.mensaje, historial
    )

    await conversaciones.guardar_turno(
        db, tenant_id, payload.session_id, payload.mensaje, respuesta, max_turnos
    )
    await usage.incrementar(db, tenant_id, nivel)

    return ChatResponse(
        respuesta=respuesta,
        nivel=nivel,
        session_id=payload.session_id,
        sugerir_lead=sugerir_lead,
    )


@router.get("/config")
@limiter.limit("30/minute")
async def config_publica(
    request: Request, response: Response, tenant: dict = Depends(get_tenant)
) -> dict:
    """El widget lee esto al arrancar: identidad visible, nada sensible."""
    identidad = tenant.get("identidad", {})
    return {
        "nombre_asistente": identidad.get("nombre_asistente", "Asistente"),
        "saludo_inicial": identidad.get("saludo_inicial", ""),
        "idioma_principal": identidad.get("idioma_principal", "es"),
        "leads_activo": tenant.get("leads", {}).get("activo", False),
        "campos_lead": tenant.get("leads", {}).get("campos", []),
        "campos_obligatorios": tenant.get("leads", {}).get("campos_obligatorios", []),
    }
