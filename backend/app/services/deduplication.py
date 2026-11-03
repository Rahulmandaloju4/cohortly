"""Two-Tier Event Deduplication Service.
Exact duplicates sharing an idempotency key are automatically excluded from engagement analytics.
Potential near-duplicates (within 5.0s tolerance window) are flagged for human investigation
and are NOT automatically excluded from engagement analytics unless explicitly confirmed.
"""

from typing import Dict, Any, List
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.app.core.config import settings


def analyze_deduplication(db: Session) -> Dict[str, Any]:
    """Analyzes raw events and computes deduplication metrics."""
    # 1. Raw event count
    raw_count = db.execute(text("SELECT COUNT(*) FROM activity_events")).scalar() or 0

    # 2. Exact duplicates: Count identical idempotency keys beyond the first (canonical) record
    exact_dup_query = text("""
        SELECT COUNT(*) FROM (
            SELECT idempotency_key, COUNT(*) as cnt
            FROM activity_events
            GROUP BY idempotency_key
            HAVING cnt > 1
        )
    """)
    exact_dup_groups = db.execute(exact_dup_query).scalar() or 0
    
    total_exact_duplicates_query = text("""
        SELECT SUM(cnt - 1) FROM (
            SELECT COUNT(*) as cnt
            FROM activity_events
            GROUP BY idempotency_key
            HAVING cnt > 1
        )
    """)
    total_exact_duplicates = db.execute(total_exact_duplicates_query).scalar() or 0

    # 3. Unique events by idempotency key
    unique_event_count = raw_count - total_exact_duplicates

    # 4. Potential Near-Duplicates (same session, content, event type, learner within tolerance window)
    near_dup_query = text(f"""
        SELECT COUNT(*) FROM (
            SELECT e1.event_id
            FROM activity_events e1
            JOIN activity_events e2 ON e1.learner_id = e2.learner_id
                AND e1.course_id = e2.course_id
                AND COALESCE(e1.content_id, '') = COALESCE(e2.content_id, '')
                AND e1.event_type = e2.event_type
                AND e1.session_id = e2.session_id
                AND e1.event_id < e2.event_id
                AND ABS(strftime('%s', e1.event_timestamp_utc) - strftime('%s', e2.event_timestamp_utc)) <= {settings.NEAR_DUPLICATE_WINDOW_SECONDS}
                AND e1.idempotency_key != e2.idempotency_key
        )
    """)
    potential_near_duplicates = db.execute(near_dup_query).scalar() or 0

    # 5. Engagement events (deduplicated for analytics)
    # Excludes exact duplicates (takes MIN(rowid) per idempotency_key)
    # Retains near-duplicates as valid engagement per policy
    engagement_types = (
        'COURSE_OPENED', 'CONTENT_VIEWED', 'VIDEO_PROGRESS',
        'VIDEO_COMPLETED', 'DOCUMENT_DOWNLOADED', 'QUIZ_SUBMITTED', 'COURSE_COMPLETED'
    )
    engagement_types_str = "','".join(engagement_types)

    valid_engagement_query = text(f"""
        SELECT COUNT(DISTINCT idempotency_key)
        FROM activity_events
        WHERE event_type IN ('{engagement_types_str}')
          AND enrollment_id IS NOT NULL
    """)
    deduplicated_engagement_count = db.execute(valid_engagement_query).scalar() or 0

    return {
        "raw_event_count": raw_count,
        "exact_duplicate_groups": exact_dup_groups,
        "exact_duplicate_count": total_exact_duplicates,
        "potential_near_duplicate_count": potential_near_duplicates,
        "unique_event_count": unique_event_count,
        "deduplicated_engagement_count": deduplicated_engagement_count,
        "policy": {
            "exact_duplicates": "Automatically excluded from analytics denominators and numerators.",
            "near_duplicates": "Flagged for investigator triage; retained in engagement metrics until manually reviewed.",
        }
    }
