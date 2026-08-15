from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Status = Literal["active", "suspended", "trial"]
Vertical = Literal["general", "real_estate", "hospitality", "guest"]


class Branding(BaseModel):
    business_name: str = ""
    logo_url: str = ""
    primary_color: str = "#0B1220"
    secondary_color: str = "#0D2B45"
    accent_color: str = "#00D4C7"
    silver_color: str = "#D7E2EB"
    champagne_color: str = "#C8A86B"
    assistant_icon: str = ""
    widget_position: Literal["bottom-right", "bottom-left"] = "bottom-right"
    widget_theme: Literal["dark", "light", "auto"] = "dark"


class Features(BaseModel):
    lead_enabled: bool = True
    booking_enabled: bool = False
    properties_enabled: bool = False


class Auth(BaseModel):
    public_key: str
    key_rotated_at: datetime | None = None
    key_previous: str | None = None
    key_previous_expires_at: datetime | None = None
    allowed_origins: list[str] = Field(default_factory=list)


class Identidad(BaseModel):
    nombre_asistente: str = "Asistente"
    tono: str = "cercano y profesional"
    idioma_principal: str = "es"
    idiomas_soportados: list[str] = Field(default_factory=lambda: ["es"])
    saludo_inicial: str = "Hola, ¿en qué puedo ayudarte?"
    mensaje_fuera_alcance: str = (
        "Eso lo ve mejor el equipo. ¿Quieres que te pongan en contacto?"
    )
    prompt_extra: str = ""


class Servicio(BaseModel):
    nombre: str
    descripcion: str = ""
    precio_desde: float | None = None


class Faq(BaseModel):
    pregunta: str
    respuesta: str


class Conocimiento(BaseModel):
    descripcion_negocio: str = ""
    horarios: str = ""
    direccion: str = ""
    telefono: str = ""
    email: str = ""
    servicios: list[Servicio] = Field(default_factory=list)
    faqs: list[Faq] = Field(default_factory=list)
    documentos: list[dict] = Field(default_factory=list)


class ReglaNivel1(BaseModel):
    id: str
    keywords: list[str]
    respuesta: str
    prioridad: int = 0


class DestinoLead(BaseModel):
    tipo: Literal["email", "webhook"]
    valor: str
    activo: bool = True


class Leads(BaseModel):
    activo: bool = True
    campos: list[str] = Field(default_factory=lambda: ["nombre", "telefono", "email", "motivo"])
    campos_obligatorios: list[str] = Field(default_factory=lambda: ["nombre", "telefono"])
    destinos: list[DestinoLead] = Field(default_factory=list)
    trigger: Literal["intencion", "siempre", "manual"] = "intencion"


class Limites(BaseModel):
    mensajes_dia: int = 500
    mensajes_minuto: int = 10
    max_turnos_memoria: int = 6


class ModeloCfg(BaseModel):
    proveedor: str = "groq"
    nombre: str | None = None
    temperatura: float = 0.4
    max_tokens: int = 500


class Web(BaseModel):
    dominio: str = ""
    cloudflare_project: str = ""
    plantilla_version: str = "1.0.0"


class Facturacion(BaseModel):
    alta: datetime | None = None
    cuota_mensual: float = 0
    estado_pago: str = "al_corriente"


class Tenant(BaseModel):
    slug: str
    nombre: str
    status: Status = "trial"
    created_at: datetime | None = None
    updated_at: datetime | None = None

    auth: Auth
    identidad: Identidad = Field(default_factory=Identidad)
    conocimiento: Conocimiento = Field(default_factory=Conocimiento)
    reglas_nivel1: list[ReglaNivel1] = Field(default_factory=list)
    leads: Leads = Field(default_factory=Leads)
    limites: Limites = Field(default_factory=Limites)
    modelo: ModeloCfg = Field(default_factory=ModeloCfg)
    web: Web = Field(default_factory=Web)
    facturacion: Facturacion = Field(default_factory=Facturacion)

    vertical: Vertical = "general"
    branding: Branding = Field(default_factory=Branding)
    features: Features = Field(default_factory=Features)
    quick_actions: list[str] = Field(default_factory=list)


class TenantCreate(BaseModel):
    slug: str
    nombre: str
    status: Status = "trial"
    allowed_origins: list[str] = Field(default_factory=list)
    identidad: Identidad = Field(default_factory=Identidad)
    conocimiento: Conocimiento = Field(default_factory=Conocimiento)
    vertical: Vertical = "general"
    branding: Branding = Field(default_factory=Branding)
    features: Features = Field(default_factory=Features)
    quick_actions: list[str] = Field(default_factory=list)


class TenantUpdate(BaseModel):
    nombre: str | None = None
    status: Status | None = None
    identidad: Identidad | None = None
    conocimiento: Conocimiento | None = None
    reglas_nivel1: list[ReglaNivel1] | None = None
    leads: Leads | None = None
    limites: Limites | None = None
    modelo: ModeloCfg | None = None
    web: Web | None = None
    allowed_origins: list[str] | None = None
    vertical: Vertical | None = None
    branding: Branding | None = None
    features: Features | None = None
    quick_actions: list[str] | None = None


class TenantPublic(BaseModel):
    """Lo que el widget puede leer sin autenticacion de admin."""

    slug: str
    nombre_asistente: str
    saludo_inicial: str
    idioma_principal: str
