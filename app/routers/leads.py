from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.core.rate_limit import limiter
from app.db import get_db
from app.deps import get_tenant
from app.models.lead import LeadRequest, LeadResponse
from app.services import leads as leads_service

router = APIRouter(prefix="/v1", tags=["leads"])


@router.post("/lead", response_model=LeadResponse)
@limiter.limit("5/minute")
async def crear_lead(
    request: Request,
    response: Response,
    payload: LeadRequest,
    tenant: dict = Depends(get_tenant),
) -> LeadResponse:
    if not tenant.get("leads", {}).get("activo", False):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Captura de leads desactivada")

    faltan = leads_service.validar(tenant, payload)
    if faltan:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Faltan campos obligatorios: {', '.join(faltan)}",
        )

    await leads_service.registrar(get_db(), tenant, payload)
    return LeadResponse(ok=True, mensaje="Gracias. Te contactamos en breve.")
