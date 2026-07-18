from datetime import datetime

from pydantic import BaseModel, Field


class LeadRequest(BaseModel):
    session_id: str | None = None
    nombre: str = Field(default="", max_length=120)
    telefono: str = Field(default="", max_length=40)
    email: str = Field(default="", max_length=160)
    motivo: str = Field(default="", max_length=1000)
    extra: dict = Field(default_factory=dict)


class LeadResponse(BaseModel):
    ok: bool
    mensaje: str


class LeadStored(BaseModel):
    tenant_id: str
    session_id: str | None
    nombre: str
    telefono: str
    email: str
    motivo: str
    extra: dict
    created_at: datetime
    entregado: bool = False
