from bson import ObjectId
from fastapi import HTTPException
from datetime import date, timezone, datetime
from edugrade.repository.mongo_grade import GradeRepository
from edugrade.utils.date import date_to_datetime_utc

class GradeService:
  def __init__(self, db):
    self.repo = GradeRepository(db)
    # self.rules = CoversionRule

  async def create(self, payload: dict) -> dict:
    doc = dict(payload)
    
    if isinstance(doc.get("date"), date):
      doc["date"] = date_to_datetime_utc(doc["date"])

    doc["createdAt"] = datetime.now(timezone.utc)

    # value_converted = await self.rules.convert(
    #   system=doc["system"],
    #   on_date=payload["date"],
    #   value=float(doc["value"]),
    # )
    
    # doc["value_converted"] = value_converted

    return await self.repo.create(doc)

  async def get(self, grade_id: str) -> dict:
    if not ObjectId.is_valid(grade_id):
      raise HTTPException(status_code=400, detail="Invalid id")

    doc = await self.repo.get_by_id(ObjectId(grade_id))
    if not doc:
      raise HTTPException(status_code=404, detail="Grade not found")

    return doc

  async def list_by_period(
    self,
    id_subject: str,
    id_student: str,
    id_institution: str,
    date_from: date,
    date_to: date,
    limit: int,
    skip: int,
  ) -> list[dict]:
    return await self.repo.list_by_period(
      id_subject=id_subject,
      id_student=id_student,
      id_institution=id_institution,
      date_from=date_from,
      date_to=date_to,
      limit=limit,
      skip=skip,
    )
