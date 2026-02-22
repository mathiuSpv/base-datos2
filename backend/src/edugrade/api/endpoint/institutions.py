from fastapi import APIRouter, Depends, HTTPException, Query, status
from edugrade.schemas.mongo.institution import InstitutionCreate, InstitutionOut
from edugrade.services.mongo.institution import InstitutionService
from edugrade.core.db import get_mongo_db
from edugrade.services.neo4j_graph import Neo4jGraphService, get_neo4j_service

router = APIRouter(prefix="/institutions", tags=["institutions"])

def get_service(db=Depends(get_mongo_db)) -> InstitutionService:
  return InstitutionService(db)

@router.post("", response_model=InstitutionOut, status_code=status.HTTP_201_CREATED)
async def create_institution(
  payload: InstitutionCreate,
  svc: InstitutionService = Depends(get_service),
  neo: Neo4jGraphService = Depends(get_neo4j_service)):
  mongo_response = await svc.create(payload.model_dump())
  if isinstance(mongo_response, dict):
    institution_id = mongo_response.get("id") or mongo_response.get("_id")
  if not institution_id:
    raise HTTPException(status_code=500, detail="Institution created in Mongo but id not found in response")
  neo.upsert_institution(str(institution_id))
  return mongo_response

@router.get("/{institution_id}", response_model=InstitutionOut)
async def get_institution(institution_id: str, svc: InstitutionService = Depends(get_service)):
  return await svc.get(institution_id)

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