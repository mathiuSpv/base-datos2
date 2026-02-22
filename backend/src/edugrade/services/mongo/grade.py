from __future__ import annotations

from datetime import datetime, timezone, date as date_type
from collections import defaultdict
from typing import Any

from bson import ObjectId
from fastapi import HTTPException

from edugrade.audit.context import AuditContext
from edugrade.audit.exec import audited
from edugrade.repository.mongo.grade import GradeRepository
from edugrade.services.mongo.conversion_rules import ConversionRulesService
from edugrade.utils.date import date_to_datetime_utc, ensure_date, ensure_date_range
from edugrade.utils.object_id import is_objectid_hex
from edugrade.utils.string import non_empty_str


class GradeService:
  def __init__(self, db, audit_logger):
    self.repo = GradeRepository(db)
    self.conv = ConversionRulesService(db)
    self.audit_logger = audit_logger

  async def create(self, payload: dict, audit: AuditContext) -> dict:
    async def _do() -> dict:
      # Validaciones de IDs
      for k in ("subjectId", "studentId", "institutionId"):
        v = payload.get(k)
        if not (isinstance(v, str) and is_objectid_hex(v)):
          raise HTTPException(status_code=400, detail=f"Invalid {k}")

      # Validaciones de strings / date
      try:
        system = non_empty_str(payload.get("system"), "system")
        country = non_empty_str(payload.get("country"), "country")
        grade = non_empty_str(payload.get("grade"), "grade")
        value = non_empty_str(payload.get("value"), "value")
        when = date_to_datetime_utc(ensure_date(payload.get("date"), "date"))
      except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

      # Conversión a ZA (puede lanzar 404/422/etc => audited lo registra como ERROR)
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

    return await audited(
      audit_logger=self.audit_logger,
      audit=audit,
      operation="CREATE",
      db="mongo",
      entity_type="Grade",
      entity_id="(pending)",
      payload_summary=(
        "grade create; "
        f"system={payload.get('system')} country={payload.get('country')} grade={payload.get('grade')}"
      ),
      fn=_do,
      entity_id_from_result=lambda doc: str(doc.get("_id") or doc.get("id") or "(missing)"),
    )

  async def delete(self, grade_id: str, audit: AuditContext) -> None:
    if not ObjectId.is_valid(grade_id):
      raise HTTPException(status_code=400, detail="Invalid id")

    async def _do() -> None:
      ok = await self.repo.delete(ObjectId(grade_id))
      if not ok:
        raise HTTPException(status_code=404, detail="Grade not found")
      return None

    await audited(
      audit_logger=self.audit_logger,
      audit=audit,
      operation="DELETE",
      db="mongo",
      entity_type="Grade",
      entity_id=grade_id,
      payload_summary="grade delete",
      fn=_do,
    )

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
    if not (is_objectid_hex(subject_id) and is_objectid_hex(student_id) and is_objectid_hex(institution_id)):
      raise HTTPException(status_code=400, detail="Invalid subjectId/studentId/institutionId")

    try:
      ensure_date_range(date_from, date_to)
    except ValueError as e:
      raise HTTPException(status_code=400, detail=str(e))

    return await self.repo.list_by_period(
      subject_id=subject_id,
      student_id=student_id,
      institution_id=institution_id,
      date_from=date_from,
      date_to=date_to,
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
      # OJO: en tu código pegado aparece "from_system" pero tu ConversionRulesService
      # que mostraste usa "system=" en get_rule_for_date. Acá uso "system=".
      rule = await self.conv.get_rule_for_date(
        system=ts,
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