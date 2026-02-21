from bson import ObjectId
from fastapi import HTTPException
from edugrade.repository.mongo.institution import InstitutionRepository


class InstitutionService:
  def __init__(self, db):
    self.repo = InstitutionRepository(db)

  async def create(self, payload: dict) -> dict:
    return await self.repo.create(payload)

  async def get(self, institution_id: str) -> dict:
    if not ObjectId.is_valid(institution_id):
      raise HTTPException(status_code=400, detail="Invalid id")

    doc = await self.repo.get_by_id(ObjectId(institution_id))
    if not doc:
      raise HTTPException(status_code=404, detail="Institution not found")

    return doc

  async def list(
    self,
    name: str | None,
    country: str | None,
    address: str | None,
    limit: int,
    skip: int,
  ) -> list[dict]:
    if address and not country:
      raise HTTPException(status_code=400, detail="country is required when address is provided")

    return await self.repo.list(name=name, country=country, address=address, limit=limit, skip=skip)