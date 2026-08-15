"""Acciones del vertical Guest (declaradas, sin implementar en Sprint 1)."""
from app.actions.base import ActionDef

CHECKIN_INFO = ActionDef("CHECKIN_INFO", "Informacion de check-in", "guest")
SHOW_PARKING = ActionDef("SHOW_PARKING", "Parking", "guest")
LOCAL_RECOMMENDATIONS = ActionDef("LOCAL_RECOMMENDATIONS", "Recomendaciones", "guest")
REPORT_ISSUE = ActionDef("REPORT_ISSUE", "Tengo una incidencia", "guest")
CONTACT_HOST = ActionDef("CONTACT_HOST", "Contactar con el anfitrion", "guest")

ACCIONES = [
    CHECKIN_INFO,
    SHOW_PARKING,
    LOCAL_RECOMMENDATIONS,
    REPORT_ISSUE,
    CONTACT_HOST,
]
