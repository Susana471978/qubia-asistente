from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=8, max_length=64)
    mensaje: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    respuesta: str
    nivel: Literal[1, 2, 3]
    session_id: str
    sugerir_lead: bool = False


class Turno(BaseModel):
    role: Literal["user", "assistant"]
    content: str
