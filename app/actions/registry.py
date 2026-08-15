"""Registro central de acciones por vertical.

Responde "¿que puede hacer un tenant de este vertical?" sin que el widget ni
el chat lo tengan hardcodeado. Es la unica fuente de verdad del catalogo.

Garantiza el aislamiento por vertical (punto 23 del plan): un tenant
real_estate nunca recibe acciones de hospitality.
"""
from app.actions import guest, hospitality, real_estate
from app.actions.base import ActionDef, Vertical

# vertical -> lista de ActionDef. "general" no expone acciones especificas.
_REGISTRO: dict[str, list[ActionDef]] = {
    "general": [],
    "real_estate": real_estate.ACCIONES,
    "hospitality": hospitality.ACCIONES,
    "guest": guest.ACCIONES,
}


def acciones_de_vertical(vertical: str) -> list[ActionDef]:
    """Devuelve las acciones declaradas para un vertical.

    Si el vertical es desconocido, devuelve lista vacia (nunca lanza), para
    que un tenant mal configurado no rompa el contrato /v1/config.
    """
    return _REGISTRO.get(vertical, [])


def tipos_de_vertical(vertical: str) -> set[str]:
    """Conjunto de 'type' validos para un vertical (util para validaciones)."""
    return {a.type for a in acciones_de_vertical(vertical)}


def es_accion_valida(vertical: str, tipo: str) -> bool:
    """True si 'tipo' pertenece al vertical dado."""
    return tipo in tipos_de_vertical(vertical)


def catalogo_completo() -> dict[str, list[dict]]:
    """Todo el catalogo serializado (debug / documentacion)."""
    return {v: [a.as_dict() for a in accs] for v, accs in _REGISTRO.items()}
