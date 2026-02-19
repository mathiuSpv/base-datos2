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
