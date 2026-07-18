from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query

from app.db import get_db
from app.deps import get_admin_user

router = APIRouter(prefix="/admin/metrics", tags=["admin"])


@router.get("/uso")
async def uso(
    dias: int = Query(default=30, ge=1, le=365),
    tenant_id: str | None = None,
    _: dict = Depends(get_admin_user),
) -> list[dict]:
    desde = (datetime.now(timezone.utc) - timedelta(days=dias)).strftime("%Y-%m-%d")
    match: dict = {"fecha": {"$gte": desde}}
    if tenant_id:
        match["tenant_id"] = tenant_id

    pipeline = [
        {"$match": match},
        {
            "$group": {
                "_id": "$tenant_id",
                "mensajes": {"$sum": "$mensajes"},
                "nivel_1": {"$sum": {"$ifNull": ["$nivel_1", 0]}},
                "nivel_2": {"$sum": {"$ifNull": ["$nivel_2", 0]}},
                "nivel_3": {"$sum": {"$ifNull": ["$nivel_3", 0]}},
            }
        },
        {"$sort": {"mensajes": -1}},
    ]
    return [
        {"tenant_id": d["_id"], **{k: v for k, v in d.items() if k != "_id"}}
        async for d in get_db().usage_daily.aggregate(pipeline)
    ]


@router.get("/leads")
async def leads(
    dias: int = Query(default=30, ge=1, le=365),
    tenant_id: str | None = None,
    _: dict = Depends(get_admin_user),
) -> list[dict]:
    desde = datetime.now(timezone.utc) - timedelta(days=dias)
    match: dict = {"created_at": {"$gte": desde}}
    if tenant_id:
        match["tenant_id"] = tenant_id

    pipeline = [
        {"$match": match},
        {
            "$group": {
                "_id": "$tenant_id",
                "total": {"$sum": 1},
                "entregados": {"$sum": {"$cond": ["$entregado", 1, 0]}},
            }
        },
        {"$sort": {"total": -1}},
    ]
    return [
        {"tenant_id": d["_id"], "total": d["total"], "entregados": d["entregados"]}
        async for d in get_db().leads.aggregate(pipeline)
    ]
