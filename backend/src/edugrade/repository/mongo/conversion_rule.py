from __future__ import annotations

from datetime import date as date_type, datetime
from typing import Any

from pymongo import ReturnDocument


class ConversionRuleRepository:
  def __init__(self, db):
    self.col = db["conversionRules"]

  async def ensure_indexes(self) -> None:
    await self.col.create_index(
      [("direction", 1), ("system", 1), ("country", 1), ("grade.min", 1), ("grade.max", 1), ("validFrom", 1), ("validTo", 1)]
    )

    await self.col.create_index(
      [("direction", 1), ("system", 1), ("country", 1), ("grade.min", 1), ("grade.max", 1), ("validTo", 1)],
      unique=True,
      partialFilterExpression={"validTo": None},
    )

  async def create(self, doc: dict) -> dict:
    res = await self.col.insert_one(doc)
    return await self.col.find_one({"_id": res.inserted_id})

  async def get_current(
    self,
    *,
    direction: str,
    system: str,
    country: str | None,
    grade: str,
  ) -> dict | None:
    q: dict[str, Any] = {
      "direction": direction,
      "system": system,
      "grade.min": {"$lte": grade},
      "grade.max": {"$gte": grade},
      "validTo": None,
    }
    if country is not None:
      q["$or"] = [{"country": country}, {"country": "ANY"}, {"country": {"$exists": False}}, {"country": None}]
    else:
      q["$or"] = [{"country": "ANY"}, {"country": {"$exists": False}}, {"country": None}]
    return await self.col.find_one(q, sort=[("validFrom", -1)])

  async def get_for_date(
    self,
    *,
    direction: str,
    system: str,
    country: str | None,
    grade: str,
    when: datetime,
  ) -> dict | None:
    q: dict[str, Any] = {
      "direction": direction,
      "system": system,
      "grade.min": {"$lte": grade},
      "grade.max": {"$gte": grade},
      "validFrom": {"$lte": when},
      "$or": [{"validTo": None}, {"validTo": {"$gte": when}}],
    }

    if country is not None:
      q["$and"] = [
        {
          "$or": [{"country": country}, {"country": "ANY"}, {"country": {"$exists": False}}, {"country": None}]
        }
      ]
    else:
      q["$and"] = [
        {
          "$or": [{"country": "ANY"}, {"country": {"$exists": False}}, {"country": None}]
        }
      ]

    return await self.col.find_one(q, sort=[("validFrom", -1)])

  async def close_valid_to(
    self,
    *,
    direction: str,
    system: str,
    country: str | None,
    grade: str,
    valid_to: datetime,
  ) -> dict | None:
    q: dict[str, Any] = {
      "direction": direction,
      "system": system,
      "grade.min": {"$lte": grade},
      "grade.max": {"$gte": grade},
      "validTo": None,
    }

    if country is not None:
      q["$or"] = [{"country": country}, {"country": "ANY"}, {"country": {"$exists": False}}, {"country": None}]
    else:
      q["$or"] = [{"country": "ANY"}, {"country": {"$exists": False}}, {"country": None}]

    return await self.col.find_one_and_update(
      q,
      {"$set": {"validTo": valid_to}},
      sort=[("validFrom", -1)],
      return_document=ReturnDocument.AFTER,
    )