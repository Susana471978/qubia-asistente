from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core import errors, security
from app.db import get_db

bearer = HTTPBearer(auto_error=False)


async def get_tenant(
    request: Request,
    x_qubia_key: str = Header(default="", alias=security.HEADER_NAME),
) -> dict:
    """Resuelve el tenant desde la clave publica y valida origen y estado."""
    db = get_db()
    tenant = await security.resolver_tenant(db, x_qubia_key)

    if tenant.get("status") != "active":
        raise errors.tenant_inactivo()

    origin = request.headers.get("Origin") or request.headers.get("Referer")
    permitidos = tenant.get("auth", {}).get("allowed_origins", [])
    if not security.origen_permitido(origin, permitidos):
        raise errors.origen_no_permitido()

    return tenant


async def get_admin_user(
    cred: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict:
    if cred is None:
        raise errors.no_autorizado()
    payload = security.decodificar_token(cred.credentials)
    if payload.get("rol") != "admin":
        raise errors.no_autorizado()
    return payload
