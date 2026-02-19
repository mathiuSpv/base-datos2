from fastapi import APIRouter, Depends, Query, status
from edugrade.core.db import get_mongo_db
from edugrade.schemas.mongo_student import StudentCreate, StudentOut
from edugrade.services.mongo_student import StudentService

router = APIRouter(prefix="/students", tags=["students"])

def get_service(db=Depends(get_mongo_db)) -> StudentService:
  return StudentService(db)

@router.post("", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
async def create_student(payload: StudentCreate, svc: StudentService = Depends(get_service)):
  return await svc.create(payload.model_dump())


@router.get("/{student_id}", response_model=StudentOut)
async def get_student(student_id: str, svc: StudentService = Depends(get_service)):
  return await svc.get(student_id)


@router.get("", response_model=list[StudentOut])
async def list_students(
  lastName: str | None = Query(default=None),
  nationality: str | None = Query(default=None),
  birthDate: str | None = Query(default=None, description="YYYY-MM-DD"),
  limit: int = Query(default=50, ge=1, le=200),
  skip: int = Query(default=0, ge=0),
  svc: StudentService = Depends(get_service),
):
  return await svc.list(lastName, nationality, birthDate, limit, skip)


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(student_id: str, svc: StudentService = Depends(get_service)):
  await svc.delete(student_id)
  return None