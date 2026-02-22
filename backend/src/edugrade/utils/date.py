from __future__ import annotations
from datetime import datetime, date, timezone

def date_to_datetime_utc(d: date) -> datetime:
  return datetime(
    year=d.year,
    month=d.month,
    day=d.day,
    hour=0,
    minute=0,
    second=0,
    tzinfo=timezone.utc,
  )

def ensure_date(value, field_name: str) -> date:
  if value is None:
    raise ValueError(f"Missing required field: {field_name}")

  if isinstance(value, date) and not isinstance(value, datetime):
    return value

  if isinstance(value, str):
    try:
      return date.fromisoformat(value)
    except ValueError as e:
      raise ValueError(f"Invalid date format for {field_name}. Expected YYYY-MM-DD") from e

  raise ValueError(f"Invalid type for {field_name}. Expected date or ISO string")

def ensure_date_range(from_date: date, to_date: date) -> None:
  if from_date > to_date:
    raise ValueError("fromDate must be <= toDate")
