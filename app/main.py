import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.core import security
from app.core.rate_limit import limiter
from app.db import connect, disconnect, get_db
from app.routers import chat, health, leads
from app.routers.admin import auth as admin_auth
from app.routers.admin import metrics as admin_metrics
from app.routers.admin import tenants as admin_tenants

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("qubia")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect()
    log.info("Qubia arrancado en entorno %s", settings.app_env)
    yield
    await disconnect()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.is_dev else None,
    redoc_url=None,
    openapi_url="/openapi.json" if settings.is_dev else None,
)

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": "Demasiadas peticiones. Espera un momento."},
    )


# CORS del panel de administracion (origenes fijos y conocidos)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.admin_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def cors_por_tenant(request: Request, call_next):
    """CORS dinamico para los endpoints publicos: cada web de cliente tiene su
    propio dominio, asi que el Origin permitido se resuelve desde el tenant."""
    origin = request.headers.get("Origin")
    ruta_publica = request.url.path.startswith("/v1")

    if not (ruta_publica and origin):
        return await call_next(request)

    key = request.headers.get(security.HEADER_NAME, "")
    permitido = False
    if key:
        try:
            tenant = await security.resolver_tenant(get_db(), key)
            permitido = security.origen_permitido(
                origin, tenant.get("auth", {}).get("allowed_origins", [])
            )
        except Exception:
            permitido = False

    if request.method == "OPTIONS":
        if not permitido:
            return Response(status_code=403)
        return Response(
            status_code=204,
            headers={
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
                "Access-Control-Allow-Headers": f"Content-Type, {security.HEADER_NAME}",
                "Access-Control-Max-Age": "86400",
                "Vary": "Origin",
            },
        )

    response = await call_next(request)
    if permitido:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
    return response


app.include_router(health.router)
app.include_router(chat.router)
app.include_router(leads.router)
app.include_router(admin_auth.router)
app.include_router(admin_tenants.router)
app.include_router(admin_metrics.router)
