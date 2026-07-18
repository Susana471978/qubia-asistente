import logging

from app.cascade import guardrails, nivel1_reglas, nivel2_rag, nivel3_llm
from app.cascade.nivel1_reglas import normalizar
from app.cascade.prompt_builder import construir_system_prompt

log = logging.getLogger("qubia.cascade")

# Senales de intencion comercial -> sugerir captura de lead
_SENALES_LEAD = [
    "cita", "presupuesto", "precio", "contratar", "llamadme", "llamarme",
    "que me llamen", "informacion", "contactar", "reservar", "disponibilidad",
]

MENSAJE_ERROR = (
    "Ahora mismo no puedo responder. Intentalo de nuevo en un momento "
    "o dejanos tus datos y te contactamos."
)


def _detectar_intencion_lead(mensaje: str) -> bool:
    texto = normalizar(mensaje)
    return any(normalizar(s) in texto for s in _SENALES_LEAD)


async def procesar(
    db,
    tenant: dict,
    mensaje: str,
    historial: list[dict],
) -> tuple[str, int, bool]:
    """Devuelve (respuesta, nivel_usado, sugerir_lead)."""

    leads_activos = tenant.get("leads", {}).get("activo", False)
    sugerir_lead = leads_activos and _detectar_intencion_lead(mensaje)

    # Barrera de entrada: no gastamos tokens en intentos de manipulacion
    if guardrails.entrada_sospechosa(mensaje):
        log.warning("injection_intento tenant=%s", tenant.get("slug"))
        return guardrails.MENSAJE_BLOQUEO, 1, False

    # Nivel 1 - reglas deterministas del tenant
    respuesta = nivel1_reglas.evaluar(mensaje, tenant.get("reglas_nivel1", []))
    if respuesta:
        return respuesta, 1, sugerir_lead

    # Nivel 2 - RAG (placeholder)
    respuesta = await nivel2_rag.consultar(db, tenant, mensaje)
    if respuesta:
        return guardrails.filtrar_salida(respuesta), 2, sugerir_lead

    # Nivel 3 - LLM
    try:
        system_prompt = construir_system_prompt(tenant)
        bruta = await nivel3_llm.completar(
            system_prompt, historial, mensaje, tenant.get("modelo", {})
        )
        if not bruta:
            return MENSAJE_ERROR, 3, sugerir_lead
        return guardrails.filtrar_salida(bruta), 3, sugerir_lead
    except Exception:
        log.exception("nivel3_fallo tenant=%s", tenant.get("slug"))
        return MENSAJE_ERROR, 3, sugerir_lead
