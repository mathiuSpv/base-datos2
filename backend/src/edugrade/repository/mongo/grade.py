from datetime import datetime
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
    date_from: datetime,
    date_to: datetime,
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
  
  async def delete(self, _id: ObjectId) -> bool:
    res = await self.col.delete_one({"_id": _id})
    return res.deleted_count == 1

  async def dashboard_summary(self, *, country: str, institution_id: str | None) -> dict:
    match_q: dict = {"country": country}
    if institution_id is not None:
      match_q["institutionId"] = institution_id

    pipeline = [
      {"$match": match_q},
      {
        "$addFields": {
          "_valueZA": {
            "$convert": {
              "input": "$valueConverted",
              "to": "double",
              "onError": None,
              "onNull": None,
            }
          }
        }
      },
      {
        "$group": {
          "_id": None,
          "examsRead": {"$sum": 1},
          "examsUsedInAverage": {"$sum": {"$cond": [{"$ne": ["$_valueZA", None]}, 1, 0]}},
          "sumZA": {"$sum": {"$ifNull": ["$_valueZA", 0]}},
        }
      },
      {
        "$project": {
          "_id": 0,
          "examsRead": 1,
          "examsUsedInAverage": 1,
          "averageZA": {
            "$cond": [
              {"$gt": ["$examsUsedInAverage", 0]},
              {"$divide": ["$sumZA", "$examsUsedInAverage"]},
              None,
            ]
          },
        }
      },
    ]

    cursor = self.col.aggregate(pipeline)
    rows = [doc async for doc in cursor]
    if not rows:
      return {"examsRead": 0, "examsUsedInAverage": 0, "averageZA": None}
    row = rows[0]
    if row.get("averageZA") is not None:
      row["averageZA"] = float(row["averageZA"])
    return row

  async def dashboard_subjects(self, *, country: str, institution_id: str) -> list[dict]:
    match_q = {"country": country, "institutionId": institution_id}

    pipeline = [
      {"$match": match_q},
      {
        "$addFields": {
          "_valueZA": {
            "$convert": {
              "input": "$valueConverted",
              "to": "double",
              "onError": None,
              "onNull": None,
            }
          }
        }
      },
      {
        "$group": {
          "_id": "$subjectId",
          "examsRead": {"$sum": 1},
          "examsUsedInAverage": {"$sum": {"$cond": [{"$ne": ["$_valueZA", None]}, 1, 0]}},
          "sumZA": {"$sum": {"$ifNull": ["$_valueZA", 0]}},
        }
      },
      {
        "$project": {
          "_id": 0,
          "subjectId": "$_id",
          "examsRead": 1,
          "examsUsedInAverage": 1,
          "averageZA": {
            "$cond": [
              {"$gt": ["$examsUsedInAverage", 0]},
              {"$divide": ["$sumZA", "$examsUsedInAverage"]},
              None,
            ]
          },
        }
      },
      {"$sort": {"subjectId": 1}},
    ]

    cursor = self.col.aggregate(pipeline)
    out = [doc async for doc in cursor]
    for d in out:
      if d.get("averageZA") is not None:
        d["averageZA"] = float(d["averageZA"])
    return out