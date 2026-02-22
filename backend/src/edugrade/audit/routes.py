from uuid import UUID
from fastapi import APIRouter, Request
from datetime import date, timedelta

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("/entities/{entity_type}/{entity_id}")
def audit_by_entity(request: Request, entity_type: str, entity_id: str, limit: int = 50):
    rows = request.app.state.audit_logger.list_by_entity(entity_type, entity_id, limit)
    return [dict(r._asdict()) for r in rows]

@router.get("/days/{day}")
def audit_by_day(request: Request, day: date, limit: int = 200):
    rows = request.app.state.audit_logger.list_by_day(day, limit)
    return [dict(r._asdict()) for r in rows]

@router.get("/requests/{request_id}")
def audit_by_request(request: Request, request_id: UUID, limit: int = 200):
    rows = request.app.state.audit_logger.list_by_request(request_id, limit)
    return [dict(r._asdict()) for r in rows]

@router.get("/recent")
def audit_recent(request: Request, days: int = 7, limit: int = 15):
    if days < 1 or days > 60:
        days = 7
    if limit < 1 or limit > 500:
        limit = 15

    today = date.today()

    # Traemos varios por día y luego recortamos globalmente
    per_day_limit = max(50, limit)  # suficiente para ordenar luego

    out: list[dict] = []
    for i in range(days):
        d = today - timedelta(days=i)
        rows = request.app.state.audit_logger.list_by_day(d, per_day_limit)
        out.extend([dict(r._asdict()) for r in rows])

    # Orden desc por ts (si ts viene como string ISO funciona bien)
    out.sort(key=lambda x: x.get("ts") or "", reverse=True)
    return out[:limit]