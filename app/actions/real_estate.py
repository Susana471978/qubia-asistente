"""Acciones del vertical Real Estate (primer vertical funcional)."""
from app.actions.base import ActionDef

SEARCH_PROPERTIES = ActionDef("SEARCH_PROPERTIES", "Buscar propiedad", "real_estate")
SHOW_PROPERTY = ActionDef("SHOW_PROPERTY", "Ver propiedad", "real_estate")
COMPARE_PROPERTIES = ActionDef("COMPARE_PROPERTIES", "Comparar", "real_estate")
REQUEST_VISIT = ActionDef("REQUEST_VISIT", "Solicitar visita", "real_estate")
REQUEST_INFO = ActionDef("REQUEST_INFO", "Pedir informacion", "real_estate")
CONTACT_AGENT = ActionDef("CONTACT_AGENT", "Contactar con un agente", "real_estate")

ACCIONES = [
    SEARCH_PROPERTIES,
    SHOW_PROPERTY,
    COMPARE_PROPERTIES,
    REQUEST_VISIT,
    REQUEST_INFO,
    CONTACT_AGENT,
]
