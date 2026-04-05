from datetime import datetime, timezone


def parse_timestamp(raw: str) -> datetime:
    """Parse ISO 8601 string and convert to UTC."""
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    else:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt
