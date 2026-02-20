from fastapi import APIRouter, Depends, Query, status
from edugrade.schemas.mongo_institution import InstitutionCreate, InstitutionOut
from edugrade.services.mongo_institution import InstitutionService
from edugrade.core.db import get_mongo_db

router = APIRouter(prefix="/institutions", tags=["institutions"])


def get_service(db=Depends(get_mongo_db)) -> InstitutionService:
  return InstitutionService(db)

@router.post("", response_model=InstitutionOut, status_code=status.HTTP_201_CREATED)
async def create_institution(payload: InstitutionCreate, svc: InstitutionService = Depends(get_service)):
  return await svc.create(payload.model_dump())


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