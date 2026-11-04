# Cohortly – Learning Analytics & Cohort Intelligence Platform

> *"Turn learning data into actionable intelligence."*

Cohortly is an explainable learning analytics and cohort intelligence web platform built for the individual 72-hour engineering challenge for the **Associate AI Forward Deployed Engineer** role at YottaFlex AI. It moves beyond descriptive dashboards to provide **diagnostic intelligence**: detecting data-quality anomalies, explaining root causes, presenting verifiable audit evidence, and delivering auditable course completion decisions.

---

## Architecture Overview

```
Cohortly/
|-- frontend/               # React 18 + TypeScript + Vite + Tailwind CSS + Recharts
|   |-- src/pages/          # 8 core domain & operational views
|   |-- src/services/       # API client injecting X-Demo-Role and X-Demo-Learner-Id
|-- backend/                # Python 3.11 + FastAPI + SQLAlchemy 2.0 + SQLite (WAL mode)
|   |-- app/api/            # 27 canonical REST operations across 8 routers
|   |-- app/core/           # Database sessions, config, RBAC authorization dependency
|   |-- app/models/         # 13 normalized SQLAlchemy declarative models
|   |-- app/validators/     # 15-point cross-entity relational validator (CHK-01 to CHK-15)
|   |-- app/eval/           # Decoupled ground-truth evaluation benchmark harness
|-- data/
|   |-- generated/          # SQLite database storage (cohortly.db)
|   |-- ground_truth/       # Quarantined benchmark anomaly ledgers (anomalies.json)
|-- docs/                   # Full architectural, schema & metric specifications
|-- scripts/reproduce.py    # Dual-run bitwise cryptographic reproducibility harness
|-- walkthrough5.md         # Full-scale production verification & walkthrough report
|-- AI_USAGE.md             # Transparent AI disclosure and human engineering review log
```

---

## Key Features & Core Logic

1. **Relational Data Model & Integrity**: 13 normalized entities (`instructors`, `learners`, `courses`, `cohorts`, `enrollments`, `content_items`, `activity_events`, `assessments`, `attempts`, `completion_rules`, `course_outcomes`, `exceptions`, `state_history`) in SQLite with WAL mode, foreign keys enabled (`PRAGMA foreign_keys = ON`), and covering B-Tree indexes.
2. **Two-Tier Event Deduplication**:
   - **Tier 1 (Exact Duplicates)**: Deterministic SHA-256 idempotency key (`learner_id:course_id:content_id:event_type:timestamp`). Canonical original is retained; duplicates are excluded from analytics.
   - **Tier 2 (Near-Duplicates)**: Same learner, content, and event type within $\le 5.0$ seconds. Flagged as candidate retries for review; not automatically censored from engagement metrics.
3. **Timezone Handling**: Persists canonical occurrence timestamps in UTC while maintaining student local calendar dates and IANA timezones; verified consistent across midnight rollovers.
4. **Explainable Completion Engine**: Evaluates content progress, quizzes, and score thresholds against active governing rules, outputting auditable JSON condition checklists and versioned outcome snapshots (`outcome_version`, `supersedes_outcome_id`, `is_current`).
5. **Survivorship-Bias-Free Engagement Metrics**:
   - **WALER** (Weekly Active Learner Engagement Rate): Active eligible learners / eligible learners $\in [0\%, 100\%]$.
   - **WAEER** (Weekly Active Enrollment Engagement Rate): Active eligible enrollments / eligible enrollments $\in [0\%, 100\%]$.
   - Evaluated using point-in-time lifecycle milestones (`registration_date`, `enrolled_at`, `dropped_at`, `completed_at`), preventing retrospective erasure of learners who completed or dropped later.
