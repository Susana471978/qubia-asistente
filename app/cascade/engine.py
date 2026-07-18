import logging

from app.cascade import guardrails, nivel1_reglas, nivel2_rag, nivel3_llm
from app.cascade.nivel1_reglas import normalizar
from app.cascade.prompt_builder import construir_system_prompt

log = logging.getLogger("qubia.cascade")

# Senales de intencion comercial -> sugerir captura de lead.
# Se usan si el tenant no define las suyas en leads.senales.
_SENALES_LEAD = [
    # peticion de contacto
    "cita", "contactar", "contacto", "llamar", "llamad", "llamen", "llamame",
    "telefono", "whatsapp", "escribidme", "avisadme",
    # intencion economica
    "presupuesto", "precio", "cuesta", "cuanto vale", "tarifa", "coste",
    "financiacion", "hipoteca",
    # intencion de operar
    "contratar", "reservar", "comprar", "vender", "alquilar", "visitar",
    "visita", "tasar", "valorar", "interesa", "interesado", "interesada",
    "me gustaria", "quiero", "necesito", "busco",
    # disponibilidad
    "disponibilidad", "disponible", "libre", "cuando podria",
]

# Senales en la RESPUESTA: el asistente esta pidiendo datos de contacto.
# Si esto aparece, hay lead aunque el mensaje del usuario no lo cantara.
_SENALES_RESPUESTA = [
    "tu numero", "tu telefono", "tus datos", "dejanos tus datos",
    "dejame tu", "podrias dejarnos", "te llamemos", "te llamen",
    "concertar una visita", "concertar una cita", "que te contacten",
    "ponerte en contacto",
]

MENSAJE_ERROR = (
    "Ahora mismo no puedo responder. Intentalo de nuevo en un momento "
    "o dejanos tus datos y te contactamos."
)


def _detectar_intencion_lead(mensaje: str, senales: list[str] | None = None) -> bool:
    texto = normalizar(mensaje)
    lista = senales if senales else _SENALES_LEAD
    return any(normalizar(s) in texto for s in lista)


def _respuesta_pide_datos(respuesta: str) -> bool:
    """True si el propio asistente esta pidiendo datos de contacto."""
    texto = normalizar(respuesta)
    return any(normalizar(s) in texto for s in _SENALES_RESPUESTA)


def _resolver_lead(tenant: dict, mensaje: str, respuesta: str) -> bool:
    """Decide si procede sugerir la captura de lead.

    Respeta leads.trigger: "siempre" siempre sugiere, "manual" nunca,
    "intencion" (por defecto) evalua mensaje y respuesta.
    """
    leads = tenant.get("leads", {})
    if not leads.get("activo", False):
        return False

    trigger = leads.get("trigger", "intencion")
    if trigger == "siempre":
        return True
    if trigger == "manual":
        return False

    senales = leads.get("senales") or None
    return _detectar_intencion_lead(mensaje, senales) or _respuesta_pide_datos(respuesta)


async def procesar(
    db,
    tenant: dict,
    mensaje: str,
    historial: list[dict],
) -> tuple[str, int, bool]:
    """Devuelve (respuesta, nivel_usado, sugerir_lead)."""

    # sugerir_lead se resuelve por respuesta, ya que el propio asistente
    # puede estar pidiendo datos aunque el mensaje no lo indicara.

    # Barrera de entrada: no gastamos tokens en intentos de manipulacion
    if guardrails.entrada_sospechosa(mensaje):
        log.warning("injection_intento tenant=%s", tenant.get("slug"))
        return guardrails.MENSAJE_BLOQUEO, 1, False

    # Nivel 1 - reglas deterministas del tenant
    respuesta = nivel1_reglas.evaluar(mensaje, tenant.get("reglas_nivel1", []))
    if respuesta:
        return respuesta, 1, _resolver_lead(tenant, mensaje, respuesta)

    # Nivel 2 - RAG (placeholder)
    respuesta = await nivel2_rag.consultar(db, tenant, mensaje)
    if respuesta:
        limpia = guardrails.filtrar_salida(respuesta)
        return limpia, 2, _resolver_lead(tenant, mensaje, limpia)

    # Nivel 3 - LLM
    try:
        system_prompt = construir_system_prompt(tenant)
        bruta = await nivel3_llm.completar(
            system_prompt, historial, mensaje, tenant.get("modelo", {})
        )
        if not bruta:
            return MENSAJE_ERROR, 3, _resolver_lead(tenant, mensaje, "")
        limpia = guardrails.filtrar_salida(bruta)
        return limpia, 3, _resolver_lead(tenant, mensaje, limpia)
    except Exception:
        log.exception("nivel3_fallo tenant=%s", tenant.get("slug"))
        return MENSAJE_ERROR, 3, _resolver_lead(tenant, mensaje, "")
