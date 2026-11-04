# Cohortly – Learning Analytics & Cohort Intelligence Platform

> *"Turn learning data into actionable intelligence."*

Cohortly is an enterprise-grade learning analytics and cohort intelligence platform designed for academic administrators, instructors, support staff, and platform administrators. Built for the individual 72-hour engineering challenge for the Associate AI Forward Deployed Engineer role at YottaFlex AI, Cohortly goes beyond surface-level dashboards to provide **explainable, diagnostic intelligence**: identifying anomalies, explaining root causes, presenting audit evidence, and providing actionable remediation paths.

---

## Architecture Overview

```
Cohortly/
|-- frontend/               # React 18 + TypeScript + Vite + Tailwind CSS + Recharts
|   |-- src/
|   |   |-- components/     # Enterprise Sidebar, Header with Demo Role Switcher
|   |   |-- pages/          # 8 core domain and operational pages
|   |   |-- services/       # Axios API client injecting X-Demo-Role header
|-- backend/                # Python 3.11 + FastAPI + SQLAlchemy 2.0 + SQLite WAL mode
|   |-- app/
|   |   |-- api/            # 25+ REST API endpoints across 8 routers
|   |   |-- core/           # Database sessions, config, RBAC authorization dependency
|   |   |-- models/         # 13 SQLAlchemy ORM declarative models
|   |   |-- schemas/        # Pydantic v2 validation schemas
|   |   |-- services/       # Deduplication, completion rules, anomaly detector
|   |   |-- generators/     # Deterministic PRNG generator (Seed 20261022 + Ref Clock)
|   |   |-- validators/     # 15-point cross-entity relational validator (CHK-01 to CHK-15)
|   |   |-- eval/           # Decoupled ground-truth evaluation benchmark harness
|   |-- tests/              # 205 automated Pytest verification tests across 17 modules
|-- data/
|   |-- generated/          # SQLite database storage (cohortly.db)
|   |-- ground_truth/       # Isolated ground-truth anomaly ledgers (anomalies.json)
|-- docs/                   # Complete architectural and data governance docs
|   |-- DATA_DICTIONARY.md
|   |-- DATABASE_SCHEMA.md
|   |-- METRIC_DEFINITIONS.md
|   |-- BUSINESS_RULES.md
|   |-- ARCHITECTURE.md
|   |-- VALIDATION_REPORT.md
|   |-- ASSUMPTIONS_AND_LIMITATIONS.md
|-- prompt-history/         # Complete audit trail of AI assistance (prompts.jsonl)
|-- scripts/                # Reproducibility verification harness (reproduce.py)
|-- AI_USAGE.md             # Transparent AI disclosure and oversight report
```

---

## Frontend Navigation (8 Pages)

| Page # | Navigation Item | Route | Core Capabilities |
|---|---|---|---|
| **1** | **Overview Dashboard** | `/` | 8 Platform KPIs (WALER, WAEER, Completion Rate, At-Risk, Active Students, Catalog, Seats, Anomalies), multi-week WALER vs WAEER Recharts area chart, cohort graduation bar chart, and early warning anomaly cards. |
| **2** | **Learners Directory** | `/learners` | Searchable directory, region/status filters, slide-over detail drawer, risk warning box, transparent outcome decision checklist, and deduplicated activity stream timeline. |
| **3** | **Courses Explorer** | `/courses` | Course catalog cards with category, difficulty, instructor, active seats, graduation rate; slide-over drawer with expandable hierarchical curriculum tree, active rule thresholds, and drop-off funnel summary. |
| **4** | **Cohort Intelligence** | `/cohorts` | Cohort health cards, dual engagement metrics (WALER vs WAEER), risk distribution bar, and multi-cohort comparison modal rendering normalized retention curves over Days 0 to 42. |
| **5** | **Content Funnel** | `/content` | Course selector, sequence drop-off waterfall chart, estimated vs actual session duration comparison table, and high-friction drop-off hotspot badges (>10% drop alert). |
| **6** | **Exceptions Investigator** | `/exceptions` | Operational anomaly ledger, severity and status filters, forensic inspection drawer with syntax-highlighted JSON evidence payload, and interactive status triage form that appends to immutable `state_history`. |
| **7** | **Data Generator** | `/generator` | Scale profile presets (Starter vs Full vs Custom), seed input (`20261022`), live database health card, 13-table storage ledger, and one-click streaming CSV and JSON table exports. |
| **8** | **Quality Audit** | `/audit` | 15-Point Cross-Entity Validation execution (`CHK-01` to `CHK-15`), Decoupled Benchmark Scorecard (Precision, Recall, F1 score by anomaly type), and deterministic SHA-256 table manifest. |

