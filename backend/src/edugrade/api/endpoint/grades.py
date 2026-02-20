from fastapi import APIRouter, Depends, Query, status
from datetime import date
from edugrade.schemas.mongo_grade import GradeCreate, GradeOut
from edugrade.services.mongo_grade import GradeService
from edugrade.core.db import get_mongo_db

router = APIRouter(prefix="/grades", tags=["grades"])

def get_service(db=Depends(get_mongo_db)) -> GradeService:
  return GradeService(db)

@router.post("", response_model=GradeOut, status_code=status.HTTP_201_CREATED)
async def create_grade(payload: GradeCreate, svc: GradeService = Depends(get_service)):
  return await svc.create(payload.model_dump())

@router.get("/{grade_id}", response_model=GradeOut)
async def get_grade(grade_id: str, svc: GradeService = Depends(get_service)):
  return await svc.get(grade_id)

@router.get("", response_model=list[GradeOut])
async def list_grades(
  id_subject: str = Query(...),
  id_student: str = Query(...),
  id_institution: str = Query(...),
  from_: date = Query(..., alias="from"),
  to: date = Query(...),
  limit: int = Query(50, ge=1, le=200),
  skip: int = Query(0, ge=0),
  svc: GradeService = Depends(get_service),
):
  return await svc.list_by_period(id_subject, id_student, id_institution, from_, to, limit, skip)
