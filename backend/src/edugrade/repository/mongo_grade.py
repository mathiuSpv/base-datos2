from datetime import date
from bson import ObjectId
from edugrade.utils.date import date_to_datetime_utc

class GradeRepository:
  def __init__(self, db):
    self.col = db["grades"]

  async def ensure_indexes(self) -> None:
    # consulta principal: subject+student+institution + date range + sort by date asc
    await self.col.create_index(
      [("id_subject", 1), ("id_student", 1), ("id_institution", 1), ("date", 1)]
    )

  async def create(self, doc: dict) -> dict:
    res = await self.col.insert_one(doc)
    return await self.col.find_one({"_id": res.inserted_id})

  async def get_by_id(self, _id: ObjectId) -> dict | None:
    return await self.col.find_one({"_id": _id})

  async def list_by_period(
    self,
    *,
    id_subject: str,
    id_student: str,
    id_institution: str,
    date_from: date,
    date_to: date,
    limit: int,
    skip: int,
  ) -> list[dict]:
    q = {
      "id_subject": id_subject,
      "id_student": id_student,
      "id_institution": id_institution,
      "date": {
        "$gte": date_to_datetime_utc(date_from),
        "$lte": date_to_datetime_utc(date_to),
      },
    }

    cursor = (
      self.col.find(q)
      .sort("date", 1)
      .skip(skip)
      .limit(limit)
    )

    return [doc async for doc in cursor]