---

## Core Capabilities & Architectural Invariants

1. **Relational Data Modeling & Integrity**:
   - 13 normalized relational entities (`instructors`, `learners`, `courses`, `cohorts`, `enrollments`, `content_items`, `activity_events`, `assessments`, `attempts`, `completion_rules`, `course_outcomes`, `exceptions`, `state_history`).
   - SQLite WAL mode with strict foreign key enforcement (`PRAGMA foreign_keys = ON;`).
2. **Two-Tier Event Deduplication**:
   - **Tier 1 (Exact Duplicates)**: SHA-256 idempotency key hashing (`learner_id:course_id:content_id:event_type:timestamp`). Canonical original record is retained while duplicates are automatically excluded from engagement metrics.
   - **Tier 2 (Near-Duplicates)**: Same learner, content, and event type within $\le 5.0$ seconds. Near-duplicates remain candidate records for investigation and are **not** automatically excluded from engagement metrics without review.
3. **Accurate Timezone Handling**:
   - Preserves UTC occurrence timestamps alongside source IANA timezones and local calendar dates.
   - Compares stored `event_date` against derived local calendar date using IANA timezones; legitimate UTC/local date differences around midnight are verified consistent, not anomalous.
4. **Explainable Analytics & Decision Engine**:
   - Preserves historical course completion snapshots with versioning (`outcome_version`, `supersedes_outcome_id`, `is_current`).
   - Generates auditable JSON condition checklists for all completion decisions without unverified text hallucinations.
5. **Append-Only State History Audit**:
   - Immutable `state_history` ledger records all enrollment status transitions and exception triage actions with previous state, new state, timestamp, actor, and mandatory reason.
6. **Strict Ground-Truth Isolation**:
   - Operational analytics and anomaly detection queries run purely on relational source data.
   - Ground truth is strictly quarantined in `data/ground_truth/anomalies.json` and accessed solely by the decoupled benchmark harness (`backend/app/eval/benchmark.py`).
7. **Deterministic Cryptographic Reproducibility**:
   - Fixed seed `20261022` and deterministic reference clock (`2026-10-22T00:00:00Z`).
   - Independent dual-generation runs verified 100% bit-for-bit identical across all 13 relational tables with matching SHA-256 digests.
8. **High Performance & Scale**:
   - Benchmarked at **16,976 events/second** (100,000 events in 5.89s, 79.18 MB SQLite file).

---

## Technology Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Recharts, React Router, Lucide Icons.
- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0, Pydantic v2, SQLite (WAL mode).
- **Data Engineering**: Deterministic synthetic generation, streaming RFC 4180 CSV / JSON serialization.
- **Testing**: Pytest (205 tests across 17 test modules, 100% pass rate).
- **Security & RBAC**: Role-Based Access Control via `X-Demo-Role` and `X-Demo-Learner-Id` headers (`PLATFORM_ADMIN`, `ACADEMIC_ADMIN`, `INSTRUCTOR`, `SUPPORT_STAFF`, `LEARNER`) with pre-query ownership enforcement and demo security disclaimers.

---

## Prerequisites

