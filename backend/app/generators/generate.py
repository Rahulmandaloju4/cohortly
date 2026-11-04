"""Deterministic parameterized synthetic data generation engine for Cohortly.
Enforces fixed random seed, deterministic reference clock, strict parent-child ordering,
batch insertion with SQLite WAL mode, and post-baseline anomaly injection.
"""

import argparse
import random
import time
import os
import sqlite3
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, Any, List

from backend.app.core.config import settings
from backend.app.utils.ids import (
    make_instructor_id,
    make_learner_id,
    make_course_id,
    make_cohort_id,
    make_enrollment_id,
    make_content_id,
    make_event_id,
    make_assessment_id,
    make_attempt_id,
    make_completion_rule_id,
    make_outcome_id,
    make_history_id,
)
from backend.app.utils.crypto import compute_idempotency_key
from backend.app.utils.time_utils import derive_local_date_from_utc
from backend.app.generators.anomalies import inject_anomalies
from backend.app.services.anomaly_detector import scan_and_register_anomalies

# Curricular Domains
COURSE_CATEGORIES = [
    "AI Engineering",
    "Cloud Computing",
    "Data Science",
    "Full-Stack Web Development",
    "Cybersecurity",
    "DevOps & SRE",
    "Distributed Systems",
]

DIFFICULTY_LEVELS = ["BEGINNER", "INTERMEDIATE", "ADVANCED"]
REGIONS = ["North America", "EMEA", "APAC", "LATAM"]
LEARNING_MODES = ["SELF_PACED", "COHORT_BASED", "BLENDED"]
DEVICE_TYPES = ["DESKTOP", "MOBILE", "TABLET"]
TIMEZONES = ["America/New_York", "Europe/London", "Asia/Tokyo", "Australia/Sydney", "America/Los_Angeles", "UTC"]

EVENT_TYPES_PROGRESSION = [
    "COURSE_OPENED",
    "CONTENT_VIEWED",
    "VIDEO_STARTED",
    "VIDEO_PROGRESS",
    "VIDEO_COMPLETED",
    "DOCUMENT_DOWNLOADED",
    "QUIZ_STARTED",
    "QUIZ_SUBMITTED",
]


class DeterministicClock:
    """Provides stable datetime generation relative to a fixed anchor date."""

    def __init__(self, anchor_iso: str = settings.REFERENCE_ANCHOR_DATE):
        self.anchor = datetime.fromisoformat(anchor_iso.replace("Z", "+00:00"))

    def date_offset(self, days: int) -> date:
        return (self.anchor + timedelta(days=days)).date()

    def datetime_offset(self, days: int, seconds: int = 0) -> datetime:
        return (self.anchor + timedelta(days=days, seconds=seconds)).replace(tzinfo=None)


