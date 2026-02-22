from bson import ObjectId
from fastapi import HTTPException
from edugrade.repository.mongo.institution import InstitutionRepository
from edugrade.audit.context import AuditContext


class InstitutionService:
  def __init__(self, db, audit_logger):
    self.repo = InstitutionRepository(db)
    self.audit_logger = audit_logger

  async def create(self, payload: dict, audit: AuditContext) -> dict:
    try:
      created = await self.repo.create(payload)

      self.audit_logger.log(
        operation="CREATE",
        db="mongo",
        entity_type="Institution",
        entity_id=created["_id"],
        request_id=audit.request_id,
        user_name=audit.user_name,
        status="SUCCESS",
        payload_summary="created institution",
      )
      return created

    except Exception as e:
      self.audit_logger.log(
        operation="CREATE",
        db="mongo",
        entity_type="Institution",
        entity_id="(pending)",
        request_id=audit.request_id,
        user_name=audit.user_name,
        status="ERROR",
        error_code=type(e).__name__,
        error_message=str(e)[:500],
        payload_summary="create institution failed",
      )
      raise

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