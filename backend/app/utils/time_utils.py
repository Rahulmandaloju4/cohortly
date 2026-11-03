"""Timezone conversion and deterministic date derivation utilities."""
from datetime import datetime, date
from zoneinfo import ZoneInfo
from typing import Tuple


def derive_local_date_from_utc(dt_utc: datetime, tz_name: str) -> date:
    """Converts a UTC datetime to local date in the given IANA timezone."""
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("UTC")
    
    # Ensure dt_utc is timezone-aware in UTC
    if dt_utc.tzinfo is None:
        dt_aware = dt_utc.replace(tzinfo=ZoneInfo("UTC"))
    else:
        dt_aware = dt_utc.astimezone(ZoneInfo("UTC"))
        
    local_dt = dt_aware.astimezone(tz)
    return local_dt.date()


def is_timezone_date_consistent(dt_utc: datetime, tz_name: str, stored_date: date) -> bool:
    """Returns True if stored_date matches the correctly derived local date for dt_utc in tz_name."""
    derived = derive_local_date_from_utc(dt_utc, tz_name)
    return derived == stored_date
