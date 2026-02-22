from __future__ import annotations

from datetime import datetime, timezone, date as date_type
from collections import defaultdict
from bson import ObjectId
from fastapi import HTTPException

from edugrade.repository.mongo.grade import GradeRepository
from edugrade.services.mongo.conversion_rules import ConversionRulesService

from edugrade.utils.object_id import is_objectid_hex, is_uuid
from edugrade.utils.string import non_empty_str
from edugrade.utils.date import date_to_datetime_utc, ensure_date, ensure_date_range


class GradeService:

  def __init__(self, db):
    self.repo = GradeRepository(db)
    self.conv = ConversionRulesService(db)

  async def create(self, payload: dict) -> dict:
    subject_id = payload.get("subjectId")
    if not (isinstance(subject_id, str) and is_uuid(subject_id)):
      raise HTTPException(status_code=400, detail=f"Invalid subjectId")
    for k in ("studentId", "institutionId"):
      v = payload.get(k)
      if not (isinstance(v, str) and is_objectid_hex(v)):
        raise HTTPException(status_code=400, detail=f"Invalid {k}")

    try:
      system = non_empty_str(payload.get("system"), "system")
      country = non_empty_str(payload.get("country"), "country")
      grade = non_empty_str(payload.get("grade"), "grade")
      value = non_empty_str(payload.get("value"), "value")
      when = date_to_datetime_utc(ensure_date(payload.get("date"), "date"))
      
    except ValueError as e:
      raise HTTPException(status_code=400, detail=str(e))

    value_converted_za = await self.conv.convert_to_za(
      value=value,
      system=system,
      country=country,
      grade=grade,
      when=when,
    )

    doc = dict(payload)
    doc["date"] = when
    doc["valueConverted"] = value_converted_za
    doc["createdAt"] = datetime.now(timezone.utc)

    return await self.repo.create(doc)

  async def get(self, grade_id: str) -> dict:
    if not ObjectId.is_valid(grade_id):
      raise HTTPException(status_code=400, detail="Invalid id")

    doc = await self.repo.get_by_id(ObjectId(grade_id))
    if not doc:
      raise HTTPException(status_code=404, detail="Grade not found")
    return doc

  async def list_by_period(
    self,
    subject_id: str,
    student_id: str,
    institution_id: str,
    date_from: date_type,
    date_to: date_type,
    limit: int,
    skip: int,
  ) -> list[dict]:
    if not (is_uuid(subject_id) and is_objectid_hex(student_id) and is_objectid_hex(institution_id)):
      raise HTTPException(status_code=400, detail="Invalid subjectId/studentId/institutionId")

    try:
      ensure_date_range(date_from, date_to)
    except ValueError as e:
      raise HTTPException(status_code=400, detail=str(e))

    return await self.repo.list_by_period(
      subject_id=subject_id,
      student_id=student_id,
      institution_id=institution_id,
      date_from=date_to_datetime_utc(date_from),
      date_to=date_to_datetime_utc(date_to),
      limit=limit,
      skip=skip,
    )

  async def get_projected(self, grade_id: str, target_system: str | None) -> dict:
    doc = await self.get(grade_id)
    return await self._project_one(doc, target_system)

  async def list_projected(
    self,
    subject_id: str,
    student_id: str,
    institution_id: str,
    date_from: date_type,
    date_to: date_type,
    limit: int,
    skip: int,
    target_system: str | None,
  ) -> list[dict]:
    docs = await self.list_by_period(subject_id, student_id, institution_id, date_from, date_to, limit, skip)
    return await self._project_many(docs, target_system)

  def _inject_display(self, doc: dict, display_value: str, display_system: str) -> dict:
    out = dict(doc)
    out["displayValue"] = display_value
    out["displaySystem"] = display_system
    return out

  async def _project_one(self, doc: dict, target_system: str | None) -> dict:
    projected = await self._project_many([doc], target_system)
    return projected[0]

  async def _project_many(self, docs: list[dict], target_system: str | None) -> list[dict]:
    if target_system is None:
      out: list[dict] = []
      for d in docs:
        out.append(self._inject_display(d, d.get("value"), d.get("system")))
      return out

    try:
      ts = non_empty_str(target_system, "targetSystem")
    except ValueError as e:
      raise HTTPException(status_code=400, detail=str(e))

    if ts == "ZA":
      out: list[dict] = []
      for d in docs:
        vza = d.get("valueConverted")
        if vza is None:
          raise HTTPException(status_code=500, detail="Grade missing valueConverted (ZA)")
        out.append(self._inject_display(d, str(vza), "ZA"))
      return out

    groups: dict[tuple[str, str, date_type], list[int]] = defaultdict(list)

    for idx, d in enumerate(docs):
      try:
        country = non_empty_str(d.get("country"), "country")
        grade = non_empty_str(d.get("grade"), "grade")
        when = ensure_date(d.get("date"), "date")
      except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

      groups[(country, grade, when)].append(idx)

    projected_values: list[str | None] = [None] * len(docs)

    for (country, grade, when), idxs in groups.items():
      rule = await self.conv.get_rule_for_date(
        from_system=ts,
        country=country,
        grade=grade,
        when=when,
      )
      mapping: dict[str, str] = rule["map"]

      for i in idxs:
        vza = docs[i].get("valueConverted")
        if vza is None:
          raise HTTPException(status_code=500, detail="Grade missing valueConverted (ZA)")

        projected_values[i] = self._inverse_lookup_no_invert(mapping, str(vza), ts)

    out: list[dict] = []
    for i, d in enumerate(docs):
      out.append(self._inject_display(d, projected_values[i], ts))  # type: ignore[arg-type]
    return out

  def _inverse_lookup_no_invert(self, mapping: dict[str, str], value_za: str, target_system: str) -> str:
    matches = [k for k, v in mapping.items() if str(v) == str(value_za)]

    if not matches:
      raise HTTPException(
        status_code=422,
        detail=f"ZA value '{value_za}' not convertible to system '{target_system}'",
      )
    if len(matches) > 1:
      raise HTTPException(
        status_code=409,
        detail=f"Ambiguous inverse mapping for ZA value '{value_za}' in system '{target_system}'",
      )
    return matches[0]