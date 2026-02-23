from __future__ import annotations

from datetime import datetime, timezone, timedelta
from fastapi import HTTPException

from edugrade.repository.mongo.conversion_rule import ConversionRuleRepository
from edugrade.repository.mongo.options import OptionsRepository
from edugrade.utils.string import normalize_value_key


DIR_TO_ZA = "TO_ZA"
DIR_FROM_ZA = "FROM_ZA"


class ConversionRulesService:
  def __init__(self, db):
    self.rules = ConversionRuleRepository(db)
    self.options = OptionsRepository(db)

  async def get_rule_for_date(
    self,
    *,
    direction: str,
    system: str,
    country: str | None,
    grade: str,
    when: datetime,
  ) -> dict:
    rule = await self.rules.get_for_date(
      direction=direction,
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
    country: str | None,
    grade: str,
    when: datetime,
  ) -> str:
    rule = await self.get_rule_for_date(
      direction=DIR_TO_ZA,
      system=system,
      country=country,
      grade=grade,
      when=when,
    )

    key = normalize_value_key(value)
    mapping: dict[str, str] = rule.get("map", {})
    if key not in mapping:
      raise HTTPException(status_code=422, detail=f"Value '{key}' not convertible for this rule")
    return str(mapping[key])

  async def convert_from_za(
    self,
    *,
    value_za: str,
    to_system: str,
    country: str | None,
    grade: str,
    when: datetime,
  ) -> str:
    rule = await self.get_rule_for_date(
      direction=DIR_FROM_ZA,
      system=to_system,
      country=country,
      grade=grade,
      when=when,
    )

    mapping: dict[str, str] = rule.get("map", {})
    if not mapping:
      raise HTTPException(status_code=422, detail=f"No conversion mapping found for system '{to_system}'")

    # Normaliza "6,5" -> "6.5", trims, etc (según tu impl)
    key = normalize_value_key(value_za)

    # 1) Match exacto: comportamiento actual
    if key in mapping:
      return str(mapping[key])

    # 2) Si no hay match exacto, cuantizamos a la key más cercana (para promedios tipo 6.48)
    try:
      value_float = float(key)
    except ValueError:
      raise HTTPException(
        status_code=422,
        detail=f"ZA value '{key}' not convertible to system '{to_system}'",
      )

    nearest = self._nearest_key(value_float, list(mapping.keys()), prefer="lower")
    if nearest is None or nearest not in mapping:
      raise HTTPException(
        status_code=422,
        detail=f"ZA value '{key}' not convertible to system '{to_system}'",
      )
    return str(mapping[nearest])

  async def create_new_converter(
    self,
    *,
    direction: str,
    system: str,
    country: str | None,
    grade: dict,
    valid_from: datetime,
    mapping: dict[str, str],
  ) -> dict:
    if direction not in (DIR_TO_ZA, DIR_FROM_ZA):
      raise HTTPException(status_code=400, detail="Invalid direction")
    if not mapping:
      raise HTTPException(status_code=400, detail="map cannot be empty")

    # Tomamos un "grade" representativo para buscar current: usamos el min del rango.
    grade_min = str((grade or {}).get("min") or "0")

    current = await self.rules.get_current(
      direction=direction,
      system=system,
      country=country,
      grade=grade_min,
    )

    if current:
      cur_from = current.get("validFrom")
      if cur_from and valid_from <= cur_from:
        raise HTTPException(status_code=409, detail="validFrom must be greater than current rule validFrom")

      close_to = valid_from - timedelta(days=1)
      if cur_from and close_to < cur_from:
        raise HTTPException(status_code=409, detail="validFrom too close; would create invalid validTo range")

      await self.rules.close_valid_to(
        direction=direction,
        system=system,
        country=country,
        grade=grade_min,
        valid_to=close_to,
      )

    doc = {
      "direction": direction,
      "system": system,
      "country": country if country is not None else "ANY",
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
    direction: str,
    system: str,
    country: str | None,
    grade_min: str,
    valid_to: datetime,
  ) -> dict:
    updated = await self.rules.close_valid_to(
      direction=direction,
      system=system,
      country=country,
      grade=grade_min,
      valid_to=valid_to,
    )
    if not updated:
      raise HTTPException(status_code=404, detail="No current rule to close")
    return updated
  
  def _nearest_key(
    self,
    value: float,
    keys: list[str],
    prefer: str = "lower",
  ) -> str:
    nums = sorted(float(k) for k in keys)
    best = nums[0]
    best_dist = abs(value - best)

    for x in nums[1:]:
      d = abs(value - x)
      if d < best_dist:
        best, best_dist = x, d
      elif d == best_dist:
        if prefer == "lower":
          best = min(best, x)
        else:
          best = max(best, x)

    # devolver exactamente la key existente (string)
    best_str = min(keys, key=lambda k: abs(float(k) - best))
    return best_str