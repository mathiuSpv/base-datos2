# edugrade/services/history/student_history.py
from __future__ import annotations

from datetime import date
from fastapi import HTTPException

from edugrade.services.neo4j_graph import Neo4jGraphService
from edugrade.repository.mongo.institution import InstitutionRepository
from edugrade.utils.object_id import is_objectid_hex

import asyncio
async def _neo(callable_, *args, **kwargs):
    return await asyncio.to_thread(callable_, *args, **kwargs)

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

    # 1) Enrollments (STUDIES_AT)
    enrollments = await _neo(self.neo.get_student_enrollments, student_id)
    print(enrollments)

    if not enrollments:
      # Si no hay enrollments, no hay historial de instituciones/años
      return {"years": []}

    # 2) Subjects (TOOK) con intervalos por materia
    # Debe devolver: subjectId, subjectName, institutionMongoId, subjectStartDate, subjectEndDate, grade
    subjects = await _neo(self.neo.get_student_subject_rows, student_id)

    # 3) Nombres de instituciones (Mongo)
    inst_ids = sorted({e["institutionMongoId"] for e in enrollments})
    inst_docs = []
    for iid in inst_ids:
      inst_docs.append(await self.inst_repo.get_one(iid))

    inst_name_by_id = {
      iid: d.get("name")
      for iid, d in zip(inst_ids, inst_docs)
      if d and d.get("name")
    }

    # 4) Enrollments separados por (institutionMongoId, enrollmentId)
    enrollment_by_key: dict[tuple[str, str], tuple[date, date | None]] = {}

    for e in enrollments:
      iid = e["institutionMongoId"]
      eid = e["enrollmentId"]

      try:
        inst_from = date.fromisoformat(e["institutionStartDate"])
      except Exception:
        raise HTTPException(status_code=500, detail="Neo4j data error: invalid institutionStartDate")

      inst_to = None
      if e.get("institutionEndDate"):
        try:
          inst_to = date.fromisoformat(e["institutionEndDate"])
        except Exception:
          raise HTTPException(status_code=500, detail="Neo4j data error: invalid institutionEndDate")

      enrollment_by_key[(iid, eid)] = (inst_from, inst_to)

    # Rango de años basado en enrollments
    periods = [(fr, _coalesce_end(to)) for fr, to in enrollment_by_key.values()]
    min_year = min(fr.year for fr, _ in periods)
    max_year = max(to.year for _, to in periods)

    # 5) Parse subjects una sola vez
    parsed_subjects: list[dict] = []
    for s in subjects:
      if not s.get("subjectStartDate"):
        continue

      subj_inst = s.get("institutionMongoId")
      if not subj_inst:
        continue

      try:
        s_from = date.fromisoformat(s["subjectStartDate"])
      except Exception:
        raise HTTPException(status_code=500, detail="Neo4j data error: invalid subjectStartDate")

      s_to = None
      if s.get("subjectEndDate"):
        try:
          s_to = date.fromisoformat(s["subjectEndDate"])
        except Exception:
          raise HTTPException(status_code=500, detail="Neo4j data error: invalid subjectEndDate")

      parsed_subjects.append({
        "subjectId": s.get("subjectId"),
        "subjectName": s.get("subjectName"),
        "institutionMongoId": subj_inst,
        "grade": s.get("grade"),
        "from": s_from,
        "to": s_to,
      })

    # 6) Construir salida incluyendo años e instituciones aunque no haya subjects
    years_out: list[dict] = []

    for y in range(min_year, max_year + 1):
      y_from, y_to = _year_start(y), _year_end(y)
      institutions_out: list[dict] = []

      for (iid, eid), (inst_from, inst_to_opt) in enrollment_by_key.items():
        inst_to = _coalesce_end(inst_to_opt)

        # Institución existe en ese año?
        if not _intersects(inst_from, inst_to, y_from, y_to):
          continue

        subjects_out: list[dict] = []

        for ps in parsed_subjects:
          # (1) Materia pertenece a ESTA institución
          if ps["institutionMongoId"] != iid:
            continue

          s_from = ps["from"]
          s_to = _coalesce_end(ps["to"])

          # (2) Materia intersecta con el enrollment
          if not _intersects(inst_from, inst_to, s_from, s_to):
            continue

          # (3) Opción A: asignar SOLO al año del startDate del subject
          if s_from.year != y:
            continue

          subjects_out.append({
            "subjectId": ps["subjectId"],
            "name": ps["subjectName"],
            "fromDate": s_from.isoformat(),
            "toDate": ps["to"].isoformat() if ps["to"] else None,
            "grade": ps.get("grade"),
          })

        subjects_out.sort(key=lambda x: x["fromDate"])

        # ✅ CLAVE: siempre agrego la institución, aunque subjects_out sea []
        institutions_out.append({
          "institutionId": iid,
          "name": inst_name_by_id.get(iid),
          "subjects": subjects_out,
        })

      # ✅ CLAVE: siempre agrego el año, aunque institutions_out sea []
      years_out.append({
        "year": y,
        "institutions": institutions_out,
      })

    return {"years": years_out}