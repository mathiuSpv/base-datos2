from datetime import datetime, timezone, date
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

def date_to_datetime_utc(d: date) -> datetime:
  return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)

class StudentRepository:
  def __init__(self, db):
    self.col = db["student"]

  async def ensure_indexes(self) -> None:
    await self.col.create_index("lastName")
    await self.col.create_index("nationality")
    await self.col.create_index([("lastName", 1), ("birthDate", 1)])
    await self.col.create_index([("firstName", "text"), ("lastName", "text")])

  async def create(self, data: dict) -> dict:
    doc = {
      **data,
      "createdAt": datetime.now(timezone.utc),
    }
    if isinstance(doc.get("birthDate"), date):
      doc["birthDate"] = date_to_datetime_utc(doc["birthDate"])
    try:
      res = await self.col.insert_one(doc)
    except DuplicateKeyError:
      raise

    created = await self.col.find_one({"_id": res.inserted_id})
    return created

  async def get_by_id(self, student_id: ObjectId) -> dict | None:
    return await self.col.find_one({"_id": student_id})

  async def list(
    self,
    *,
    last_name: str | None = None,
    nationality: str | None = None,
    birth_date: str | None = None,
    limit: int = 50,
    skip: int = 0,
  ) -> list[dict]:
    q: dict = {}

    if last_name:
      q["lastName"] = last_name
    if nationality:
      q["nationality"] = nationality
    if birth_date:
      q["birthDate"] = birth_date

    cursor = self.col.find(q).sort("createdAt", -1).skip(skip).limit(limit)
    return [doc async for doc in cursor]

  async def delete(self, student_id: ObjectId) -> bool:
    res = await self.col.delete_one({"_id": student_id})
    return res.deleted_count == 1