def generate_dataset(
    profile: str = "starter",
    seed: int = settings.DEFAULT_SEED,
    num_learners: int = None,
    num_courses: int = None,
    num_enrollments: int = None,
    num_events: int = None,
    db_path: str = "data/generated/cohortly.db",
    ground_truth_path: str = "data/ground_truth/anomalies.json",
    quiet: bool = False,
) -> Dict[str, Any]:
    """Generates the synthetic dataset deterministically and persists via batch insertions."""
    start_time = time.time()
    
    # 1. Resolve scale
    if profile == "starter":
        n_learners = num_learners or settings.STARTER_LEARNERS
        n_instructors = settings.STARTER_INSTRUCTORS
        n_courses = num_courses or settings.STARTER_COURSES
        n_cohorts = settings.STARTER_COHORTS
        n_enrollments = num_enrollments or settings.STARTER_ENROLLMENTS
        n_events = num_events or settings.STARTER_EVENTS
    else:  # full
        n_learners = num_learners or settings.FULL_LEARNERS
        n_instructors = settings.FULL_INSTRUCTORS
        n_courses = num_courses or settings.FULL_COURSES
        n_cohorts = settings.FULL_COHORTS
        n_enrollments = num_enrollments or settings.FULL_ENROLLMENTS
        n_events = num_events or settings.FULL_EVENTS

    # 2. Initialize deterministic PRNGs
    rng = random.Random(seed)
    clock = DeterministicClock()

    if not quiet:
        print(f"=== Starting Cohortly Deterministic Data Generation ===")
        print(f"Profile: {profile.upper()} | Seed: {seed} | Database: {db_path}")
        print(f"Targets: {n_learners} Learners, {n_courses} Courses, {n_enrollments} Enrollments, {n_events} Events")

    # Ensure output directories exist
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    os.makedirs("data/ground_truth", exist_ok=True)
    os.makedirs("data/manifests", exist_ok=True)

    # 3. Connect to SQLite and create schema if not existing
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = OFF;")  # Disable temporarily for rapid bulk truncate/load
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA cache_size = -64000;")
    conn.execute("PRAGMA temp_store = MEMORY;")

    cursor = conn.cursor()

    # Drop existing tables to ensure exact deterministic rebuild
    table_names = [
        "state_history", "exceptions", "course_outcomes", "attempts", "assessments",
        "completion_rules", "activity_events", "content_items", "enrollments",
        "cohorts", "courses", "learners", "instructors"
    ]
    for tbl in table_names:
        cursor.execute(f"DROP TABLE IF EXISTS {tbl};")

    # Read and apply DDL schema
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import backend.app.models  # Ensures all 13 declarative models are registered on Base.metadata
    from backend.app.core.database import Base
    
    target_engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(target_engine)

    # ---------------------------------------------------------
    # STEP 1: Instructors
    # ---------------------------------------------------------
    instructors_data = []
    first_names = ["Elena", "Marcus", "Sofia", "Aiden", "Devin", "Priya", "Carlos", "Yuki", "Lars", "Fatima"]
    last_names = ["Rostova", "Vance", "Moretti", "Kowalski", "Patel", "Tanaka", "Chen", "Novak", "O'Connor", "Diallo"]
    
    for i in range(1, n_instructors + 1):
        ins_id = make_instructor_id(i)
        fn = rng.choice(first_names)
        ln = rng.choice(last_names)
        email = f"{fn.lower()}.{ln.lower()}.{i}@cohortly.internal"
        dept = rng.choice(COURSE_CATEGORIES)
        created_at = clock.datetime_offset(days=-90, seconds=i * 60)
        instructors_data.append((ins_id, fn, ln, email, dept, created_at.isoformat()))

    cursor.executemany(
        "INSERT INTO instructors (instructor_id, first_name, last_name, email, department, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        instructors_data,
    )
    conn.commit()
    if not quiet:
        print(f"[OK] Generated {len(instructors_data)} Instructors")

    # ---------------------------------------------------------
    # STEP 2: Learners
    # ---------------------------------------------------------
    learners_data = []
    # Status distribution: 85% Active, 12% Inactive, 3% Suspended
    status_choices = ["ACTIVE"] * 85 + ["INACTIVE"] * 12 + ["SUSPENDED"] * 3
    
    for i in range(1, n_learners + 1):
        lrn_id = make_learner_id(i)
        fn = rng.choice(first_names)
        ln = rng.choice(last_names)
        email = f"{fn.lower()}.{ln.lower()}.{i}@synthetic.cohortly.io"
        reg_days_ago = rng.randint(30, 180)
        reg_date = clock.date_offset(days=-reg_days_ago)
        status = rng.choice(status_choices)
        region = rng.choice(REGIONS)
        learning_mode = rng.choice(LEARNING_MODES)
        created_at = clock.datetime_offset(days=-reg_days_ago, seconds=i * 10)
        learners_data.append((lrn_id, fn, ln, email, reg_date.isoformat(), status, region, learning_mode, created_at.isoformat()))

    cursor.executemany(
        "INSERT INTO learners (learner_id, first_name, last_name, email, registration_date, learner_status, region, learning_mode, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        learners_data,
    )
    conn.commit()
    if not quiet:
        print(f"[OK] Generated {len(learners_data)} Learners")

    # ---------------------------------------------------------
    # STEP 3: Courses
    # ---------------------------------------------------------
    courses_data = []
    course_topics = [
        "Distributed Systems Architecture", "Advanced Kubernetes & Cloud Native",
        "Deep Learning Systems with PyTorch", "Production Machine Learning Pipelines",
        "Modern Full-Stack Applications with TypeScript", "Zero-Trust Security & Network Architecture",
        "High-Throughput Streaming with Apache Kafka", "Relational Database Internals & Tuning",
        "Microservices Architecture & API Gateways", "Autonomous AI Agents in Enterprise Systems",
    ]
    for i in range(1, n_courses + 1):
        crs_id = make_course_id(i)
        topic = course_topics[(i - 1) % len(course_topics)]
        crs_name = f"{topic} (Level {((i - 1) % 3) + 1})"
        category = COURSE_CATEGORIES[(i - 1) % len(COURSE_CATEGORIES)]
        diff = DIFFICULTY_LEVELS[(i - 1) % len(DIFFICULTY_LEVELS)]
        ins_id = instructors_data[(i - 1) % len(instructors_data)][0]
        status = "ACTIVE" if i <= int(n_courses * 0.9) else "ARCHIVED"
        created_at = clock.datetime_offset(days=-120, seconds=i * 100)
        courses_data.append((crs_id, crs_name, category, diff, ins_id, status, created_at.isoformat()))

    cursor.executemany(
        "INSERT INTO courses (course_id, course_name, category, difficulty_level, instructor_id, course_status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        courses_data,
    )
    conn.commit()
    if not quiet:
        print(f"[OK] Generated {len(courses_data)} Courses")

    # ---------------------------------------------------------
    # STEP 4: Cohorts
    # ---------------------------------------------------------
    cohorts_data = []
    for i in range(1, n_cohorts + 1):
        coh_id = make_cohort_id(2026, i)
        start_days = -60 + (i * 5)
        start_d = clock.date_offset(days=start_days)
        end_d = clock.date_offset(days=start_days + 90)
        coh_name = f"Cohort 2026-{i:02d} ({rng.choice(REGIONS)})"
        region = rng.choice(REGIONS)
        ptype = rng.choice(["ACCELERATED", "STANDARD", "PART_TIME"])
        created_at = clock.datetime_offset(days=start_days - 15)
        cohorts_data.append((coh_id, coh_name, start_d.isoformat(), end_d.isoformat(), region, ptype, created_at.isoformat()))

    cursor.executemany(
        "INSERT INTO cohorts (cohort_id, cohort_name, start_date, end_date, region, program_type, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        cohorts_data,
    )
    conn.commit()
    if not quiet:
        print(f"[OK] Generated {len(cohorts_data)} Cohorts")

    # ---------------------------------------------------------
    # STEP 5: Enrollments
    # ---------------------------------------------------------
    enrollments_data = []
    existing_enrs = set()
    enr_counter = 1
    
    # Ensure wide distribution across learners and courses
    learner_ids = [l[0] for l in learners_data]
    course_ids = [c[0] for c in courses_data]
    cohort_ids = [c[0] for c in cohorts_data]

    learner_reg_map = {l[0]: date.fromisoformat(l[4]) for l in learners_data}
    while len(enrollments_data) < n_enrollments:
        lid = rng.choice(learner_ids)
        cid = rng.choice(course_ids)
        if (lid, cid) in existing_enrs:
            continue
        existing_enrs.add((lid, cid))
        
        enr_id = make_enrollment_id(lid, cid)
        coh_id = rng.choice(cohort_ids)
        reg_d = learner_reg_map[lid]
        days_since_reg = max(1, (clock.anchor.date() - reg_d).days)
        offset_from_reg = rng.randint(0, min(days_since_reg, 30))
        enrolled_at = datetime.combine(reg_d + timedelta(days=offset_from_reg), datetime.min.time()) + timedelta(seconds=rng.randint(0, 86400))
        expected_comp = (enrolled_at + timedelta(days=60)).date()
        
        # Enrollment outcome distribution: 65% ACTIVE, 25% COMPLETED, 8% DROPPED, 2% PAUSED
        rand_val = rng.random()
        if rand_val < 0.25:
            status = "COMPLETED"
            comp_days = rng.randint(10, 45)
            comp_dt = min(enrolled_at + timedelta(days=comp_days), clock.anchor.replace(tzinfo=None) - timedelta(hours=1))
            completed_at = comp_dt.isoformat()
            dropped_at = None
        elif rand_val < 0.33:
            status = "DROPPED"
            drop_days = rng.randint(5, 25)
            drop_dt = min(enrolled_at + timedelta(days=drop_days), clock.anchor.replace(tzinfo=None) - timedelta(hours=1))
            completed_at = None
            dropped_at = drop_dt.isoformat()
        elif rand_val < 0.35:
            status = "PAUSED"
            completed_at = None
            dropped_at = None
        else:
            status = "ACTIVE"
            completed_at = None
            dropped_at = None

        enrollments_data.append((
            enr_id, lid, cid, coh_id, enrolled_at.isoformat(), status,
            expected_comp.isoformat(), completed_at, dropped_at
        ))
        enr_counter += 1

    cursor.executemany(
        "INSERT INTO enrollments (enrollment_id, learner_id, course_id, cohort_id, enrolled_at, enrollment_status, expected_completion_date, completed_at, dropped_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        enrollments_data,
    )
    conn.commit()
    if not quiet:
        print(f"[OK] Generated {len(enrollments_data)} Enrollments")

    # ---------------------------------------------------------
    # STEP 6: Content Items (Hierarchy: Module -> Lessons)
    # ---------------------------------------------------------
    content_items_data = []
    course_content_map = {}  # course_id -> list of content_ids
    course_required_content_map = {}  # course_id -> list of required content_ids
    
    for c in courses_data:
        cid = c[0]
        course_content_map[cid] = []
        seq = 1
        # 3 Modules per course, each having 3-4 lessons
        for m in range(1, 4):
            module_id = make_content_id(cid, seq)
            mod_title = f"Module {m}: Fundamentals & Concepts"
            c_type = "ARTICLE"
            est_dur = 20
            created_at = c[6]
            content_items_data.append((module_id, cid, None, mod_title, c_type, seq, est_dur, 0, created_at))
            seq += 1

            for l in range(1, 4):
                lesson_id = make_content_id(cid, seq)
                lesson_title = f"Lesson {m}.{l}: In-Depth Practice"
                l_type = rng.choice(["VIDEO", "VIDEO", "DOCUMENT", "QUIZ"])
                l_dur = rng.randint(15, 60)
                is_req = 1 if l < 3 else 0  # 3rd lesson optional elective
                content_items_data.append((lesson_id, cid, module_id, lesson_title, l_type, seq, l_dur, is_req, created_at))
                course_content_map[cid].append(lesson_id)
                if is_req:
                    course_required_content_map.setdefault(cid, []).append(lesson_id)
                seq += 1

    cursor.executemany(
        "INSERT INTO content_items (content_id, course_id, parent_content_id, title, content_type, sequence_number, estimated_duration_minutes, is_required, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        content_items_data,
    )
    conn.commit()
    if not quiet:
        print(f"[OK] Generated {len(content_items_data)} Hierarchical Content Items")

    # ---------------------------------------------------------
    # STEP 7: Assessments
    # ---------------------------------------------------------
    assessments_data = []
    course_assessments_map = {}  # course_id -> list of assessment_ids
    asm_counter = 1
    
    for c in courses_data:
        cid = c[0]
        course_assessments_map[cid] = []
        # 2 Required Assessments per course: 1 Midterm Quiz, 1 Final Project
        asm1_id = make_assessment_id(2026, asm_counter)
        asm_counter += 1
        due1 = clock.date_offset(days=-20)
        assessments_data.append((asm1_id, cid, "Midterm Technical Evaluation", "QUIZ", 100.00, 70.00, 1, due1.isoformat(), c[6]))
        course_assessments_map[cid].append(asm1_id)

        asm2_id = make_assessment_id(2026, asm_counter)
        asm_counter += 1
        due2 = clock.date_offset(days=10)
        assessments_data.append((asm2_id, cid, "Final Capstone Implementation", "PROJECT", 100.00, 75.00, 1, due2.isoformat(), c[6]))
        course_assessments_map[cid].append(asm2_id)

    cursor.executemany(
        "INSERT INTO assessments (assessment_id, course_id, title, assessment_type, max_score, passing_score, is_required, due_date, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        assessments_data,
    )
    conn.commit()
    if not quiet:
        print(f"[OK] Generated {len(assessments_data)} Assessments")

    # ---------------------------------------------------------
    # STEP 8: Completion Rules
    # ---------------------------------------------------------
    rules_data = []
    course_rule_map = {}
    for c in courses_data:
        cid = c[0]
        rule_id = make_completion_rule_id(cid, version=1)
        course_rule_map[cid] = rule_id
        eff_from = clock.date_offset(days=-120)
        rules_data.append((rule_id, cid, 80.00, 70.00, 1, eff_from.isoformat(), None, 1, 1))

    cursor.executemany(
        "INSERT INTO completion_rules (completion_rule_id, course_id, minimum_content_completion_percentage, minimum_assessment_score, require_all_mandatory_assessments, effective_from, effective_to, rule_version, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        rules_data,
    )
    conn.commit()
    if not quiet:
        print(f"[OK] Generated {len(rules_data)} Completion Rules")

    # ---------------------------------------------------------
    # STEP 9: Activity Events (Streaming / Chunked)
    # ---------------------------------------------------------
    events_generated_count = 0
    near_duplicate_count = 0
    evt_counter = 1
    
    # We distribute events across active and completed enrollments
    active_or_comp_enrs = [e for e in enrollments_data if e[5] in ("ACTIVE", "COMPLETED")]
    if not active_or_comp_enrs:
        active_or_comp_enrs = enrollments_data

    # Generate valid baseline events
    chunk_size = 50000
    events_inserted = 0
    batch_to_insert = []

    # Pre-generate required completion events for COMPLETED enrollments
    # so that genuine completions satisfy the content completion rule
    completed_enrs = [e for e in enrollments_data if e[5] == "COMPLETED"]
    for enr in completed_enrs:
        enr_id = enr[0]
        lid = enr[1]
        cid = enr[2]
        enr_dt = datetime.fromisoformat(enr[4])
        comp_dt = datetime.fromisoformat(enr[7]) if enr[7] else clock.anchor.replace(tzinfo=None)
        span_seconds = max(60, int((comp_dt - enr_dt).total_seconds()))
        content_items = course_required_content_map.get(cid, [])
        for idx, cont_id in enumerate(content_items):
            sec_offset = int((idx / max(1, len(content_items))) * span_seconds)
            event_utc = enr_dt + timedelta(seconds=sec_offset)
            tz = rng.choice(TIMEZONES)
            local_d = derive_local_date_from_utc(event_utc, tz)
            session_id = f"SES-{lid}-{event_utc.strftime('%Y%m%d%H')}"
            device = rng.choice(DEVICE_TYPES)
            event_type = "VIDEO_COMPLETED" if idx % 2 == 0 else "DOCUMENT_DOWNLOADED"
            ingestion_ts = event_utc + timedelta(seconds=2)
            idemp = compute_idempotency_key(lid, cid, cont_id, event_type, session_id, event_utc.isoformat() + "Z")
            evt_id = make_event_id(enr_id, evt_counter)
            evt_counter += 1
            record = (
                evt_id, enr_id, lid, cid, cont_id, event_type, event_utc.isoformat(),
                tz, local_d.isoformat(), session_id, device, "REALTIME",
                ingestion_ts.isoformat(), idemp
            )
            events_generated_count += 1
            batch_to_insert.append(record)

    while events_generated_count < n_events:
        enr = rng.choice(active_or_comp_enrs)
        enr_id = enr[0]
        lid = enr[1]
        cid = enr[2]
        
        # Pick content item from course
        content_items = course_content_map.get(cid, [])
        cont_id = rng.choice(content_items) if content_items else None
        
        event_type = rng.choice(EVENT_TYPES_PROGRESSION)
        
        # Days between enrollment and reference anchor
        enr_dt = datetime.fromisoformat(enr[4])
        days_active = max(1, (clock.anchor.replace(tzinfo=None) - enr_dt).days)
        offset_days = rng.randint(0, days_active)
        event_utc = enr_dt + timedelta(days=offset_days, seconds=rng.randint(0, 86400))
        
        tz = rng.choice(TIMEZONES)
        local_d = derive_local_date_from_utc(event_utc, tz)
        
        session_id = f"SES-{lid}-{event_utc.strftime('%Y%m%d%H')}"
        device = rng.choice(DEVICE_TYPES)
        sync_mode = rng.choice(["REALTIME", "REALTIME", "OFFLINE_SYNC", "LATE_SYNC"])
        
        # Ingestion timestamp >= event_timestamp_utc
        ingest_delay = rng.randint(1, 5) if sync_mode == "REALTIME" else rng.randint(60, 7200)
        ingestion_ts = event_utc + timedelta(seconds=ingest_delay)
        
        idemp = compute_idempotency_key(lid, cid, cont_id, event_type, session_id, event_utc.isoformat() + "Z")
        evt_id = make_event_id(enr_id, evt_counter)
        evt_counter += 1

        record = (
            evt_id, enr_id, lid, cid, cont_id, event_type, event_utc.isoformat(),
            tz, local_d.isoformat(), session_id, device, sync_mode,
            ingestion_ts.isoformat(), idemp
        )
        events_generated_count += 1
        batch_to_insert.append(record)

        # Inject potential near-duplicates (~1% of stream: same session & context within 2-4 seconds)
        if rng.random() < 0.01:
            near_dup_utc = event_utc + timedelta(seconds=rng.randint(1, 4))
            near_dup_local = derive_local_date_from_utc(near_dup_utc, tz)
            near_dup_ingest = ingestion_ts + timedelta(seconds=2)
            near_idemp = compute_idempotency_key(lid, cid, cont_id, event_type, session_id, near_dup_utc.isoformat() + "Z")
            near_id = make_event_id(enr_id, evt_counter)
            evt_counter += 1
            near_rec = (
                near_id, enr_id, lid, cid, cont_id, event_type, near_dup_utc.isoformat(),
                tz, near_dup_local.isoformat(), session_id, device, sync_mode,
                near_dup_ingest.isoformat(), near_idemp
            )
            events_generated_count += 1
            batch_to_insert.append(near_rec)
            near_duplicate_count += 1

        if len(batch_to_insert) >= chunk_size:
            cursor.executemany(
                "INSERT INTO activity_events (event_id, enrollment_id, learner_id, course_id, content_id, event_type, event_timestamp_utc, source_timezone, event_date, session_id, device_type, sync_status, ingestion_timestamp, idempotency_key) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                batch_to_insert,
            )
            conn.commit()
            events_inserted += len(batch_to_insert)
            batch_to_insert = []
            if not quiet:
                print(f"  .. Inserted {events_inserted} / {n_events} Activity Events")

    if batch_to_insert:
        cursor.executemany(
            "INSERT INTO activity_events (event_id, enrollment_id, learner_id, course_id, content_id, event_type, event_timestamp_utc, source_timezone, event_date, session_id, device_type, sync_status, ingestion_timestamp, idempotency_key) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            batch_to_insert,
        )
        conn.commit()
        events_inserted += len(batch_to_insert)

    if not quiet:
        print(f"[OK] Generated and Inserted {events_inserted} Activity Events (including {near_duplicate_count} near-duplicate candidates)")

    # ---------------------------------------------------------
    # STEP 10: Assessment Attempts
    # ---------------------------------------------------------
    attempts_data = []
    attempt_counter = 1
    
    for enr in enrollments_data:
        enr_id = enr[0]
        cid = enr[2]
        status = enr[5]
        asms = course_assessments_map.get(cid, [])
        
        for asm_id in asms:
            # If completed, learner attempted and passed
            if status == "COMPLETED":
                att_id = make_attempt_id(asm_id, attempt_counter)
                attempt_counter += 1
                score = round(rng.uniform(75.0, 98.0), 2)
                sub_at = datetime.fromisoformat(enr[4]) + timedelta(days=rng.randint(5, 20))
                attempts_data.append((att_id, asm_id, enr_id, 1, score, sub_at.isoformat(), sub_at.isoformat(), "PASSED"))
            elif status == "ACTIVE" and rng.random() < 0.6:
                # Active learner may have 1 attempt (some pass, some fail)
                att_id = make_attempt_id(asm_id, attempt_counter)
                attempt_counter += 1
                score = round(rng.uniform(50.0, 85.0), 2)
                sub_at = datetime.fromisoformat(enr[4]) + timedelta(days=rng.randint(5, 15))
                att_stat = "PASSED" if score >= 70.0 else "FAILED"
                attempts_data.append((att_id, asm_id, enr_id, 1, score, sub_at.isoformat(), sub_at.isoformat(), att_stat))

    cursor.executemany(
        "INSERT INTO attempts (attempt_id, assessment_id, enrollment_id, attempt_number, score, submitted_at, graded_at, attempt_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        attempts_data,
    )
    conn.commit()
    if not quiet:
        print(f"[OK] Generated {len(attempts_data)} Assessment Attempts")

    # ---------------------------------------------------------
    # STEP 11: State History (Append-Only)
    # ---------------------------------------------------------
    history_data = []
    hist_counter = 1
    for enr in enrollments_data:
        # Initial registration transition
        h_id = make_history_id(hist_counter)
        hist_counter += 1
        history_data.append((h_id, "ENROLLMENT", enr[0], None, "ACTIVE", enr[4], "SYSTEM", "SYS-REGISTRATION", "Initial student enrollment"))

        # If status moved to COMPLETED or DROPPED, append transition
        if enr[5] == "COMPLETED" and enr[7]:
            h_id = make_history_id(hist_counter)
            hist_counter += 1
            history_data.append((h_id, "ENROLLMENT", enr[0], "ACTIVE", "COMPLETED", enr[7], "SYSTEM", "SYS-OUTCOME-ENGINE", "Completion rule criteria satisfied"))
        elif enr[5] == "DROPPED" and enr[8]:
            h_id = make_history_id(hist_counter)
            hist_counter += 1
            history_data.append((h_id, "ENROLLMENT", enr[0], "ACTIVE", "DROPPED", enr[8], "SYSTEM", "SYS-PORTAL", "Student voluntary withdrawal"))

    cursor.executemany(
        "INSERT INTO state_history (history_id, entity_type, entity_id, previous_state, new_state, changed_at, actor_role, actor_id, reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        history_data,
    )
    conn.commit()
    if not quiet:
        print(f"[OK] Generated {len(history_data)} Append-Only State History Logs")

    # ---------------------------------------------------------
    # STEP 12: Course Outcomes (Snapshot Architecture)
    # ---------------------------------------------------------
    outcomes_data = []
    for enr in enrollments_data:
        enr_id = enr[0]
        cid = enr[2]
        rule_id = course_rule_map[cid]
        status = enr[5]
        
        out_id = make_outcome_id(enr_id, version=1)
        if status == "COMPLETED":
            c_pct = round(rng.uniform(85.0, 100.0), 2)
            a_pct = 100.0
            f_score = round(rng.uniform(78.0, 96.0), 2)
            calc_at = enr[7]
            reason = '{"decision": "COMPLETED", "content_passed": true, "score_passed": true, "reason": "All completion criteria satisfied"}'
            c_stat = "COMPLETED"
        elif status == "DROPPED":
            c_pct = round(rng.uniform(10.0, 40.0), 2)
            a_pct = 0.0
            f_score = None
            calc_at = enr[8]
            reason = '{"decision": "INCOMPLETE", "reason": "Enrollment dropped before completion"}'
            c_stat = "INCOMPLETE"
        else:
            c_pct = round(rng.uniform(20.0, 75.0), 2)
            a_pct = round(rng.uniform(0.0, 50.0), 2)
            f_score = round(rng.uniform(55.0, 75.0), 2) if a_pct > 0 else None
            calc_at = clock.datetime_offset(days=-5).isoformat()
            reason = '{"decision": "IN_PROGRESS", "reason": "Coursework in progress"}'
            c_stat = "IN_PROGRESS"

        outcomes_data.append((
            out_id, enr_id, 1, rule_id, c_stat, c_pct, a_pct, f_score,
            calc_at, None, 1, reason
        ))

    cursor.executemany(
        "INSERT INTO course_outcomes (outcome_id, enrollment_id, outcome_version, completion_rule_id, completion_status, content_completion_percentage, assessment_progress_percentage, final_assessment_score, calculated_at, supersedes_outcome_id, is_current, outcome_reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        outcomes_data,
    )
    conn.commit()
    if not quiet:
        print(f"[OK] Generated {len(outcomes_data)} Course Outcomes")

    # ---------------------------------------------------------
    # STEP 13: Post-Baseline Anomaly Injection & Ground Truth
    # ---------------------------------------------------------
    from backend.app.models import (
        Learner as M_Learner, Course as M_Course, Enrollment as M_Enrollment,
        ActivityEvent as M_Event, CourseOutcome as M_Outcome, Assessment as M_Assessment,
        Attempt as M_Attempt, CompletionRule as M_Rule
    )
    
    # Query instances needed by anomaly injector
    TargetSession = sessionmaker(bind=target_engine)
    db = TargetSession()
    try:
        sample_learners = db.query(M_Learner).limit(50).all()
        sample_courses = db.query(M_Course).limit(20).all()
        sample_enrollments = db.query(M_Enrollment).limit(100).all()
        sample_events = db.query(M_Event).limit(50).all()
        sample_outcomes = db.query(M_Outcome).limit(50).all()
        sample_assessments = db.query(M_Assessment).limit(50).all()
        sample_attempts = db.query(M_Attempt).limit(50).all()
        sample_rules = db.query(M_Rule).limit(20).all()

        injected = inject_anomalies(
            db_session=db,
            learners=sample_learners,
            courses=sample_courses,
            enrollments=sample_enrollments,
            events=sample_events,
            outcomes=sample_outcomes,
            assessments=sample_assessments,
            attempts=sample_attempts,
            rules=sample_rules,
            ground_truth_path=ground_truth_path,
        )

        # Insert injected anomalies into raw SQLite tables
        # 1. Duplicates
        if injected["duplicate_events"]:
            cursor.executemany(
                "INSERT INTO activity_events (event_id, enrollment_id, learner_id, course_id, content_id, event_type, event_timestamp_utc, source_timezone, event_date, session_id, device_type, sync_status, ingestion_timestamp, idempotency_key) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (e["event_id"], e["enrollment_id"], e["learner_id"], e["course_id"], e["content_id"], e["event_type"],
                     e["event_timestamp_utc"].isoformat(), e["source_timezone"], e["event_date"].isoformat(), e["session_id"],
                     e["device_type"], e["sync_status"], e["ingestion_timestamp"].isoformat(), e["idempotency_key"])
                    for e in injected["duplicate_events"]
                ]
            )

        # 2. Unenrolled
        if injected["unenrolled_events"]:
            cursor.executemany(
                "INSERT INTO activity_events (event_id, enrollment_id, learner_id, course_id, content_id, event_type, event_timestamp_utc, source_timezone, event_date, session_id, device_type, sync_status, ingestion_timestamp, idempotency_key) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (e["event_id"], e["enrollment_id"], e["learner_id"], e["course_id"], e["content_id"], e["event_type"],
                     e["event_timestamp_utc"].isoformat(), e["source_timezone"], e["event_date"].isoformat(), e["session_id"],
                     e["device_type"], e["sync_status"], e["ingestion_timestamp"].isoformat(), e["idempotency_key"])
                    for e in injected["unenrolled_events"]
                ]
            )

        # 3. Premature outcomes
        if injected["premature_outcomes"]:
            for o in injected["premature_outcomes"]:
                if o.get("supersedes_outcome_id"):
                    cursor.execute("UPDATE course_outcomes SET is_current = 0 WHERE outcome_id = ?", (o["supersedes_outcome_id"],))
            cursor.executemany(
                "INSERT INTO course_outcomes (outcome_id, enrollment_id, outcome_version, completion_rule_id, completion_status, content_completion_percentage, assessment_progress_percentage, final_assessment_score, calculated_at, supersedes_outcome_id, is_current, outcome_reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (o["outcome_id"], o["enrollment_id"], o["outcome_version"], o["completion_rule_id"], o["completion_status"],
                     o["content_completion_percentage"], o["assessment_progress_percentage"], o["final_assessment_score"],
                     o["calculated_at"].isoformat(), o["supersedes_outcome_id"], 1, o["outcome_reason"])
                    for o in injected["premature_outcomes"]
                ]
            )

        # 4. Timezone mismatch
        if injected["timezone_mismatch_events"]:
            cursor.executemany(
                "INSERT INTO activity_events (event_id, enrollment_id, learner_id, course_id, content_id, event_type, event_timestamp_utc, source_timezone, event_date, session_id, device_type, sync_status, ingestion_timestamp, idempotency_key) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (e["event_id"], e["enrollment_id"], e["learner_id"], e["course_id"], e["content_id"], e["event_type"],
                     e["event_timestamp_utc"].isoformat(), e["source_timezone"], e["event_date"].isoformat(), e["session_id"],
                     e["device_type"], e["sync_status"], e["ingestion_timestamp"].isoformat(), e["idempotency_key"])
                    for e in injected["timezone_mismatch_events"]
                ]
            )

        conn.commit()
        # Scan and register operational anomalies into exceptions table deterministically
        scan_and_register_anomalies(db, detection_time=clock.datetime_offset(0, seconds=3600))
    finally:
        db.close()

    if not quiet:
        print(f"[OK] Injected {len(injected['ground_truth_records'])} Labelled Edge Cases & Registered Operational Exceptions")

    # Re-enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.close()
    target_engine.dispose()

    duration = time.time() - start_time
    summary = {
        "profile": profile,
        "seed": seed,
        "duration_seconds": round(duration, 3),
        "counts": {
            "instructors": len(instructors_data),
            "learners": len(learners_data),
            "courses": len(courses_data),
            "cohorts": len(cohorts_data),
            "enrollments": len(enrollments_data),
            "content_items": len(content_items_data),
            "activity_events": events_inserted + len(injected["duplicate_events"]) + len(injected["unenrolled_events"]) + len(injected["timezone_mismatch_events"]),
            "assessments": len(assessments_data),
            "attempts": len(attempts_data),
            "completion_rules": len(rules_data),
            "course_outcomes": len(outcomes_data) + len(injected["premature_outcomes"]),
            "exceptions": len(injected["ground_truth_records"]),
            "state_history": len(history_data),
            "anomalies_injected": len(injected["ground_truth_records"]),
        }
    }
    
    if not quiet:
        print(f"=== Synthetic Data Generation Complete in {summary['duration_seconds']}s ===")
        for k, v in summary["counts"].items():
            print(f"  - {k}: {v:,}")

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cohortly Deterministic Synthetic Data Generator")
    parser.add_argument("--profile", choices=["starter", "full"], default="starter", help="Dataset scale preset")
    parser.add_argument("--seed", type=int, default=settings.DEFAULT_SEED, help="Fixed random seed (default: 20261022)")
    parser.add_argument("--learners", type=int, default=None, help="Custom learner count")
    parser.add_argument("--courses", type=int, default=None, help="Custom course count")
    parser.add_argument("--enrollments", type=int, default=None, help="Custom enrollment count")
    parser.add_argument("--events", type=int, default=None, help="Custom event count")
    parser.add_argument("--db-path", type=str, default="data/generated/cohortly.db", help="Target SQLite DB path")
    parser.add_argument("--quiet", action="store_true", help="Suppress console outputs")

    args = parser.parse_args()
    generate_dataset(
        profile=args.profile,
        seed=args.seed,
        num_learners=args.learners,
        num_courses=args.courses,
        num_enrollments=args.enrollments,
        num_events=args.events,
        db_path=args.db_path,
        quiet=args.quiet,
    )
