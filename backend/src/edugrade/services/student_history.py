# edugrade/services/history/student_history.py
from __future__ import annotations

from datetime import date
from fastapi import HTTPException

from edugrade.services.neo4j_graph import Neo4jGraphService
from edugrade.repository.mongo.institution import InstitutionRepository
from edugrade.utils.object_id import is_objectid_hex


def _year_start(y: int) -> date:
  return date(y, 1, 1)

def _year_end(y: int) -> date:
  return date(y, 12, 31)

def _coalesce_end(d: date | None) -> date:
  return d if d else date.today()

def _intersects(a_from: date, a_to: date, b_from: date, b_to: date) -> bool:
  return a_from <= b_to and b_from <= a_to


class StudentHistoryService:
  def __init__(self, mongo_db, neo: Neo4jGraphService):
    self.inst_repo = InstitutionRepository(mongo_db)
    self.neo = neo

  async def get_history(self, student_id: str) -> dict:
    if not is_objectid_hex(student_id):
      raise HTTPException(status_code=400, detail="Invalid studentId")
    
    rows = self.neo.get_student_history_rows(student_id)
    if not rows:
      return {"years": []}
    
    inst_ids = sorted({r["institutionMongoId"] for r in rows})
    inst_docs = await self.inst_repo.get_by_ids(inst_ids)
    inst_name_by_id = {str(d["_id"]): d.get("name") for d in inst_docs if d.get("name")}

    enrollment_by_inst: dict[str, tuple[date, date | None]] = {}
    for r in rows:
      iid = r["institutionMongoId"]

      try:
        inst_from = date.fromisoformat(r["institutionStartDate"])
      except Exception:
        raise HTTPException(status_code=500, detail="Neo4j data error: invalid institutionStartDate")

      inst_to = None
      if r.get("institutionEndDate"):
        try:
          inst_to = date.fromisoformat(r["institutionEndDate"])
        except Exception:
          raise HTTPException(status_code=500, detail="Neo4j data error: invalid institutionEndDate")

      if iid not in enrollment_by_inst:
        enrollment_by_inst[iid] = (inst_from, inst_to)
      else:
        cur_fr, cur_to = enrollment_by_inst[iid]
        new_fr = min(cur_fr, inst_from)
        if cur_to is None or inst_to is None:
          new_to = None
        else:
          new_to = max(cur_to, inst_to)
        enrollment_by_inst[iid] = (new_fr, new_to)

    periods = [(fr, _coalesce_end(to)) for fr, to in enrollment_by_inst.values()]
    min_year = min(fr.year for fr, _ in periods)
    max_year = max(to.year for _, to in periods)
    
    rows_by_inst: dict[str, list[dict]] = {}
    for r in rows:
      rows_by_inst.setdefault(r["institutionMongoId"], []).append(r)

    years_out: list[dict] = []
    for y in range(min_year, max_year + 1):
      y_from, y_to = _year_start(y), _year_end(y)
      institutions_out: list[dict] = []

      for iid, (inst_from, inst_to_opt) in enrollment_by_inst.items():
        inst_to = _coalesce_end(inst_to_opt)
        if not _intersects(inst_from, inst_to, y_from, y_to):
          continue

        subjects_out: list[dict] = []
        for rr in rows_by_inst.get(iid, []):
          try:
            s_from = date.fromisoformat(rr["subjectStartDate"])
          except Exception:
            raise HTTPException(status_code=500, detail="Neo4j data error: invalid subjectStartDate")

          s_to = None
          if rr.get("subjectEndDate"):
            try:
              s_to = date.fromisoformat(rr["subjectEndDate"])
            except Exception:
              raise HTTPException(status_code=500, detail="Neo4j data error: invalid subjectEndDate")

          if s_from.year != y:
            continue

          subjects_out.append({
            "subjectId": rr["subjectId"],
            "name": rr["subjectName"],  # Neo4j
            "fromDate": s_from.isoformat(),
            "toDate": s_to.isoformat() if s_to else None,
          })

        subjects_out.sort(key=lambda x: x["fromDate"])

        institutions_out.append({
          "institutionId": iid,
          "name": inst_name_by_id.get(iid),
          "subjects": subjects_out,
        })

      years_out.append({"year": y, "institutions": institutions_out})

    return {"years": years_out}