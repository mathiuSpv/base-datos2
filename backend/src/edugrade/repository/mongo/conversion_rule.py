from datetime import date as date_type
from pymongo import ReturnDocument


class ConversionRuleRepository:
  def __init__(self, db):
    self.col = db["conversionRules"]

  async def ensure_indexes(self) -> None:
    await self.col.create_index(
      [("system", 1), ("country", 1), ("grade", 1), ("validFrom", 1), ("validTo", 1)]
    )
    
    await self.col.create_index(
      [("system", 1), ("country", 1), ("grade", 1), ("validTo", 1)],
      unique=True,
      partialFilterExpression={"validTo": None},
    )

  async def create(self, doc: dict) -> dict:
    res = await self.col.insert_one(doc)
    return await self.col.find_one({"_id": res.inserted_id})

  async def get_current(self, *, system: str, country: str, grade: str) -> dict | None:
    return await self.col.find_one(
      {"system": system, "country": country, "grade": grade, "validTo": None}
    )

  async def get_for_date(
    self,
    *,
    system: str,
    country: str,
    grade: str,
    when: date_type,
  ) -> dict | None:
    print(f"Finding conversion rule for system={system} country={country} grade={grade} when={when}")
    return await self.col.find_one(
      {
      "system": system,
      "country": country,
      "grade.min": {"$lte": grade},
      "grade.max": {"$gte": grade},
      "validFrom": {"$lte": when},
      "$or": [{"validTo": None}, {"validTo": {"$gte": when}}],
      },
      sort=[("validFrom", -1)],
    )

  async def close_valid_to(
    self,
    *,
    system: str,
    country: str,
    grade: str,
    valid_to: date_type,
  ) -> dict | None:
    return await self.col.find_one_and_update(
      {"system": system, "country": country, "grade": grade, "validTo": None},
      {"$set": {"validTo": valid_to}},
      return_document=ReturnDocument.AFTER,
    )