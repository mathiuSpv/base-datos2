import math

def non_empty_str(s: str | None, field_name: str = "Value") -> str:
  if s is None:
    raise ValueError(f"{field_name} must be a non-empty string")
  s2 = s.strip()
  if not s2:
    raise ValueError(f"{field_name} must be a non-empty string")
  return s2

def round_half_up(value_str: str) -> int:
  try:
    number = float(value_str.strip())
  except (ValueError, AttributeError):
    raise ValueError("Must be a valid numeric string")

  return math.floor(number + 0.5) if number >= 0 else math.ceil(number - 0.5)

def normalize_value_key(v: str) -> str:
  return str(v).strip()