- **Python**: Version 3.11+ (tested on Python 3.11.7)
- **Node.js**: Version 18+ (tested on v22.17.0)
- **npm**: Version 9+ (tested on 10.9.2)

---

## Installation & Quick Start

### 1. Clone & Setup Backend Virtual Environment

```bash
# Clone the repository
git clone https://github.com/manda/Cohortly.git
cd Cohortly

# Create and activate virtual environment
# Windows:
python -m venv venv
.\venv\Scripts\activate
# Unix/macOS:
python3 -m venv venv
source venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt
```

### 2. Setup Frontend

```bash
cd frontend
npm install
cd ..
```

---

## Running the Application

### 1. Generate Starter Synthetic Dataset

```bash
# Generates starter database (200 learners, 20 courses, 500 enrollments, 10,007 events)
python -m backend.app.generators.generate --profile starter --seed 20261022
```

### 2. Start Backend API Server

```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Documentation (Interactive Swagger UI): `http://127.0.0.1:8000/docs`
- Health Endpoint: `http://127.0.0.1:8000/api/health`

### 3. Start Frontend Development Server

```bash
cd frontend
npm run dev
```
- Web Application: `http://localhost:5173`

---

## Deterministic Reproducibility Verification

Run the automated reproducibility harness to verify that independent synthesis runs with seed `20261022` produce bitwise-identical SHA-256 table digests:

```bash
python scripts/reproduce.py --profile starter --seed 20261022
```

Output highlights:
```
[SUCCESS] All 13 relational tables are bit-for-bit cryptographically reproducible!
Executed: 15 Checks | Passed: 12 | Tracked Anomalies: 3 | Failed: 0
Precision: 100.0% | Recall: 100.0% | F1 Score: 100.0% (8 TP | 0 FP | 0 FN)
```

---

## Automated Test Suite

Run the full 205-test Pytest matrix across all 17 test modules:

```bash
pytest backend/tests/ -v
```


---

## Documentation Index

- [`docs/DATA_DICTIONARY.md`](file:///c:/Users/manda/FusionProjects/Cohortly/docs/DATA_DICTIONARY.md): Complete data dictionary of all 13 tables and 70+ columns.
- [`docs/DATABASE_SCHEMA.md`](file:///c:/Users/manda/FusionProjects/Cohortly/docs/DATABASE_SCHEMA.md): DDL schema, composite indexes, foreign key constraints, and SQLite PRAGMAs.
- [`docs/METRIC_DEFINITIONS.md`](file:///c:/Users/manda/FusionProjects/Cohortly/docs/METRIC_DEFINITIONS.md): Mathematical formulations for WAL, WALER, WAEER, and graduation rates.
- [`docs/BUSINESS_RULES.md`](file:///c:/Users/manda/FusionProjects/Cohortly/docs/BUSINESS_RULES.md): Governing completion rules, two-tier deduplication, and anomaly definitions.
- [`docs/ARCHITECTURE.md`](file:///c:/Users/manda/FusionProjects/Cohortly/docs/ARCHITECTURE.md): System architecture, RBAC capabilities, and performance optimizations.
- [`docs/VALIDATION_REPORT.md`](file:///c:/Users/manda/FusionProjects/Cohortly/docs/VALIDATION_REPORT.md): 15-point validation audit, cryptographic digests, and ground-truth benchmark scorecard.
- [`docs/ASSUMPTIONS_AND_LIMITATIONS.md`](file:///c:/Users/manda/FusionProjects/Cohortly/docs/ASSUMPTIONS_AND_LIMITATIONS.md): Documented edge cases, design decisions, and demo boundaries.
- [`AI_USAGE.md`](file:///c:/Users/manda/FusionProjects/Cohortly/AI_USAGE.md): Transparent disclosure of AI acceleration and human engineering modifications.
- [`prompt-history/prompts.jsonl`](file:///c:/Users/manda/FusionProjects/Cohortly/prompt-history/prompts.jsonl): Chronological JSONL log of all engineering prompts.
#   c o h o r t l y  
 