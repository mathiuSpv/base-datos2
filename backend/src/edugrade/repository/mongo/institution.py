from datetime import datetime, timezone
from bson import ObjectId
import re

class InstitutionRepository:
  def __init__(self, db):
    self.col = db['institutions']

  async def ensure_indexes(self) -> None:
    await self.col.create_index("name")
    await self.col.create_index([("country", 1), ("address", 1)])

  async def create(self, payload: dict) -> dict:
    doc = dict(payload)
    doc["createdAt"] = datetime.now(timezone.utc)

    res = await self.col.insert_one(doc)
    return await self.col.find_one({"_id": res.inserted_id})

  async def get_by_id(self, institution_id: ObjectId) -> dict | None:
    return await self.col.find_one({"_id": institution_id})

  async def list(
    self,
    *,
    name: str,
    country: str,
    address: str | None = None,
    limit: int = 50,
    skip: int = 0,
  ) -> list[dict]:
    q: dict = {}
    if name:
      q["name"] = {"$regex": re.escape(name), "$options": "i"}

    if address and country:
      q["address"] = {"$regex": re.escape(address), "$options": "i"}
      q["country"] = country
        
    if country and "country" not in q:
      q["country"] = country

    cursor = self.col.find(q).sort("createdAt", -1).skip(skip).limit(limit)
    return [doc async for doc in cursor]