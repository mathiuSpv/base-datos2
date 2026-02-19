from datetime import datetime, timezone, date
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from edugrade.utils.date import date_to_datetime_utc

class StudentRepository:
  def __init__(self, db):
    self.col = db["student"]

  async def ensure_indexes(self) -> None:
    await self.col.create_index([("nationality", 1), ("identity", 1)])
    await self.col.create_index("lastName")
    await self.col.create_index("firstName")
    
  async def create(self, data: dict) -> dict:
    doc = {
      **data,
      "createdAt": datetime.now(timezone.utc),
    }
    if isinstance(doc.get("birthDate"), date):
      doc["birthDate"] = date_to_datetime_utc(doc["birthDate"])
      
    identity = doc.get("identity")
    if identity is None or str(identity).strip() == "":
      doc.pop("identity", None)
    try:
      res = await self.col.insert_one(doc)
    except DuplicateKeyError:
      raise

    created = await self.col.find_one({"_id": res.inserted_id})
    created["_id"] = str(created["_id"])
    return created

  async def get_by_id(self, student_id: ObjectId) -> dict | None:
    return await self.col.find_one({"_id": student_id})

  async def list(
    self,
    *,
    first_name: str | None = None,
    last_name_like: str | None = None,
    nationality: str | None = None,
    identity: str | None = None,
    limit: int = 50,
    skip: int = 0,
  ) -> list[dict]:
    q: dict = {}

    if identity and nationality:
      q["identity"] = identity; q["nationality"] = nationality
      
    if first_name:
      q["firstName"] = {"$regex": first_name, "$options": "i"}
    
    if last_name_like:
      q["lastName"] = {"$regex": last_name_like, "$options": "i"}
      
    if nationality and "nationality" not in q:
      q["nationality"] = nationality

    cursor = self.col.find(q).sort("createdAt", -1).skip(skip).limit(limit)
    return [doc async for doc in cursor]

  async def delete(self, student_id: ObjectId) -> bool:
    res = await self.col.delete_one({"_id": student_id})
    return res.deleted_count == 1
