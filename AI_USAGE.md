# Cohortly – AI Usage & Engineering Oversight Disclosure

In accordance with Section 17 of the YottaFlex AI engineering challenge, this document provides a transparent and verifiable record of how AI assistance (Google DeepMind Antigravity / Gemini 3.8) was utilized during the design, architecture, and implementation of **Cohortly – Learning Analytics & Cohort Intelligence Platform**.

---

## 1. Where AI Accelerated Development

1. **Boilerplate and Scaffolding**:
   - Accelerated the authoring of relational DDL definitions, Pydantic v2 validation schemas, and SQLAlchemy 2.0 declarative models across all 13 operational tables.
   - Generated initial scaffolding for React components, TypeScript interfaces, and Tailwind CSS enterprise styling classes.
2. **Comprehensive Documentation Authoring**:
   - Rapidly synthesized detailed Markdown documentation (`DATA_DICTIONARY.md`, `DATABASE_SCHEMA.md`, `METRIC_DEFINITIONS.md`, `BUSINESS_RULES.md`, `ARCHITECTURE.md`, `VALIDATION_REPORT.md`, `ASSUMPTIONS_AND_LIMITATIONS.md`) matching the architectural specifications.
3. **Synthetic Data Distributions & Deterministic Math**:
   - Assisted in structuring realistic Poisson and normal distribution samplers for student sessions, assessment scores, and completion probability curves.

---

## 2. Where AI Generated Substantial Implementation

1. **SQLAlchemy 2.0 ORM & SQLite WAL Configurations**:
   - Declarative models with cascading rules, strict foreign key constraints, and composite B-Tree index specifications.
2. **Two-Tier Deduplication & Anomaly Detection Queries**:
   - Structured pure relational SQL queries for exact duplicate grouping (`idempotency_key`), near-duplicate retention, unenrolled activity detection, and timezone conversion matching.
3. **Automated Pytest Matrix**:
   - Generated 40 automated unit and integration tests across 13 test suites covering edge cases, boundary conditions, and contract assertions.
4. **React Enterprise Frontend**:
   - Implemented 8 comprehensive UI pages featuring Recharts multi-axis charts, dark navy navigation, interactive demo role switcher, slide-over inspection drawers, and status triage workflows.

---

## 3. Human Review & Engineering Modifications (Known AI-Generated Errors & Corrections)

During the iterative engineering process, the following critical design flaws were identified in the initial AI-proposed design and manually corrected:

| Ref # | Initial AI Proposal | Architectural Flaw Identified | Human Engineering Correction Implemented |
|---|---|---|---|
| **1** | Timezone anomaly detection flagged any event where `DATE(utc_timestamp) != event_date`. | **Incorrect logic**: A legitimate event occurring at 23:30 NY time naturally rolls into the next day in UTC without being an anomaly. | Changed detection logic to strictly compare stored `event_date` against `DATE(timezone_convert(event_timestamp_utc, source_timezone))`. |
| **2** | Single exact-hash event deduplication that discarded duplicates. | **Data loss risk & missed retries**: Overlooked near-duplicate retries with slight timestamp differences. | Implemented two-tier strategy: Exact Duplicates (canonical retention + raw preservation) and Potential Near-Duplicates ($\le 5$s session retry window). |
| **3** | Unique constraint on `course_outcomes(enrollment_id)`. | **Audit destruction**: Recalculating completion wiped out previous historical decisions and rule versions. | Implemented outcome snapshot versioning with `outcome_version`, `supersedes_outcome_id`, and `is_current` flags. |
| **4** | Event ID format `EVT-<enrollment_id>-<seq>`. | **Foreign key impossibility**: Unenrolled activity anomalies have no `enrollment_id`, making the ID template invalid without fake records. | Designed dual ID format: `EVT-ENR-...` for normal events and `EVT-UNENROLLED-<lrn>-<crs>-...` with nullable `enrollment_id`. |
| **5** | Weekly Active Engagement Rate divided by eligible enrollments. | **Entity mismatch**: Divided distinct learners by total enrollments, skewing rates for multi-enrolled students. | Separated into WALER (Learner Engagement Rate) and WAEER (Enrollment Engagement Rate) with consistent $[W_{\text{start}}, W_{\text{end}}]$ windows. |
| **6** | Python `CURRENT_TIMESTAMP` defaults in models. | **Nondeterministic exports**: Caused different SHA-256 checksums across repeated runs with the same seed. | Replaced with deterministic reference clock (`2026-10-22T00:00:00Z`) and stable record serialization. |
| **7** | Vague "AI-assisted" explanation claims. | **Overstatement**: The engine uses deterministic business rules and relational SQL checks, not an LLM. | Renamed to "Explainable Analytics & Decision Engine" with auditable JSON rule checklists. |
| **8** | Automated exclusion of potential near-duplicates from analytics. | **False negative on rapid interactions**: Users rapidly clicking 'next' or scrubbing videos were censored from engagement rates. | Refined policy: Exact duplicates are auto-excluded; near-duplicates remain candidates for review and are NOT automatically excluded without review. |
| **9** | Overwriting entity lifecycle status in place. | **Lost transition audit**: Enrollment and exception resolution changes destroyed transition history. | Introduced append-only `state_history` table recording entity, previous state, new state, actor, and reason. |
| **10** | Validation count discrepancy (13 vs 15). | **Inconsistency**: Architecture and validator checks cited different numbers of checks. | Standardized on 15-point cross-entity validation (CHK-01 to CHK-15) across all schemas, APIs, and docs. |

---

## 4. Engineering Validation Methods

1. **Static Analysis & Code Review**:
   - Verified that zero operational modules import or reference `data/ground_truth/`.
   - Verified that foreign key cascades and restricted deletes operate cleanly with PRAGMA foreign keys enabled.
2. **Deterministic Bitwise Reproducibility Verification**:
   - Executed `scripts/reproduce.py` with seed `20261022` to assert bitwise identical SHA-256 checksums across all 13 relational tables in dual-generation runs.
3. **Automated Testing**:
   - Executed full 40-test Pytest matrix on Python 3.11 with zero mocked database responses (100% pass rate in 4.22s).
4. **End-to-End Local Execution**:
   - Verified FastAPI backend OpenAPI docs on port 8000.
   - Verified React Vite frontend build (`tsc && vite build`) with 0 errors across all 8 core pages and 5 demo roles.
5. **Decoupled Evaluation Benchmark**:
   - Confirmed 100% precision, 100% recall, and 100% F1 score across all 4 anomaly categories against the isolated ground-truth file.
