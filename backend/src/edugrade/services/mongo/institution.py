from bson import ObjectId
from fastapi import HTTPException

from edugrade.repository.mongo.institution import InstitutionRepository
from edugrade.audit.context import AuditContext
from edugrade.audit.exec import audited


class InstitutionService:
  def __init__(self, db, audit_logger):
    self.repo = InstitutionRepository(db)
    self.audit_logger = audit_logger

  async def create(self, payload: dict, audit: AuditContext) -> dict:
    async def _do():
      return await self.repo.create(payload)

    def _entity_id(doc: dict) -> str:
      _id = doc.get("_id") or doc.get("id")
      return str(_id) if _id is not None else "(missing)"

    return await audited(
      audit_logger=self.audit_logger,
      audit=audit,
      operation="CREATE",
      db="mongo",
      entity_type="Institution",
      entity_id="(pending)",
      payload_summary=f"institution create; name={payload.get('name','?')}",
      fn=_do,
      entity_id_from_result=_entity_id,
    )

  async def get(self, institution_id: str) -> dict:
    if not ObjectId.is_valid(institution_id):
      raise HTTPException(status_code=400, detail="Invalid id")

    doc = await self.repo.get_one(institution_id)
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