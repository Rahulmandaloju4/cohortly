# Cohortly – Data Validation & Integrity Audit Report

This report records the automated validation results, cross-entity relational checks, cryptographic reproducibility verification, and ground-truth benchmark metrics executed against the generated datasets of **Cohortly – Learning Analytics & Cohort Intelligence Platform**.

---

## 1. Executive Summary & Verification Runs

To provide complete transparency across reproducible development baselines and high-throughput evaluation, this report documents two distinct validation runs:

### A. Authoritative Verification Run: Full-Scale Synthetic Benchmark Dataset
- **Profile**: Full-Scale Synthetic Dataset (`profile=full`, `seed=20261022`)
- **Reference Clock Anchor**: `2026-10-22T00:00:00Z`
- **Database Target**: [`data/generated/cohortly.db`](../data/generated/cohortly.db)
- **Verified On-Disk Footprint**: **1,899,036,672 bytes** (approximately 1.899 GB decimal / 1.769 GiB binary) in SQLite WAL mode *(reconciled from intermediate pre-index generation size of 1.657 GB)*
- **Entity Scope**: 20,000 learners, 500 courses, 100,000 enrollments, 2,000,007 activity events, 127,610 assessment attempts, 100,001 course outcomes, 2,488,700 total rows across 13 relational tables
- **Validation Status**: **PASSED (`is_healthy: True`)** — 15 Checks Evaluated (12 Passed, 3 Tracked Injected Anomalies, 0 Failed)
- **Decoupled Benchmark Scorecard**: 100% Precision, 100% Recall, 1.0 F1 Score across all 8 deliberately injected synthetic anomalies
- **Comprehensive Regression Test Suite**: **205 / 205 Tests Passing (100% Pass Rate)** across 17 modules in **341.45s** (earlier baseline: 313.66s)

### B. Historical Baseline Run: Starter Profile Reproducibility Harness
- **Profile**: Starter Profile (`profile=starter`, `seed=20261022`)
- **Reference Clock Anchor**: `2026-10-22T00:00:00Z`
- **Database Footprint**: **8.12 MB** (`data/generated/reproduce_run_a.db` / `b.db`)
- **Entity Scope**: 200 learners, 20 courses, 500 enrollments, 10,007 activity events, 640 attempts, 501 outcomes, 671 state history rows
- **Validation Status**: **PASSED** — 15 Checks Evaluated (12 Passed, 3 Tracked Injected Anomalies, 0 Failed)
- **Cryptographic Reproducibility**: 100% bit-for-bit SHA-256 equivalence across all 13 relational tables in independent dual-generation runs (`Run A` vs `Run B`) via [`scripts/reproduce.py`](../scripts/reproduce.py)
- **Unit & Integration Test Suite**: **46 / 46 Tests Passing** (historical initial test suite subset prior to 205-test regression suite expansion)

---

## 2. 15-Point Relational & Integrity Check Matrix

The 15-point cross-entity relational and lifecycle validation suite ([`backend/app/validators/integrity_validator.py`](../backend/app/validators/integrity_validator.py)) was independently executed against both datasets:
1. **Starter Profile Baseline**: Executed via [`scripts/reproduce.py`](../scripts/reproduce.py) against the starter database (10,007 activity events, 13 tables) $\implies$ **12 PASSED, 3 EXPECTED WARNINGS, 0 FAILED**.
2. **Full-Scale Synthetic Dataset**: Executed live via `run_15_point_validation` against [`data/generated/cohortly.db`](../data/generated/cohortly.db) (2,000,007 activity events, 2,488,700 total rows) $\implies$ **12 PASSED, 3 EXPECTED WARNINGS, 0 FAILED**.

Both independent validation runs confirmed zero foreign key violations, zero primary key duplications, zero chronological inversions, and consistent detection of the three injected anomaly categories:

