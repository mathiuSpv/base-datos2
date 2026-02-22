from datetime import date
from fastapi import APIRouter, Depends, Query, status, Request
from edugrade.core.db import get_mongo_db
from edugrade.schemas.mongo.grade import GradeCreate, GradeOut
from edugrade.audit.context import AuditContext, get_audit_context
from edugrade.services.mongo.grade import GradeService

router = APIRouter(prefix="/exams", tags=["exams"])

def get_service(request: Request,db=Depends(get_mongo_db)) -> GradeService:
  return GradeService(db, request.app.state.audit_logger)

@router.post("", response_model=GradeOut, status_code=status.HTTP_201_CREATED)
async def create_exam(
    payload: GradeCreate, 
    audit: AuditContext = Depends(get_audit_context),
    svc: GradeService = Depends(get_service)):
  return await svc.create(payload.model_dump(), audit=audit)

@router.get("/{exam_id}", response_model=GradeOut)
async def get_exam(
  exam_id: str,
  targetSystem: str | None = Query(default=None, description="None => original; 'ZA' => ZA; other => convert from ZA to that system"),
  svc: GradeService = Depends(get_service),
):
  return await svc.get_projected(exam_id, targetSystem)

@router.get("", response_model=list[GradeOut])
async def list_exams(
  subjectId: str | None = Query(default=None),
  studentId: str | None = Query(default=None),
  institutionId: str | None = Query(default=None),
  fromDate: date = Query(...),
  toDate: date = Query(...),
  limit: int = Query(default=50, ge=1, le=200),
  skip: int = Query(default=0, ge=0),
  targetSystem: str | None = Query(default=None, description="None => original; 'ZA' => ZA; other => convert from ZA to that system"),
  svc: GradeService = Depends(get_service),
):
  return await svc.list_projected(subjectId, studentId, institutionId, fromDate, toDate, limit, skip, targetSystem)