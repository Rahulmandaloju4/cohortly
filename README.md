# Cohortly – Learning Analytics & Cohort Intelligence Platform

> *"Turn learning data into actionable intelligence."*

Cohortly is an enterprise-grade learning analytics and cohort intelligence platform designed for academic administrators, instructors, support staff, and platform administrators. Built for the individual 72-hour engineering challenge for the Associate AI Forward Deployed Engineer role at YottaFlex AI, Cohortly goes beyond surface-level dashboards to provide **explainable, diagnostic intelligence**: identifying anomalies, explaining root causes, presenting audit evidence, and providing actionable remediation paths.

---

## Architecture Overview

```
Cohortly/
|-- frontend/               # React 18 + TypeScript + Vite + Tailwind CSS + Recharts
|-- backend/                # Python 3.11 + FastAPI + SQLAlchemy 2.0 + SQLite
|   |-- app/
|   |   |-- api/            # 25 REST API endpoints across 9 domains
|   |   |-- core/           # Configuration, DB sessions, RBAC middleware
|   |   |-- models/         # SQLAlchemy ORM declarative models (11 tables)
|   |   |-- schemas/        # Pydantic v2 schemas
|   |   |-- services/       # Deduplication, completion rules, outcome versioning
|   |   |-- analytics/      # High-performance SQL aggregations
|   |   |-- generators/     # Deterministic generator (Seed: 20261022 + Ref Clock)
|   |   |-- validators/     # 15-point cross-entity relational validator
|   |   |-- eval/           # Isolated ground-truth evaluation benchmark
|   |-- tests/              # 13 dedicated Pytest verification suites
|-- data/
|   |-- generated/          # SQLite database storage
|   |-- ground_truth/       # Isolated ground-truth anomaly ledgers
|   |-- exports/            # Deterministic CSV and JSON exports
|   |-- manifests/          # Dataset manifests and SHA-256 checksums
|-- docs/                   # Complete architectural and data governance docs
|   |-- DATA_DICTIONARY.md
|   |-- DATABASE_SCHEMA.md
|   |-- METRIC_DEFINITIONS.md
|   |-- BUSINESS_RULES.md
|   |-- ARCHITECTURE.md
|   |-- VALIDATION_REPORT.md
|   |-- ASSUMPTIONS_AND_LIMITATIONS.md
|-- prompt-history/         # Complete audit trail of AI assistance
|-- scripts/                # Reproducibility verification and launch scripts
|-- AI_USAGE.md             # Transparent AI disclosure and oversight report
```

---

## Core Capabilities

1. **Relational Data Modeling & Integrity**:
   - 11 normalized relational entities (`instructors`, `learners`, `courses`, `cohorts`, `enrollments`, `content_items`, `activity_events`, `assessments`, `attempts`, `completion_rules`, `course_outcomes`, `exceptions`).
   - 15-point cross-entity validation suite ensuring referential, chronological, and lifecycle integrity.
2. **Two-Tier Event Deduplication**:
   - Exact deduplication via SHA-256 idempotency key hashing, designating canonical events while retaining raw records.
   - Near-duplicate retry classification within a $\le 5$-second session window for investigator audit.
3. **Accurate Timezone Handling**:
   - Preserves UTC occurrence timestamps alongside source IANA timezones and local calendar dates.
   - Detects timezone anomalies only when stored dates fail true timezone conversion.
4. **Explainable Analytics & Decision Engine**:
   - Preserves historical course completion snapshots with versioning (`outcome_version`, `supersedes_outcome_id`).
   - Generates auditable condition checklists for all completion decisions without hallucinations.
5. **Strict Ground-Truth Isolation**:
   - Operational analytics and anomaly detection queries run purely on relational source data.
   - Ground truth is stored in an isolated ledger and used strictly by independent benchmark evaluation modules.
6. **Deterministic Reproducibility**:
   - Fixed seed `20261022` and deterministic reference clock (`2026-10-22T00:00:00Z`).
   - Verified bitwise identical CSV/JSON exports with matching SHA-256 checksums.
7. **Scale & Performance**:
   - Tested up to 2,000,000 activity events with SQLite WAL mode, batch ingestion (50,000 rows/chunk), and pure SQL aggregations.

---

## Technology Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Recharts, React Router, Lucide Icons.
- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0, Pydantic v2, SQLite (WAL mode).
- **Data Engineering**: Deterministic synthetic generation, streaming CSV/JSON serialization, Pandas.
- **Testing**: Pytest, FastAPI TestClient.
- **Tools**: Git, Postman/OpenAPI compatibility.

---

## Prerequisites

- **Python**: Version 3.11+
- **Node.js**: Version 18+ (tested on v22.17.0)
- **npm**: Version 9+ (tested on 10.9.2)

---

## Installation & Setup

### 1. Clone & Setup Backend Virtual Environment

```bash
# From workspace root
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Unix/macOS:
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
# Ensure virtual environment is activated
python -m backend.app.generators.generate --profile starter --seed 20261022
```

### 2. Start Backend API Server

```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Docs (Swagger UI): `http://127.0.0.1:8000/docs`
- Health Endpoint: `http://127.0.0.1:8000/api/health`

### 3. Start Frontend Development Server

```bash
cd frontend
npm run dev
```
- Web Application: `http://localhost:5173`

---

## Reproducibility Verification

To verify that the synthetic generator produces bitwise-identical datasets and matching SHA-256 checksums under seed `20261022`:

```bash
python scripts/reproduce.py --profile starter --seed 20261022
```

---

## Testing

Run the complete 13-suite automated test matrix:

```bash
pytest backend/tests/ -v
```

---

## Documentation Index

- [`docs/DATA_DICTIONARY.md`](file:///c:/Users/manda/FusionProjects/Cohortly/docs/DATA_DICTIONARY.md): Complete data dictionary of all 12 tables and fields.
- [`docs/DATABASE_SCHEMA.md`](file:///c:/Users/manda/FusionProjects/Cohortly/docs/DATABASE_SCHEMA.md): DDL schema, indexes, constraints, and PRAGMAs.
- [`docs/METRIC_DEFINITIONS.md`](file:///c:/Users/manda/FusionProjects/Cohortly/docs/METRIC_DEFINITIONS.md): Mathematical formulations for WAL, WALER, WAEER, and completion rates.
- [`docs/BUSINESS_RULES.md`](file:///c:/Users/manda/FusionProjects/Cohortly/docs/BUSINESS_RULES.md): Governing completion rules, deduplication, and anomaly definitions.
- [`docs/ARCHITECTURE.md`](file:///c:/Users/manda/FusionProjects/Cohortly/docs/ARCHITECTURE.md): System architecture, RBAC, and performance design.
- [`docs/VALIDATION_REPORT.md`](file:///c:/Users/manda/FusionProjects/Cohortly/docs/VALIDATION_REPORT.md): 15-point validation audit and ground-truth benchmark results.
- [`docs/ASSUMPTIONS_AND_LIMITATIONS.md`](file:///c:/Users/manda/FusionProjects/Cohortly/docs/ASSUMPTIONS_AND_LIMITATIONS.md): Documented edge cases, assumptions, and demo boundaries.
- [`AI_USAGE.md`](file:///c:/Users/manda/FusionProjects/Cohortly/AI_USAGE.md): Full disclosure of AI acceleration and human engineering oversight.
- [`prompt-history/`](file:///c:/Users/manda/FusionProjects/Cohortly/prompt-history/): Chronological record of prompts used.
