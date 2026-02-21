from datetime import date as date_type
from bson import ObjectId

class GradeRepository:
  def __init__(self, db):
    self.col = db["grades"]

  async def ensure_indexes(self) -> None:
    # consulta principal: subject+student+institution
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
    subject_id: str,
    student_id: str,
    institution_id: str,
    date_from: date_type,
    date_to: date_type,
    limit: int,
    skip: int,
  ) -> list[dict]:
    q = {
      "subjectId": subject_id,
      "studentId": student_id,
      "institutionId": institution_id,
      "date": {"$gte": date_from, "$lte": date_to},
    }

    cursor = (
      self.col.find(q)
      .sort("date", 1)
      .skip(skip)
      .limit(limit)
    )
    
    return [doc async for doc in cursor]