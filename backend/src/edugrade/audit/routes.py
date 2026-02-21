from datetime import date
from uuid import UUID
from fastapi import APIRouter, Request

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
