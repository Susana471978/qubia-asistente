from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.core.security import HEADER_NAME


def ip_real(request: Request) -> str:
    cf = request.headers.get("CF-Connecting-IP")
    if cf:
        return cf.strip()
    fwd = request.headers.get("X-Forwarded-For")
    if fwd:
        return fwd.split(",")[0].strip()
    return get_remote_address(request)


def clave_tenant_ip(request: Request) -> str:
    key = request.headers.get(HEADER_NAME, "sin-key")
    return f"{key}:{ip_real(request)}"


limiter = Limiter(key_func=clave_tenant_ip, headers_enabled=True)