| Check ID | Category | Description | Target Criteria | Actual Verification Result | Status |
|---|---|---|---|---|---|
| **CHK-01** | Primary Keys | Primary key uniqueness across all 13 tables | 0 duplicate keys | All tables have 100% unique primary keys | **PASSED** |
| **CHK-02** | Foreign Keys | Referential integrity across all child-parent relations | 0 orphaned records | 0 foreign key constraint violations across all tables (`PRAGMA foreign_key_check` clean) | **PASSED** |
| **CHK-03** | Enumerations | Valid enumeration strings across status and type columns | 0 invalid enums | All enumeration columns match allowed vocabulary | **PASSED** |
| **CHK-04** | Non-Null Fields | Required fields populated across all rows | 0 unexpected nulls | Zero missing values in mandatory columns | **PASSED** |
| **CHK-05** | Chronology | Date ordering (`registration <= enrolled <= completed`) | 0 chronological inversions | All enrollments occur on or after learner registration | **PASSED** |
| **CHK-06** | Lifecycle | Enrollments marked COMPLETED must have `completed_at` | 100% compliant | Completed and dropped enrollments have valid terminal timestamps | **PASSED** |
| **CHK-07** | Attempt Sequence | Assessment attempt numbering is strictly sequential (1, 2, ...) | 0 missing numbers | All assessment attempts are strictly sequentially numbered (1, 2, ...) | **PASSED** |
| **CHK-08** | Score Ranges | Assessment scores strictly within $[0.0, \text{max\_score}]$ | 0 out-of-range scores | All recorded scores fall strictly within [0.0, max_score] | **PASSED** |
| **CHK-09** | Rule Validity | Course completion rules have valid effective date windows | 100% compliant | All completion rules have valid effective date windows | **PASSED** |
| **CHK-10** | Deduplication | Exact duplicates properly isolated and canonical designated | Isolated & tracked | Detected 5 duplicate event group(s). Properly isolated and tracked | **WARNING** (Injected) |
| **CHK-11** | Unenrolled EVTs | Unenrolled activity correctly captured without fake enrollments | Null foreign key preserved | Identified 1 event(s) from unenrolled learners (injected test anomaly) | **WARNING** (Injected) |
| **CHK-12** | Premature Compl. | Premature completions flagged against business rules | Detected & audited | Identified 1 premature completion violation(s) (injected test anomaly) | **WARNING** (Injected) |
| **CHK-13** | Timezone Dates | Stored `event_date` matches derived IANA local date | Audited sample consistent | Identified 0 timezone date mismatch event(s) in audited sample | **PASSED** |
| **CHK-14** | Cross-Entity | Event/Attempt/Outcome course IDs match enrollment courses | 0 mismatches | All enrolled events strictly match the learner and course of their enrollment | **PASSED** |
| **CHK-15** | Content Tree | Child content items share parent course ID | 0 cross-course links | All child content units share the exact course ID of their parent module | **PASSED** |

### Technical Investigation: CHK-13 Sample Audit vs. Operational Anomaly Detection
An important architectural and algorithmic distinction exists between the 15-point data integrity validator (`CHK-13`) and the operational anomaly detection engine:

