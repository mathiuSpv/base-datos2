from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from edugrade.audit.context import AuditContext, get_audit_context
from edugrade.core.db import get_mongo_db
from edugrade.schemas.mongo.student import StudentCreate, StudentOut
from edugrade.services.mongo.student import StudentService
from edugrade.services.neo4j_graph import Neo4jGraphService, get_neo4j_service

router = APIRouter(prefix="/students", tags=["students"])

def get_service(request: Request, db=Depends(get_mongo_db)) -> StudentService:
  return StudentService(db, request.app.state.audit_logger)

@router.post("", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
async def create_student(
  payload: StudentCreate, 
  audit: AuditContext = Depends(get_audit_context),
  svc: StudentService = Depends(get_service),
  neo: Neo4jGraphService = Depends(get_neo4j_service)):
  mongo_response = await svc.create(payload.model_dump(), audit=audit)
  if isinstance(mongo_response, dict):
    student_id = mongo_response.get("id") or mongo_response.get("_id")
  if not student_id:
    raise HTTPException(status_code=500, detail="Student created in Mongo but id not found in response")
  neo.upsert_student(str(student_id))
  return mongo_response


@router.get("/{student_id}", response_model=StudentOut)
async def get_student(student_id: str, svc: StudentService = Depends(get_service)):
  return await svc.get(student_id)


@router.get("", response_model=list[StudentOut])
async def list_students(
  firstName: str | None = Query(default=None),
  lastName: str | None = Query(default=None, description="LIKE '%lastName%' (case-insensitive)"),
  nationality: str | None = Query(default=None),
  identity: str | None = Query(default=None, description="requires nationality"),
  limit: int = Query(default=50, ge=1, le=200),
  skip: int = Query(default=0, ge=0),
  svc: StudentService = Depends(get_service),
):
  return await svc.list(firstName, lastName, nationality, identity, limit, skip)


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(
  student_id: str, 
  audit: AuditContext = Depends(get_audit_context),
  svc: StudentService = Depends(get_service)):
  await svc.delete(student_id, audit=audit)
  return "0"