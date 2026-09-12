from datetime import UTC, datetime


def as_utc(value: datetime) -> datetime:
    """SQLite returns our UTC columns without tzinfo; keep the original instant."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
