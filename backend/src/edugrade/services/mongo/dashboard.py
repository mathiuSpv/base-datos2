from __future__ import annotations

from datetime import date
from fastapi import HTTPException

from edugrade.repository.mongo.grade import GradeRepository
from edugrade.services.mongo.conversion_rules import ConversionRulesService
from edugrade.utils.date import date_to_datetime_utc
from edugrade.utils.object_id import is_objectid_hex
from edugrade.utils.string import non_empty_str
from edugrade.services.neo4j_graph import Neo4jGraphService

class DashboardService:
  def __init__(self, db, audit_logger, neo4j_service: Neo4jGraphService):
    self.repo = GradeRepository(db)
    self.conv = ConversionRulesService(db)
    self.audit_logger = audit_logger
    self.neo = neo4j_service

  def _norm_country(self, country: str) -> str:
    try:
      c = non_empty_str(country, "country").upper()
    except ValueError as e:
      raise HTTPException(status_code=400, detail=str(e))
    if len(c) != 3:
      raise HTTPException(status_code=400, detail="country must be ISO-3 (3 letters)")
    return c

  def _norm_institution(self, institution_id: str | None, *, required: bool) -> str | None:
    if institution_id is None:
      if required:
        raise HTTPException(status_code=400, detail="institutionId is required")
      return None

    try:
      inst = non_empty_str(institution_id, "institutionId")
    except ValueError as e:
      raise HTTPException(status_code=400, detail=str(e))

    if not is_objectid_hex(inst):
      raise HTTPException(status_code=400, detail="Invalid institutionId")

    return inst

  async def _project_avg(
    self,
    *,
    avg_za: float,
    target_system: str | None,
    country: str,
  ) -> tuple[str | None, str | None]:
    # Default: ZA
    if target_system is None or target_system == "ZA":
      return (str(avg_za), "ZA")

    try:
      ts = non_empty_str(target_system, "targetSystem")
    except ValueError as e:
      raise HTTPException(status_code=400, detail=str(e))

    when = date_to_datetime_utc(date.today())

    # convert_from_za debe soportar valores no exactos (nearest-key)
    projected = await self.conv.convert_from_za(
      value_za=str(avg_za),
      to_system=ts,
      country=country,
      grade="0",   # placeholder; si luego agregan grade/conversionRule selector, reemplazar acá
      when=when,
    )
    return (projected, ts)

  async def get_average(self, *, country: str, institution_id: str | None, target_system: str | None) -> dict:
    c = self._norm_country(country)
    inst = self._norm_institution(institution_id, required=False)

    stats = await self.repo.dashboard_summary(country=c, institution_id=inst)
    exams_read = int(stats.get("examsRead") or 0)
    exams_used = int(stats.get("examsUsedInAverage") or 0)
    avg_za = stats.get("averageZA")

    if exams_used == 0 or avg_za is None:
      return {
        "country": c,
        "institutionId": inst,
        "examsRead": exams_read,
        "examsUsedInAverage": exams_used,
        "averageZA": None,
        "displayValue": None,
        "displaySystem": None,
      }

    display_value, display_system = await self._project_avg(avg_za=float(avg_za), target_system=target_system, country=c)

    return {
      "country": c,
      "institutionId": inst,
      "examsRead": exams_read,
      "examsUsedInAverage": exams_used,
      "averageZA": float(avg_za),
      "displayValue": display_value,
      "displaySystem": display_system,
    }

  async def get_average_by_subject(self, *, country: str, institution_id: str, target_system: str | None) -> dict:
    c = self._norm_country(country)
    inst = self._norm_institution(institution_id, required=True)

    rows = await self.repo.dashboard_subjects(country=c, institution_id=inst)

    # --- lookup de nombres en neo4j (batch) ---
    subject_ids = [r.get("subjectId") for r in rows if r.get("subjectId")]
    neo_rows = self.neo.get_subjects_by_ids(subject_ids)
    name_by_id = {r["id"]: r.get("name") for r in neo_rows}

    subjects_out: list[dict] = []
    for r in rows:
      subject_id = r.get("subjectId")
      subject_name = name_by_id.get(subject_id)

      exams_read = int(r.get("examsRead") or 0)
      exams_used = int(r.get("examsUsedInAverage") or 0)
      avg_za = r.get("averageZA")

      if exams_used == 0 or avg_za is None:
        subjects_out.append(
          {
            "subjectId": subject_id,
            "subjectName": subject_name,
            "examsRead": exams_read,
            "examsUsedInAverage": exams_used,
            "averageZA": None,
            "displayValue": None,
            "displaySystem": None,
          }
        )
        continue

      display_value, display_system = await self._project_avg(avg_za=float(avg_za), target_system=target_system, country=c)

      subjects_out.append(
        {
          "subjectId": subject_id,
          "subjectName": subject_name,
          "examsRead": exams_read,
          "examsUsedInAverage": exams_used,
          "averageZA": float(avg_za),
          "displayValue": display_value,
          "displaySystem": display_system,
        }
      )

    return {"country": c, "institutionId": inst, "subjects": subjects_out}