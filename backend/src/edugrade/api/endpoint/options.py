from fastapi import APIRouter, Depends, Query
from edugrade.core.db import get_mongo_db
from edugrade.services.mongo.options import OptionsService

router = APIRouter(prefix="/options", tags=["options"])

def get_service(db=Depends(get_mongo_db)) -> OptionsService:
  return OptionsService(db)

@router.get("/{key}")
async def get_option(
  key: str,
  only_values: bool = Query(default=False),
  svc: OptionsService = Depends(get_service),
):
  return await svc.get_option(key, only_values)