# Cohortly – AI Usage & Engineering Oversight Disclosure

In accordance with Section 17 of the YottaFlex AI engineering challenge, this document provides a transparent and verifiable record of how AI assistance (Google DeepMind Antigravity / Gemini 3.8) was utilized during the design, architecture, and implementation of **Cohortly**.

---

## 1. Where AI Accelerated Development

1. **Boilerplate and Scaffolding**:
   - Accelerated the authoring of repetitive relational DDL definitions, Pydantic validation schemas, and SQLAlchemy 2.0 declarative models across all 11 tables.
   - Generated initial scaffolding for React components, TypeScript interfaces, and Tailwind styling classes.
2. **Comprehensive Documentation Authoring**:
   - Rapidly synthesized detailed Markdown documentation (`DATA_DICTIONARY.md`, `DATABASE_SCHEMA.md`, `METRIC_DEFINITIONS.md`, `BUSINESS_RULES.md`, `ARCHITECTURE.md`) based on the architectural specifications.
3. **Synthetic Data Distributions & Deterministic Math**:
   - Assisted in structuring realistic Poisson and normal distribution samplers for student sessions, assessment scores, and completion probability curves.

---

## 2. Where AI Generated Substantial Implementation

1. **SQLAlchemy 2.0 ORM & SQLite Configurations**:
   - Declarative models with cascading rules, unique constraints, and B-Tree index specifications.
2. **Two-Tier Deduplication & Anomaly Detection Queries**:
   - Structured pure relational SQL queries for exact duplicate grouping (`idempotency_key`), unenrolled activity detection, and timezone conversion matching.
3. **Automated Pytest Matrix**:
   - Generated 13 test suites covering edge cases, boundary conditions, and contract assertions.

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

---

## 4. Engineering Validation Methods

1. **Static Analysis & Code Review**:
   - Verified that zero operational modules import or reference `data/ground_truth/`.
   - Verified that foreign key cascades and restricted deletes operate cleanly.
2. **Deterministic Bitwise Reproducibility Verification**:
   - Executed `scripts/reproduce.py` twice with seed `20261022` to assert bitwise identical SHA-256 checksums.
3. **Automated Testing**:
   - Executed full 13-suite Pytest matrix on Python 3.11 with zero mocked database responses.
4. **End-to-End Local Execution**:
   - Verified FastAPI backend Swagger docs on port 8000.
   - Verified React Vite frontend on port 5173 across all 8 core views and 5 demo roles.
