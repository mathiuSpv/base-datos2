from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from edugrade.schemas.neo4j.student import StudentOut
from edugrade.services.mongo.student import StudentService
from edugrade.schemas.mongo.institution import InstitutionCreate, InstitutionOut
from edugrade.services.mongo.institution import InstitutionService
from edugrade.core.db import get_mongo_db
from edugrade.services.neo4j_graph import Neo4jGraphService, get_neo4j_service
from edugrade.schemas.neo4j.subject import SubjectOut
from edugrade.audit.context import AuditContext, get_audit_context
from edugrade.audit.exec import audited
import asyncio

router = APIRouter(prefix="/institutions", tags=["institutions"])

async def _neo(callable_, *args, **kwargs):
    return await asyncio.to_thread(callable_, *args, **kwargs)

def get_service(request: Request,db=Depends(get_mongo_db)) -> InstitutionService:
  return InstitutionService(db, request.app.state.audit_logger)

def get_student_service(request: Request, db=Depends(get_mongo_db)) -> StudentService:
  return StudentService(db, request.app.state.audit_logger)

def svc_dep() -> Neo4jGraphService:
  return get_neo4j_service()

@router.post("", response_model=InstitutionOut, status_code=status.HTTP_201_CREATED)
async def create_institution(
  payload: InstitutionCreate,
  audit: AuditContext = Depends(get_audit_context),
  svc: InstitutionService = Depends(get_service),
  neo: Neo4jGraphService = Depends(get_neo4j_service)):
  
  mongo_response = await svc.create(payload.model_dump(),audit=audit)
  institution_id = None
  if isinstance(mongo_response, dict):
    institution_id = mongo_response.get("id") or mongo_response.get("_id")

  if not institution_id:
    raise HTTPException(status_code=500, detail="Institution created in Mongo but id not found in response")

  await _neo(neo.upsert_institution, str(institution_id))
  return mongo_response

@router.get("/{institution_id}", response_model=InstitutionOut)
async def get_institution(institution_id: str, svc: InstitutionService = Depends(get_service)):
  return await svc.get(institution_id)

@router.get("/{institutionMongoId}/subjects", response_model=list[SubjectOut])
async def get_subjects_by_institution(
    institutionMongoId: str,
    svc: Neo4jGraphService = Depends(svc_dep),
):
    try:
      return await _neo(svc.get_subjects_by_institution, institutionMongoId)
    except Exception as e:
      raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=list[InstitutionOut])
async def list_institutions(
  name: str | None = Query(default=None, description="LIKE '%name%' (case-insensitive)"),
  country: str | None = Query(default=None),
  address: str | None = Query(default=None, description="requires country; LIKE '%address%' (case-insensitive)"),
  limit: int = Query(default=50, ge=1, le=200),
  skip: int = Query(default=0, ge=0),
  svc: InstitutionService = Depends(get_service),
):
  return await svc.list(name, country, address, limit, skip)

@router.get("/by-student/{student_id}", response_model=list[InstitutionOut])
async def list_institutions_for_student(
  student_id: str,
  svc: InstitutionService = Depends(get_service),
  neo: Neo4jGraphService = Depends(get_neo4j_service),
):
  institution_ids = await _neo(neo.get_student_institutions, student_id)

  results: list[InstitutionOut] = []
  for institution_id in institution_ids:
    inst = await svc.get(institution_id.get('institutionId'))
    if inst is not None:
      results.append(inst)

  return results

@router.get("/{institution_id}/students", response_model=list[StudentOut])
async def list_students_for_institution(
  institution_id: str,
  student_svc: StudentService = Depends(get_student_service),
  neo: Neo4jGraphService = Depends(get_neo4j_service),
):
  student_ids: list[str] = await _neo(neo.get_students_by_institution, institution_id)

  out: list[StudentOut] = []
  for sid in student_ids:
    out.append(await student_svc.get(sid))

  return out

@router.post("/{institution_id}/subjects", response_model=SubjectOut, status_code=status.HTTP_201_CREATED)
async def create_subject_for_institution(
    institution_id: str,
    name: str = Query(...),
    audit: AuditContext = Depends(get_audit_context),
    neo: Neo4jGraphService = Depends(get_neo4j_service),
    request: Request = None,
):
    audit_logger = request.app.state.audit_logger

    async def _do():
        return await _neo(neo.upsert_subject, name, institution_id)

    try:
        subject = await audited(
            audit_logger=audit_logger,
            audit=audit,
            operation="CREATE",
            db="neo4j",
            entity_type="Subject",
            entity_id=f"{institution_id}:{name}",
            payload_summary=f"subject create; institutionId={institution_id} name={name}",
            fn=_do,
        )
        return subject
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
