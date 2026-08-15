"""Acciones del vertical Hospitality (declaradas, sin implementar en Sprint 1)."""
from app.actions.base import ActionDef

SHOW_MENU = ActionDef("SHOW_MENU", "Ver menu", "hospitality")
CHECK_RESERVATION = ActionDef("CHECK_RESERVATION", "Consultar reserva", "hospitality")
REQUEST_TABLE = ActionDef("REQUEST_TABLE", "Reservar mesa", "hospitality")
SHOW_EVENTS = ActionDef("SHOW_EVENTS", "Ver eventos", "hospitality")
CONTACT_RESTAURANT = ActionDef("CONTACT_RESTAURANT", "Contactar", "hospitality")

ACCIONES = [
    SHOW_MENU,
    CHECK_RESERVATION,
    REQUEST_TABLE,
    SHOW_EVENTS,
    CONTACT_RESTAURANT,
]