6. **Append-Only State History**: Immutable `state_history` ledger logs all enrollment status transitions and exception triage actions with actor roles, timestamps, and mandatory audit reasons.
7. **Authoritative 27-Operation RBAC & Learner Privacy**:
   - 5 roles: `PLATFORM_ADMIN`, `ACADEMIC_ADMIN`, `INSTRUCTOR`, `SUPPORT_STAFF`, `LEARNER`.
   - `LEARNER` role is strictly restricted to self-service access on their own record (`/api/learners/{id}`); URL tampering returns **HTTP 403 Forbidden**; the learners roster is restricted.
   - *Demo Auth Boundary*: `X-Demo-Role` and `X-Demo-Learner-Id` headers are provided strictly for evaluation convenience and must be replaced with server-verified JWT/OIDC bearer tokens in production.

---

## Application Pages (8 Core Views)

| # | Page | Route | Description |
|---|---|---|---|
| **1** | **Overview Dashboard** | `/` | 8 platform KPIs with accessible tooltips; 8-week WALER vs WAEER trend chart; 50-cohort graduation progression with interactive `<Brush />` slider; early warning anomaly cards. |
| **2** | **Learners Directory** | `/learners` | Searchable directory, region/status filters, slide-over profile drawer, transparent outcome checklist, deduplicated activity stream. *(Restricted for `LEARNER`)*. |
| **3** | **Courses & Curriculum** | `/courses` | 500-course catalog sorted deterministically by Course ID (`CRS-000001` to `CRS-000500`); responsive pagination (50 items/page, 10 pages total); multi-line title wrapping; slide-over curriculum tree & completion rule drawer. |
| **4** | **Cohort Intelligence** | `/cohorts` | 50 cohort cards with dual engagement rates (WALER vs WAEER), risk distribution indicators, and multi-cohort comparison modal over Days 0 to 42. |
| **5** | **Content Funnel** | `/content` | Course selector, lesson sequence drop-off waterfall chart, estimated vs actual session duration comparison, and high-friction hotspot alert badges (>10% drop). |
| **6** | **Exceptions & Triage** | `/exceptions` | Data-quality anomaly ledger, forensic inspection drawer with syntax-highlighted JSON evidence, and interactive status triage form (`OPEN` $\leftrightarrow$ `INVESTIGATING` $\leftrightarrow$ `RESOLVED`) appending to `state_history`. |
| **7** | **Synthetic Generator** | `/generator` | Profile presets (Starter vs Full vs Custom), fixed seed (`20261022`), live database health card, 13-table storage ledger, and streaming CSV/JSON table exports. |
| **8** | **Quality & Benchmark Audit** | `/audit` | Live execution of 15-Point Relational Validation Suite (`CHK-01` to `CHK-15`), Decoupled Benchmark Scorecard (Precision, Recall, F1 score), and SHA-256 table manifest viewer. |

---

## Dataset Scale Profiles & Reproducibility

| Metric / Entity | Starter Profile | Full-Scale Synthetic Benchmark Profile |
|---|---|---|
| **Primary Use** | Fast local testing, quick verification (~2s) | Full benchmark & relational integrity audit |
| **Learners / Courses / Cohorts** | 200 / 20 / 10 | 20,000 / 500 / 50 |
| **Enrollments / Content Items** | 500 / 240 | 100,000 / 6,000 |
| **Activity Events** | 10,007 (10k valid + 7 injected) | 2,000,007 (2M valid + 7 injected) |
| **Assessments / Attempts** | 40 / 640 | 1,000 / 127,610 |
| **Outcomes / Rules / Exceptions** | 501 / 20 / 8 | 100,001 / 500 / 8 |
| **State History Records** | 671 (baseline) | 132,824 (132,794 baseline + 30 test triage audit records) |
| **Total Database Rows** | **12,857** | **2,488,700** |
| **Database Size on Disk** | **~10 MB** | **1,899,036,672 bytes (~1.899 GB)** |

### Cryptographic Reproducibility
Independent synthesis runs with seed `20261022` and anchor `2026-10-22T00:00:00Z` produce bit-for-bit identical SHA-256 table digests:
```bash
python scripts/reproduce.py --profile starter --seed 20261022
```

