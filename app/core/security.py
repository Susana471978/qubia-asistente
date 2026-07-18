import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.core import errors
from app.core.cache import tenant_cache

KEY_PREFIX = "qb_pub"
HEADER_NAME = "X-Qubia-Key"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --------------------------------------------------------------------------
# Claves publicas de tenant
# --------------------------------------------------------------------------
def generar_public_key(slug: str) -> str:
    return f"{KEY_PREFIX}_{slug}_{secrets.token_hex(6)}"


def origen_permitido(origin: str | None, permitidos: list[str]) -> bool:
    """En dev se permite todo. En produccion el Origin debe estar en la lista.
    Se compara esquema+host+puerto, ignorando path y barra final."""
    if settings.is_dev:
        return True
    if not permitidos:
        return False
    if not origin:
        return False

    def norm(u: str) -> str:
        p = urlparse(u if "//" in u else f"https://{u}")
        return f"{p.scheme}://{p.netloc}".lower().rstrip("/")

    return norm(origin) in {norm(p) for p in permitidos}


async def resolver_tenant(db, public_key: str) -> dict:
    """Resuelve una clave publica a documento de tenant, con cache."""
    if not public_key or not public_key.startswith(KEY_PREFIX):
        raise errors.tenant_no_encontrado()

    cached = tenant_cache.get(public_key)
    if cached is not None:
        return cached

    ahora = datetime.now(timezone.utc)
    doc = await db.tenants.find_one({"auth.public_key": public_key})

    if doc is None:
        # Clave anterior aun vigente (ventana de rotacion)
        doc = await db.tenants.find_one(
            {
                "auth.key_previous": public_key,
                "auth.key_previous_expires_at": {"$gt": ahora},
            }
        )

    if doc is None:
        raise errors.tenant_no_encontrado()

    doc["_id"] = str(doc["_id"])
    tenant_cache.set(public_key, doc)
    return doc


def invalidar_tenant_cache(*keys: str | None) -> None:
    for k in keys:
        if k:
            tenant_cache.invalidate(k)


# --------------------------------------------------------------------------
# Auth de administracion (interno Objetiva)
# --------------------------------------------------------------------------
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verificar_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def crear_access_token(subject: str, rol: str = "admin") -> str:
    expira = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_min)
    payload = {"sub": subject, "rol": rol, "exp": expira}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def decodificar_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
    except JWTError:
        raise errors.no_autorizado()
