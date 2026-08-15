from fastapi import APIRouter, Depends, Request, Response

from app.cascade import engine
from app.core import errors
from app.core.rate_limit import limiter
from app.db import get_db
from app.deps import get_tenant
from app.models.chat import ChatRequest, ChatResponse, ChatResponseV2
from app.services import conversaciones, usage

router = APIRouter(prefix="/v1", tags=["chat"])


@router.post("/chat", response_model=ChatResponseV2)
@limiter.limit("20/minute")
async def chat(
    request: Request,
    response: Response,
    payload: ChatRequest,
    tenant: dict = Depends(get_tenant),
) -> ChatResponseV2:
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

    # Contrato Core 2.0: sobre enriquecido (ui/actions/lead).
    # En Sprint 1 ui=None y actions=[] (el motor de acciones llega en Sprint 2).
    # Se mantienen alias viejos para compatibilidad con el widget actual.
    return ChatResponseV2(
        message=respuesta,
        session_id=payload.session_id,
        level=nivel,
        ui=None,
        actions=[],
        lead={"suggest": sugerir_lead},
        respuesta=respuesta,
        nivel=nivel,
        sugerir_lead=sugerir_lead,
    )


@router.get("/config")
@limiter.limit("30/minute")
async def config_publica(
    request: Request, response: Response, tenant: dict = Depends(get_tenant)
) -> dict:
    """El widget lee esto al arrancar: contrato Core 2.0, nada sensible."""
    identidad = tenant.get("identidad", {})
    branding = tenant.get("branding", {})
    features = tenant.get("features", {})
    leads = tenant.get("leads", {})

    return {
        "assistant": {
            "name": identidad.get("nombre_asistente", "Asistente"),
            "greeting": identidad.get("saludo_inicial", ""),
        },
        "branding": {
            "business_name": branding.get("business_name", tenant.get("nombre", "")),
            "logo": branding.get("logo_url", ""),
            "primary": branding.get("primary_color", "#0B1220"),
            "secondary": branding.get("secondary_color", "#0D2B45"),
            "accent": branding.get("accent_color", "#00D4C7"),
            "silver": branding.get("silver_color", "#D7E2EB"),
            "champagne": branding.get("champagne_color", "#C8A86B"),
            "assistant_icon": branding.get("assistant_icon", ""),
            "widget_position": branding.get("widget_position", "bottom-right"),
            "widget_theme": branding.get("widget_theme", "dark"),
        },
        "vertical": tenant.get("vertical", "general"),
        "features": {
            "leads": features.get("lead_enabled", leads.get("activo", True)),
            "booking": features.get("booking_enabled", False),
            "properties": features.get("properties_enabled", False),
        },
        "quick_actions": tenant.get("quick_actions", []),
        # --- alias de compatibilidad (widget viejo) ---
        "nombre_asistente": identidad.get("nombre_asistente", "Asistente"),
        "saludo_inicial": identidad.get("saludo_inicial", ""),
        "idioma_principal": identidad.get("idioma_principal", "es"),
        "leads_activo": leads.get("activo", False),
        "campos_lead": leads.get("campos", []),
        "campos_obligatorios": leads.get("campos_obligatorios", []),
    }