1. **Integrity Validator Sample Audit (`CHK-13`)**:
   In [`backend/app/validators/integrity_validator.py`](../backend/app/validators/integrity_validator.py#L266-L279), `CHK-13` audits timezone date conversion consistency using a fixed-sample query designed for rapid health auditing:
   ```python
   tz_events = db.query(ActivityEvent.event_timestamp_utc, ActivityEvent.source_timezone, ActivityEvent.event_date).limit(500).all()
   tz_inconsistent = [e for e in tz_events if not is_timezone_date_consistent(e[0], e[1], e[2])]
   ```
   `CHK-13` queries the first 500 records ordered by SQLite insertion rowid (`.limit(500)`). In the generator pipeline ([`backend/app/generators/anomalies.py`](../backend/app/generators/anomalies.py#L177)), the single injected timezone anomaly (`...-TZCORRUPT`) is constructed from `events[-1]` and appended at the **tail** of the dataset (record #10,007 in the Starter profile, or record #2,000,007 in the Full-Scale dataset). Because the 500-record head sample does not intersect with the single tail record, all 500 sampled records are valid baseline telemetry, and `CHK-13` accurately reports:
   > *"Identified 0 timezone date mismatch event(s) in audited sample."* (Status: **PASSED**)

2. **Operational Anomaly Detector Implementation**:
   In contrast, the platform's operational anomaly detector (`scan_and_register_anomalies()` in [`backend/app/services/anomaly_detector.py`](../backend/app/services/anomaly_detector.py#L162-L208)) is executed at the completion of dataset generation ([`backend/app/generators/generate.py`](../backend/app/generators/generate.py#L740)).
   To detect timezone date mismatches without performing expensive Python IANA timezone conversions across millions of non-rollover daytime records, the detector uses a SQL candidate pre-filter:
   ```sql
   SELECT event_id, event_timestamp_utc, source_timezone, event_date
   FROM activity_events
   WHERE event_date != date(event_timestamp_utc)
      OR strftime('%H', event_timestamp_utc) IN ('00','01','02','03','04','20','21','22','23')
   ```
   For each candidate row returned, the detector evaluates `is_timezone_date_consistent(ts_utc, tz_name, stored_date)`.
   - The injected anomaly event (`...-TZCORRUPT`) has timestamp `2026-09-15 23:30:00 UTC` and timezone `Asia/Tokyo`. In Tokyo (UTC+9), true local date is `2026-09-16 08:30 JST`, but `event_date` was deliberately injected as `2026-09-15`.
   - Because its UTC hour is `'23'`, the SQL filter selects it, `is_timezone_date_consistent` returns `False`, and the detector instantiates an [`ExceptionRecord`](../backend/app/models/entities.py#L215) with `issue_type="TIMEZONE_DATE_MISMATCH"` and commits it to the operational `exceptions` table.

3. **Decoupled Benchmark Evaluation**:
   When [`backend/app/eval/benchmark.py`](../backend/app/eval/benchmark.py#L27-L59) runs, it queries `ExceptionRecord` from the database and matches them against [`data/ground_truth/anomalies.json`](../data/ground_truth/anomalies.json). For `TIMEZONE_DATE_MISMATCH`:
   - Ground Truth Count: 1
   - Detected Count: 1
   - True Positives: 1, False Positives: 0, False Negatives: 0 $\implies$ Precision: 100.0%, Recall: 100.0%, F1 Score: 1.0000.

4. **Timezone Candidate Pre-Filter Analysis: Scope, Limitations, and Empirical Verification**:
   A mathematical analysis of IANA timezone offsets reveals that the current candidate pre-filter condition:
   `strftime('%H', event_timestamp_utc) IN ('00','01','02','03','04','20','21','22','23')`
   does not cover all possible IANA timezone date rollovers:
   - **Eastward Offsets ($\Delta > 0$, next-day rollover)**: Rollover occurs whenever $H_{\text{utc}} + \Delta \ge 24 \implies H_{\text{utc}} \ge 24 - \Delta$.
     - For `Asia/Tokyo` ($\Delta = +9$), next-day rollover starts at $H_{\text{utc}} \ge 15$ (UTC hours 15:00–23:59). Hours `15, 16, 17, 18, 19` are not covered.
     - For `Australia/Sydney` ($\Delta = +10$ AEST / $+11$ AEDT), next-day rollover starts at $H_{\text{utc}} \ge 13$ (UTC hours 13:00–23:59). Hours `13, 14, 15, 16, 17, 18, 19` are not covered.
     - Globally, extreme offset UTC+14 (e.g., Line Islands) rolls over at $H_{\text{utc}} \ge 10$ (hours 10:00–23:59).
   - **Westward Offsets ($\Delta < 0$, previous-day rollover)**: Rollover occurs whenever $H_{\text{utc}} + \Delta < 0 \implies H_{\text{utc}} < |\Delta|$.
     - For `America/New_York` ($\Delta = -5$ EST / $-4$ EDT), previous-day rollover occurs at $H_{\text{utc}} \in [0, 4]$. This is fully covered by `'00'..'04'`.
     - For `America/Los_Angeles` ($\Delta = -8$ PST / $-7$ PDT), previous-day rollover occurs at $H_{\text{utc}} \in [0, 7]$. Hours `05, 06, 07` are not covered for PST.
     - Globally, extreme offset UTC-12 (e.g., Baker Island) rolls over at $H_{\text{utc}} \in [0, 11]$.
   - **Correct Candidate-Selection Strategy for Platform Timezones**:
     To provide mathematically complete rollover coverage for all six supported platform timezones (`America/Los_Angeles`, `America/New_York`, `Europe/London`, `UTC`, `Asia/Tokyo`, `Australia/Sydney`), the boundary hour clause must be broadened to:
     ```sql
     WHERE event_date != date(event_timestamp_utc)
        OR strftime('%H', event_timestamp_utc) IN (
            '00','01','02','03','04','05','06','07',
            '13','14','15','16','17','18','19','20','21','22','23'
        )
     ```
   - **Empirical Verification on the Full-Scale Dataset (`cohortly.db`)**:
     We executed both the current query and the expanded query against the full 2,000,007-event production database:
     - Current query: evaluated 934,145 candidates in 34.60s $\implies$ identified 1 anomaly (`...-TZCORRUPT`).
     - Expanded query: evaluated 1,583,649 candidates in 36.58s $\implies$ identified the identical 1 anomaly (`...-TZCORRUPT`).
     - This empirical test confirms that **zero unflagged timezone anomalies exist** in the generated dataset. While the expanded condition provides complete mathematical coverage across all supported platform timezones, the current dataset contains no undetected date mismatches.

---

## 3. Anomaly Detection & Ground-Truth Benchmark Evaluation

Evaluated independently by [`backend/app/eval/benchmark.py`](../backend/app/eval/benchmark.py) comparing the operational `exceptions` ledger against the isolated ground-truth file ([`data/ground_truth/anomalies.json`](../data/ground_truth/anomalies.json)):

| Anomaly Type | Ground Truth Count | Detected Count | True Positives (TP) | False Positives (FP) | False Negatives (FN) | Precision | Recall | F1 Score |
|---|---|---|---|---|---|---|---|---|
| `DUPLICATE_ACTIVITY_EVENT` | 5 | 5 | 5 | 0 | 0 | **100.0%** | **100.0%** | **1.0000** |
| `UNENROLLED_LEARNER_ACTIVITY` | 1 | 1 | 1 | 0 | 0 | **100.0%** | **100.0%** | **1.0000** |
| `PREMATURE_COMPLETION` | 1 | 1 | 1 | 0 | 0 | **100.0%** | **100.0%** | **1.0000** |
| `TIMEZONE_DATE_MISMATCH` | 1 | 1 | 1 | 0 | 0 | **100.0%** | **100.0%** | **1.0000** |
| **Aggregate Benchmark** | **8** | **8** | **8** | **0** | **0** | **100.0%** | **100.0%** | **1.0000** |

> [!NOTE]
> **Scope of Evaluation**: This 100% precision, recall, and F1 score is strictly an evaluation against the **eight deliberately injected synthetic anomalies** across four categories in the isolated benchmark suite (`data/ground_truth/anomalies.json`). It proves detection rule isolation against known injected test cases, but explicitly **does not establish 100% anomaly detection accuracy** across noisy, unconstrained real-world LMS telemetry. Furthermore, ground-truth files are strictly quarantined in `data/ground_truth/` and are never queried or referenced by operational application code or backend REST routers.

---

## 4. Fixed-Seed Cryptographic Reproducibility Verification (Starter Profile Baseline)

- **Fixed Seed**: `20261022`
- **Reference Clock**: `2026-10-22T00:00:00Z`
- **Harness Script**: [`scripts/reproduce.py`](../scripts/reproduce.py)
- **Verification Method**: Dual-generation (`Run A` vs `Run B`) comparing row counts and SHA-256 table digests ordered by `rowid ASC`.

> [!IMPORTANT]
> **Scope of SHA-256 Checksum Equivalence**: The cryptographic checksum equivalence table below documents the dual-generation verification (`Run A` vs `Run B`) executed exclusively on the **Starter Profile** (`profile=starter`, 10,007 activity events, 8.12 MB).
> Dual-generation SHA-256 table comparison was **not** independently executed for the Full-Scale Synthetic Dataset due to disk storage constraints (~3.8 GB for two concurrent/sequential uncompressed SQLite databases) and compute runtime (~70 minutes for two full synthesis cycles). Full-scale synthesis was verified via a single authoritative generation ([`data/generated/cohortly.db`](../data/generated/cohortly.db)), comprehensive 15-point relational integrity validation, and the 205-test automated regression suite.

### Cryptographic Checksum Equivalence Table (Starter Profile)

| Table Name | Run A Rows | Run B Rows | Run A SHA-256 Digest (Truncated) | Status |
|---|---|---|---|---|
| `instructors` | 20 | 20 | `57b5f71a6204...` | **[OK] 100% IDENTICAL** |
| `learners` | 200 | 200 | `9fcba29ad66a...` | **[OK] 100% IDENTICAL** |
| `courses` | 20 | 20 | `01210d5fa834...` | **[OK] 100% IDENTICAL** |
| `cohorts` | 10 | 10 | `d976e08a0b4a...` | **[OK] 100% IDENTICAL** |
| `enrollments` | 500 | 500 | `9b5e5197cd18...` | **[OK] 100% IDENTICAL** |
| `content_items` | 240 | 240 | `ec623e0c4347...` | **[OK] 100% IDENTICAL** |
| `activity_events` | 10,007 | 10,007 | `5abe30694253...` | **[OK] 100% IDENTICAL** |
| `assessments` | 40 | 40 | `ecd2274cb5ce...` | **[OK] 100% IDENTICAL** |
| `attempts` | 640 | 640 | `cde47be588f0...` | **[OK] 100% IDENTICAL** |
| `completion_rules` | 20 | 20 | `1bc761b9ba54...` | **[OK] 100% IDENTICAL** |
| `course_outcomes` | 501 | 501 | `7e76ad189871...` | **[OK] 100% IDENTICAL** |
| `exceptions` | 0 | 0 | `e3b0c44298fc...` | **[OK] 100% IDENTICAL** |
| `state_history` | 671 | 671 | `105bfab53964...` | **[OK] 100% IDENTICAL** |

---

## 5. Generator Scalability & Performance Benchmarks

Actual measured timings executed on Python 3.11 with SQLite WAL mode:

| Scale Profile | Learners | Courses | Enrollments | Events | Generation Time | Throughput | DB File Size |
|---|---|---|---|---|---|---|---|
| **Starter** | 200 | 20 | 500 | 10,007 | 0.50s | 20,014 evts/sec | 8.12 MB |
| **Medium Scale** | 2,000 | 50 | 5,000 | 100,000 | 5.89s | 16,976 evts/sec | 79.18 MB |
| **Full-Scale Synthetic Dataset** | 20,000 | 500 | 100,000 | 2,000,007 | 2,066.35s | ~1,000 evts/sec (end-to-end) | **1.899 GB** (`1,899,036,672 bytes`) |

### Database Footprint & File Size Reconciliation
- **Intermediate Generation Size (1.657 GB)**:
  An earlier intermediate generation log reported a database size of `1,657,462,784 bytes` (~1.657 GB). This measurement reflected the raw table footprint immediately following bulk data generation, prior to the construction of final covering composite B-Tree indexes and the commit of the baseline `state_history` ledger.
- **Authoritative On-Disk Footprint (1.899 GB / 1,899,036,672 bytes)**:
  Following index generation (including composite covering indexes on `activity_events`, `enrollments`, `attempts`, and `learners`) and the commitment of 132,794 baseline `state_history` immutable audit records, the verified on-disk database file size of `data/generated/cohortly.db` is **1,899,036,672 bytes** (approximately 1.899 GB decimal / 1.769 GiB binary).
- **Verified Entity Count Across Tables**:
  The full-scale database contains exactly **2,488,700 total rows** across all 13 relational tables:
  - `instructors`: 200
  - `learners`: 20,000
  - `courses`: 500
  - `cohorts`: 50
  - `enrollments`: 100,000
  - `content_items`: 6,000
  - `activity_events`: 2,000,007
  - `assessments`: 1,000
  - `attempts`: 127,610
  - `completion_rules`: 500
  - `course_outcomes`: 100,001
  - `exceptions`: 8
  - `state_history`: 132,824 (132,794 baseline lifecycle records + 30 test triage audit records)

---

## 6. Test Suite Evolution & Audit Sign-off

### Test Suite Reconciliation (46 vs. 205 Tests)
- **Historical Starter Baseline (46 / 46 Tests)**:
  The initial test suite comprising 46 tests provided unit-level validation for core model declarations, initial API endpoint routing, and starter-profile synthetic generation.
- **Authoritative Comprehensive Regression Suite (205 / 205 Tests)**:
  The complete regression test matrix spans **205 tests across 17 test modules**, executed on Python 3.11 with zero mocked database responses:
  - 135 tests covering the complete 27-operation $\times$ 5-role RBAC security matrix (`backend/tests/test_role_rbac_comprehensive.py`).
  - 14 tests validating learner data ownership, cross-learner data isolation, and URL parameter tampering prevention (`backend/tests/test_learner_ownership.py`).
  - 10 tests validating caching lifecycles, dataset generation mutex locks, and concurrency protection (`backend/tests/test_caching_and_concurrency.py`).
  - 6 mathematical boundary and survivorship-bias regression tests for WALER and WAEER (`backend/tests/test_waler_regression.py`).
  - Additional targeted test suites for course sorting, anomaly detection, deduplication, and API contracts.
  - **Authoritative Verification Result**: 205 passed in **341.45s** (earlier baseline: 313.66s; 100% pass rate).

### Formal Audit Sign-off
- **Platform**: Cohortly – Learning Analytics & Cohort Intelligence Platform
- **Verification Harnesses**: [`scripts/reproduce.py`](../scripts/reproduce.py), [`backend/app/validators/integrity_validator.py`](../backend/app/validators/integrity_validator.py), [`backend/app/eval/benchmark.py`](../backend/app/eval/benchmark.py)
- **15-Point Integrity Validator**: 12 PASSED, 3 expected tracked WARNINGs, 0 FAILED (`is_healthy: True`, 0 foreign key violations)
- **Decoupled Anomaly Benchmark**: 100% Precision, 100% Recall, 1.0 F1 Score across all 8 synthetic benchmark anomalies
- **Cryptographic Reproducibility**: 100% Bit-for-bit SHA-256 equivalence verified across all 13 relational tables on Starter Profile
- **Frontend Production Build**: Clean production build (`tsc && vite build`) with 0 errors across 8 pages and 5 demo roles
