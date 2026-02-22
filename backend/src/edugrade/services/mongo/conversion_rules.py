from datetime import datetime, timezone, date as date_type, timedelta
from fastapi import HTTPException

from edugrade.repository.mongo.conversion_rule import ConversionRuleRepository
from edugrade.repository.mongo.options import OptionsRepository
from edugrade.audit.context import AuditContext
from edugrade.utils.string import normalize_value_key

class ConversionRulesService:
  def __init__(self, db, audit_logger):
    self.rules = ConversionRuleRepository(db)
    self.options = OptionsRepository(db)
    self.audit_logger = audit_logger

  @staticmethod
  def _invert_map(m: dict[str, str]) -> dict[str, str]:
    inv: dict[str, str] = {}
    for k, v in m.items():
      if v in inv and inv[v] != k:
        raise HTTPException(
          status_code=409,
          detail=f"Ambiguous inverse map: ZA value '{v}' maps from multiple source values ('{inv[v]}' and '{k}')",
        )
      inv[v] = k
    return inv

  async def get_rule_for_date(
    self,
    *,
    system: str,
    country: str,
    grade: str,
    when: date_type,
  ) -> dict:
    rule = await self.rules.get_for_date(
      system=system,
      country=country,
      grade=grade,
      when=when,
    )
    if not rule:
      raise HTTPException(status_code=404, detail="No conversion rule found for the given parameters/date")
    return rule

  async def convert_to_za(
    self,
    *,
    value: str,
    system: str,
    country: str,
    grade: str,
    when: date_type,
  ) -> str:
    rule = await self.get_rule_for_date(
      system=system,
      country=country,
      grade=grade,
      when=when,
    )

    key = normalize_value_key(value)
    mapping: dict[str, str] = rule.get("map", {})
    if key not in mapping:
      raise HTTPException(status_code=422, detail=f"Value '{key}' not convertible for this rule")
    return mapping[key]

  async def convert_from_za(
    self,
    *,
    values_za: list[str],
    to_system: str,
    country: str,
    grade: str,
    when: date_type,
  ) -> list[str]:
    rule = await self.get_rule_for_date(
      system=to_system,
      country=country,
      grade=grade,
      when=when,
    )

    inv = self._invert_map(rule.get("map", {}))

    out: list[str] = []
    for v in values_za:
      key = normalize_value_key(v)
      if key not in inv:
        raise HTTPException(status_code=422, detail=f"ZA value '{key}' not convertible to system '{to_system}'")
      out.append(inv[key])

    return out

  async def create_new_converter(
    self,
    *,
    system: str,
    country: str,
    grade: str,
    valid_from: date_type,
    mapping: dict[str, str],
  ) -> dict:
    if not mapping:
      raise HTTPException(status_code=400, detail="map cannot be empty")

    current = await self.rules.get_current(
      system=system,
      country=country,
      grade=grade,
    )

    if current:
      cur_from = current.get("validFrom")
      if cur_from and valid_from <= cur_from:
        raise HTTPException(
          status_code=409,
          detail="validFrom must be greater than current rule validFrom for the same fromSystem/country/grade",
        )
        
      close_to = valid_from - timedelta(days=1)
      if close_to < cur_from:
        raise HTTPException(status_code=409, detail="validFrom too close; would create invalid validTo range")

      await self.rules.close_valid_to(
        system=system,
        country=country,
        grade=grade,
        valid_to=close_to,
      )

    doc = {
      "system": system,
      "country": country,
      "grade": grade,
      "validFrom": valid_from,
      "validTo": None,
      "map": mapping,
      "createdAt": datetime.now(timezone.utc),
    }
    return await self.rules.create(doc)

  async def close_current_valid_to(
    self,
    *,
    system: str,
    country: str,
    grade: str,
    valid_to: date_type,
  ) -> dict:

    updated = await self.rules.close_valid_to(
      system=system,
      country=country,
      grade=grade,
      valid_to=valid_to,
    )
    
    if not updated:
      raise HTTPException(status_code=404, detail="No current rule to close")
    return updated