### Decoupled Anomaly Benchmark
Evaluated against **8 deliberately injected synthetic anomalies** in `data/ground_truth/anomalies.json` (5 duplicate events, 1 unenrolled event, 1 premature completion, 1 timezone offset date mismatch):
- **Precision**: 100.0% (8 / 8) | **Recall**: 100.0% (8 / 8) | **F1 Score**: 1.0000
*(Note: Evaluated strictly against synthetic test harness cases; does not represent unconstrained production LMS telemetry).*

---

## Installation & Running the Application

### 1. Setup Backend & Virtual Environment
```bash
git clone https://github.com/<your-username>/Cohortly.git
cd Cohortly

# Windows:
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux:
python3 -m venv venv
source venv/bin/activate

pip install -r backend/requirements.txt
```

### 2. Setup Frontend
```bash
cd frontend
npm install
cd ..
```

### 3. Generate Data & Launch
```bash
# Option A: Quick-start with starter profile (~2s generation)
python -m backend.app.generators.generate --profile starter --seed 20261022

# Option B: Run with pre-generated full database (data/generated/cohortly.db already present)

# Start Backend API Server (Port 8000)
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

# Start Frontend Dev Server (in another terminal, Port 5173)
cd frontend
npm run dev
```

- **Web Application**: `http://localhost:5173`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`
- **Health Diagnostic**: `http://127.0.0.1:8000/api/health`

---

## Automated Testing

```bash
# Run all 205 Pytest tests across 17 modules
pytest backend/tests/ -v

# Run frontend production build (TypeScript + Vite)
cd frontend
npm run build
cd ..
```
- **Test Results**: All **205 / 205 tests passed** with 100% success rate (authoritative final regression run: **341.45s**; baseline run: **313.66s**).
- **Frontend Build**: Clean production build in **13.53s** (`tsc && vite build`, 0 compiler errors).

---

## Documentation Index

- [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md): Comprehensive schema data dictionary (13 tables, 70+ attributes).
- [`docs/DATABASE_SCHEMA.md`](docs/DATABASE_SCHEMA.md): DDL schema, composite indexes, foreign keys, and SQLite PRAGMA settings.
- [`docs/METRIC_DEFINITIONS.md`](docs/METRIC_DEFINITIONS.md): Mathematical formulations for WAL, WALER, WAEER, and completion metrics.
- [`docs/BUSINESS_RULES.md`](docs/BUSINESS_RULES.md): Governing rules, two-tier deduplication, and anomaly definitions.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): System architecture, caching strategies, and 27-operation RBAC matrix.
- [`docs/VALIDATION_REPORT.md`](docs/VALIDATION_REPORT.md): 15-point validation report, cryptographic digests, and benchmark scorecard.
- [`docs/ASSUMPTIONS_AND_LIMITATIONS.md`](docs/ASSUMPTIONS_AND_LIMITATIONS.md): Edge cases, design assumptions, and demo boundaries.
- [`walkthrough5.md`](walkthrough5.md): End-to-end implementation and full-scale production verification walkthrough.
- [`AI_USAGE.md`](AI_USAGE.md): Transparent AI disclosure, engineering oversight, and human corrections log.
- [`prompt-history/prompts.jsonl`](prompt-history/prompts.jsonl): Chronological log of engineering prompts.

---

## Limitations & AI Disclosure

1. **Database Concurrency**: SQLite WAL mode with 30s busy timeout supports concurrent read workflows across 24 workers. For high-volume multi-writer production environments, migration to PostgreSQL with horizontal read replicas is recommended.
2. **Authentication**: `X-Demo-Role` and `X-Demo-Learner-Id` headers are client-controlled demo headers for evaluation convenience. Production systems must implement server-verified JWT/OIDC authentication.
3. **AI Disclosure**: AI assistance (Google DeepMind Antigravity / Gemini) was used for initial boilerplate, schema definitions, and draft scaffolding. Critical business logic, timezone rollover corrections, two-tier deduplication, snapshot versioning, and WALER mathematical formulations were manually architected and reviewed. Full disclosure is provided in [`AI_USAGE.md`](AI_USAGE.md).
