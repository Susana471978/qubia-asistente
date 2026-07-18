from datetime import datetime, timedelta, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.core import security
from app.db import get_db
from app.deps import get_admin_user
from app.models.tenant import TenantCreate, TenantUpdate

router = APIRouter(prefix="/admin/tenants", tags=["admin"])

VENTANA_ROTACION_DIAS = 7


def _serializar(doc: dict) -> dict:
    doc["_id"] = str(doc["_id"])
    return doc


async def _obtener(db, tenant_id: str) -> dict:
    if not ObjectId.is_valid(tenant_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "ID invalido")
    doc = await db.tenants.find_one({"_id": ObjectId(tenant_id)})
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tenant no encontrado")
    return doc


@router.get("")
async def listar(_: dict = Depends(get_admin_user)) -> list[dict]:
    cursor = get_db().tenants.find({}).sort("nombre", 1)
    return [_serializar(d) async for d in cursor]


@router.get("/{tenant_id}")
async def detalle(tenant_id: str, _: dict = Depends(get_admin_user)) -> dict:
    return _serializar(await _obtener(get_db(), tenant_id))


@router.post("", status_code=status.HTTP_201_CREATED)
async def crear(payload: TenantCreate, _: dict = Depends(get_admin_user)) -> dict:
    db = get_db()
    ahora = datetime.now(timezone.utc)
    doc = {
        "slug": payload.slug,
        "nombre": payload.nombre,
        "status": payload.status,
        "created_at": ahora,
        "updated_at": ahora,
        "auth": {
            "public_key": security.generar_public_key(payload.slug),
            "key_rotated_at": ahora,
            "key_previous": None,
            "key_previous_expires_at": None,
            "allowed_origins": payload.allowed_origins,
        },
        "identidad": payload.identidad.model_dump(),
        "conocimiento": payload.conocimiento.model_dump(),
        "reglas_nivel1": [],
        "leads": {
            "activo": True,
            "campos": ["nombre", "telefono", "email", "motivo"],
            "campos_obligatorios": ["nombre", "telefono"],
            "destinos": [],
            "trigger": "intencion",
        },
        "limites": {"mensajes_dia": 500, "mensajes_minuto": 10, "max_turnos_memoria": 6},
        "modelo": {
            "proveedor": "groq",
            "nombre": None,
            "temperatura": 0.4,
            "max_tokens": 500,
        },
        "web": {"dominio": "", "cloudflare_project": "", "plantilla_version": "1.0.0"},
        "facturacion": {"alta": ahora, "cuota_mensual": 0, "estado_pago": "al_corriente"},
    }
    try:
        res = await db.tenants.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(status.HTTP_409_CONFLICT, "El slug ya existe")
    doc["_id"] = str(res.inserted_id)
    return doc


@router.patch("/{tenant_id}")
async def actualizar(
    tenant_id: str, payload: TenantUpdate, _: dict = Depends(get_admin_user)
) -> dict:
    db = get_db()
    actual = await _obtener(db, tenant_id)

    cambios: dict = {"updated_at": datetime.now(timezone.utc)}
    datos = payload.model_dump(exclude_unset=True, exclude_none=True)

    if "allowed_origins" in datos:
        cambios["auth.allowed_origins"] = datos.pop("allowed_origins")
    for campo, valor in datos.items():
        cambios[campo] = valor

    await db.tenants.update_one({"_id": ObjectId(tenant_id)}, {"$set": cambios})

    auth = actual.get("auth", {})
    security.invalidar_tenant_cache(auth.get("public_key"), auth.get("key_previous"))

    return _serializar(await _obtener(db, tenant_id))


@router.post("/{tenant_id}/rotar-key")
async def rotar_key(tenant_id: str, _: dict = Depends(get_admin_user)) -> dict:
    """Genera clave nueva y mantiene la anterior viva una semana."""
    db = get_db()
    actual = await _obtener(db, tenant_id)
    auth = actual.get("auth", {})
    anterior = auth.get("public_key")

    ahora = datetime.now(timezone.utc)
    nueva = security.generar_public_key(actual["slug"])

    await db.tenants.update_one(
        {"_id": ObjectId(tenant_id)},
        {
            "$set": {
                "auth.public_key": nueva,
                "auth.key_rotated_at": ahora,
                "auth.key_previous": anterior,
                "auth.key_previous_expires_at": ahora
                + timedelta(days=VENTANA_ROTACION_DIAS),
                "updated_at": ahora,
            }
        },
    )
    security.invalidar_tenant_cache(anterior, auth.get("key_previous"))

    return {
        "public_key": nueva,
        "key_previous": anterior,
        "expira_anterior": (ahora + timedelta(days=VENTANA_ROTACION_DIAS)).isoformat(),
    }


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def suspender(tenant_id: str, _: dict = Depends(get_admin_user)) -> None:
    """Baja logica. Los datos del cliente se conservan."""
    db = get_db()
    actual = await _obtener(db, tenant_id)
    await db.tenants.update_one(
        {"_id": ObjectId(tenant_id)},
        {"$set": {"status": "suspended", "updated_at": datetime.now(timezone.utc)}},
    )
    auth = actual.get("auth", {})
    security.invalidar_tenant_cache(auth.get("public_key"), auth.get("key_previous"))
