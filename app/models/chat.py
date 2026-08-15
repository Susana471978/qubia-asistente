from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=8, max_length=64)
    mensaje: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    respuesta: str
    nivel: Literal[1, 2, 3]
    session_id: str
    sugerir_lead: bool = False


class UIBlock(BaseModel):
    """Bloque de UI enriquecida que el widget renderiza (no texto plano).

    type: property_cards | property_detail | comparison | quick_actions |
          lead_form | visit_form | success_message | (extensible por vertical)
    """
    type: str
    items: list[dict] = Field(default_factory=list)
    data: dict = Field(default_factory=dict)


class Action(BaseModel):
    """Accion que el usuario puede disparar desde la UI.

    type es generico y depende del vertical:
      real_estate: SEARCH_PROPERTIES, SHOW_PROPERTY, COMPARE_PROPERTIES,
                   REQUEST_VISIT, REQUEST_INFO, CONTACT_AGENT
      hospitality: SHOW_MENU, CHECK_RESERVATION, REQUEST_TABLE, ...
      guest:       CHECKIN_INFO, SHOW_PARKING, LOCAL_RECOMMENDATIONS, ...
    """
    type: str
    label: str = ""
    payload: dict = Field(default_factory=dict)


class LeadHint(BaseModel):
    """Sugerencia de captura de lead. suggest reemplaza al viejo sugerir_lead."""
    suggest: bool = False
    reason: str = ""


class ChatResponseV2(BaseModel):
    """Contrato enriquecido: mensaje + intencion + UI + acciones.

    Mantiene alias de compatibilidad (respuesta/nivel/sugerir_lead) para
    que el widget actual siga funcionando durante la transicion.
    """
    message: str
    session_id: str
    level: Literal[1, 2, 3]
    ui: UIBlock | None = None
    actions: list[Action] = Field(default_factory=list)
    lead: LeadHint = Field(default_factory=LeadHint)

    # --- alias de compatibilidad (widget viejo lee estos) ---
    respuesta: str = ""
    nivel: Literal[1, 2, 3] | None = None
    sugerir_lead: bool = False


class Turno(BaseModel):
    role: Literal["user", "assistant"]
    content: str
