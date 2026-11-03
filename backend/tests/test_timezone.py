"""Unit tests for timezone conversion, anomaly detection, and weekly boundary assignments."""
import pytest
from datetime import datetime, date
from backend.app.utils.time_utils import derive_local_date_from_utc, is_timezone_date_consistent


def test_valid_timezone_conversion():
    """Verify correct conversion to local date across IANA zones."""
    # Noon UTC on Sept 15
    utc_dt = datetime(2026, 9, 15, 12, 0, 0)
    
    # New York (UTC-4 in daylight saving)
    ny_date = derive_local_date_from_utc(utc_dt, "America/New_York")
    assert ny_date == date(2026, 9, 15)

    # Tokyo (UTC+9)
    tokyo_date = derive_local_date_from_utc(utc_dt, "Asia/Tokyo")
    assert tokyo_date == date(2026, 9, 15)


def test_legitimate_utc_local_date_differences_around_midnight():
    """Verify that events near midnight naturally produce different calendar dates without anomaly."""
    # 23:30 UTC on Sept 15
    late_utc = datetime(2026, 9, 15, 23, 30, 0)

    # Tokyo (UTC+9) is 08:30 on Sept 16!
    tokyo_date = derive_local_date_from_utc(late_utc, "Asia/Tokyo")
    assert tokyo_date == date(2026, 9, 16)
    assert tokyo_date != late_utc.date()  # Legitimate date difference!
    
    # is_timezone_date_consistent must return True because 2026-09-16 is the correct local date!
    assert is_timezone_date_consistent(late_utc, "Asia/Tokyo", date(2026, 9, 16)) is True


def test_incorrect_stored_local_date_detection():
    """Verify that an anomaly is flagged ONLY when stored date differs from derived date."""
    late_utc = datetime(2026, 9, 15, 23, 30, 0)
    
    # If the database stored 2026-09-15 for Tokyo (which was actually 2026-09-16), that is an anomaly!
    assert is_timezone_date_consistent(late_utc, "Asia/Tokyo", date(2026, 9, 15)) is False


def test_weekly_reporting_boundaries():
    """Verify weekly boundary handling around midnight (Monday vs Sunday)."""
    # Sunday 23:59:00 UTC (Sept 20, 2026) -> Falls in ISO Week 38
    sunday_utc = datetime(2026, 9, 20, 23, 59, 0)
    iso_week_utc = sunday_utc.isocalendar()[1]
    assert iso_week_utc == 38

    # Local Tokyo time is Monday morning (Sept 21, 2026) -> ISO Week 39
    tokyo_date = derive_local_date_from_utc(sunday_utc, "Asia/Tokyo")
    iso_week_tokyo = tokyo_date.isocalendar()[1]
    assert iso_week_tokyo == 39

    # Cohortly normalizes to UTC reporting week, but captures the boundary shift for regional reconciliation
    assert iso_week_utc != iso_week_tokyo
