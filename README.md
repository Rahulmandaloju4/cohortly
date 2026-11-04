# Cohortly – Learning Analytics & Cohort Intelligence Platform

> *"Turn learning data into actionable intelligence."*

Cohortly is an explainable learning analytics and cohort intelligence web platform designed for academic administrators, instructors, support staff, and platform administrators. Developed for the individual 72-hour engineering challenge for the **Associate AI Forward Deployed Engineer** role at YottaFlex AI, Cohortly moves beyond static metrics dashboards to provide **diagnostic intelligence**: identifying data-quality anomalies, explaining root causes, presenting verifiable audit evidence, and delivering transparent course completion decisions through auditable rule checklists.

---

## 1. Overview

Educational institutions, bootcamps, and enterprise learning management systems (LMS) generate massive streams of student interaction telemetry—such as video views, document downloads, quiz attempts, and course milestones. However, raw LMS telemetry frequently suffers from common real-world data flaws:
- Multi-client retry storms generating exact and near-duplicate event streams.
- Client clock skew and timezone offsets that distort engagement metrics around midnight boundaries.
- Asymmetric definitions of active engagement that artificially inflate metrics above 100% or introduce survivorship bias into historical cohort analysis.
- Unenrolled user sessions that orphan activity records from course enrollments.
- "Black-box" completion determinations that award or withhold certificates without transparent, auditable justification.

Cohortly addresses these challenges by combining strict relational schema integrity, deterministic event deduplication, point-in-time historical lifecycle modeling, and transparent, rules-based completion logic.

---

## 2. Problem Statement & Objectives

Traditional learning analytics dashboards often summarize vanity metrics without validating the integrity of the underlying data pipeline. Cohortly was architected around seven core objectives:

1. **Relational Schema Rigor**: Model the complete LMS lifecycle across 13 normalized entities with strict foreign key constraints and covering composite B-Tree indexes in SQLite (Write-Ahead Logging mode).
2. **Two-Tier Deduplication**: Differentiate between exact duplicate retries (deterministic SHA-256 idempotency hashing) and rapid session interactions (near-duplicates within $\le 5.0$ seconds), preventing artificial metric inflation without censoring legitimate rapid user activity.
3. **Accurate Timezone Preservation**: Store canonical timestamps in UTC while maintaining student local calendar dates and IANA timezones, distinguishing genuine timezone day-rollovers from corrupted device timestamps.
4. **Survivorship-Bias-Free Engagement Metrics**: Mathematically formulate Weekly Active Learner Engagement Rate (**WALER**) and Weekly Active Enrollment Engagement Rate (**WAEER**) such that numerators are strict subsets of denominators ($0\% \le \text{Rate} \le 100\%$) and historical eligibility is derived strictly from immutable event-time milestones.
5. **Explainable Completion Engine**: Replace opaque completion flags with versioned outcome snapshots (`outcome_version`, `supersedes_outcome_id`, `is_current`) and transparent JSON evaluation checklists.
6. **Decoupled Anomaly Benchmark**: Isolate operational queries from benchmark truth; evaluate detection accuracy strictly through a decoupled benchmark harness comparing against quarantined ground truth.
7. **Deterministic Cryptographic Reproducibility**: Guarantee that independent synthesis runs with fixed seed `20261022` and reference clock `2026-10-22T00:00:00Z` produce bit-for-bit identical SHA-256 database table digests.

---

## 3. Key Features

- **Explainable Course Completion Decision Engine**: Evaluates content completion percentages, mandatory quiz milestones, and passing score thresholds against active governing rules, outputting auditable criteria checklists for every student outcome.
- **Two-Tier Event Deduplication**: Automatic analytical exclusion for exact duplicate events; flag-and-review retention for rapid-fire near-duplicates ($\le 5.0$s window).
- **Point-in-Time Historical Cohort Analytics**: Computes 8-week historical WALER and WAEER trajectories using registration and enrollment timestamps, preventing retrospective pruning of learners who later dropped or graduated.
- **Append-Only Audit Ledger (`state_history`)**: Records all enrollment lifecycle transitions and exception triage actions with actor roles, timestamps, and mandatory audit reasons.
- **Authoritative 27-Operation Role-Based Access Control (RBAC)**: Enforces granular role boundaries across 5 demo roles (`PLATFORM_ADMIN`, `ACADEMIC_ADMIN`, `INSTRUCTOR`, `SUPPORT_STAFF`, `LEARNER`), featuring learner self-service privacy protection that blocks peer inspection and URL tampering.
- **15-Point Relational & Lifecycle Validation Suite (`CHK-01` to `CHK-15`)**: Comprehensive automated audit covering primary key uniqueness, foreign key referential integrity, date chronology, lifecycle milestones, score ranges, and cross-entity course alignment.
- **Deterministic Synthetic Data Generator**: High-throughput parameterized generation engine with deterministic pseudorandom number generators (PRNG) supporting Starter and Full-scale synthetic benchmark profiles.
- **Decoupled Ground-Truth Benchmark Harness**: Quantitative evaluation scoring Precision, Recall, and F1 score against deliberately injected synthetic anomalies without operational data leakage.

---

## 4. Application Pages

The Cohortly web interface consists of eight dedicated pages:

| # | Page Name | Route | Core Capabilities |
|---|---|---|---|
| **1** | **Overview Dashboard** | `/` | 8 Platform KPI cards with full definitions and tooltips (WALER, WAEER, Completion Rate, At-Risk Learners, Active Students, Curriculum Catalog, Total Enrollments, Quality Anomalies); 8-week WALER vs WAEER trend chart; cohort graduation bar chart with interactive `<Brush />` slider across 50 cohorts; early warning anomaly cards with safe text wrapping. |
| **2** | **Learners Directory** | `/learners` | Searchable directory with region and status filters; slide-over inspection drawer; transparent graduation decision checklist; deduplicated activity stream timeline. *(Restricted for `LEARNER` role)*. |
| **3** | **Courses & Curriculum** | `/courses` | 500-course catalog sorted deterministically by Course ID (`CRS-000001` to `CRS-000500`); responsive pagination (50 courses per page, 10 pages total) with previous/next controls; multi-line natural title wrapping with visible Level 1/2/3 distinction; slide-over drawer with hierarchical curriculum tree, active completion rule parameters, and drop-off funnel summary. |
| **4** | **Cohort Intelligence** | `/cohorts` | 50 cohort cards displaying dual engagement metrics (WALER and WAEER); risk distribution indicators; multi-cohort comparison modal rendering normalized retention curves over Days 0 to 42. |
| **5** | **Content Funnel** | `/content` | Course selector; lesson-by-lesson sequence drop-off waterfall chart; estimated vs actual session duration comparison table; high-friction drop-off hotspot badges (>10% drop alert). |
| **6** | **Exceptions & Triage** | `/exceptions` | Operational data-quality anomaly ledger; severity and status filters; forensic inspection drawer with syntax-highlighted JSON evidence payload; interactive triage status update form (`OPEN` $\leftrightarrow$ `INVESTIGATING` $\leftrightarrow$ `RESOLVED`) appending to the immutable `state_history` ledger. |
| **7** | **Synthetic Generator** | `/generator` | Profile presets (Starter vs Full vs Custom); fixed seed input (`20261022`); reference clock indicator; live database health status; 13-table storage ledger; streaming CSV and JSON table export triggers. |
| **8** | **Quality & Benchmark Audit** | `/audit` | Live execution of the 15-Point Relational Validation Suite (`CHK-01` to `CHK-15`); Decoupled Benchmark Scorecard (Precision, Recall, F1 score by anomaly category); cryptographic SHA-256 table manifest viewer. |

---

## 5. Architecture Overview

```
Cohortly/
|-- frontend/               # React 18 + TypeScript + Vite + Tailwind CSS + Recharts
|   |-- src/
|   |   |-- components/     # Enterprise Sidebar, Header with Demo Role Switcher, Badges
|   |   |-- pages/          # 8 core domain and operational pages
|   |   |-- services/       # Axios API client injecting X-Demo-Role and X-Demo-Learner-Id
|-- backend/                # Python 3.11 + FastAPI + SQLAlchemy 2.0 + SQLite (WAL Mode)
|   |-- app/
|   |   |-- api/            # 27 canonical REST endpoints across 8 routers
|   |   |-- core/           # Database sessions, config, RBAC authorization dependency
|   |   |-- models/         # 13 SQLAlchemy declarative ORM models
|   |   |-- schemas/        # Pydantic v2 request/response schemas
|   |   |-- services/       # Deduplication, completion rules, anomaly detector
|   |   |-- generators/     # Deterministic PRNG generator (Seed 20261022 + Ref Clock)
|   |   |-- validators/     # 15-point cross-entity relational validator (CHK-01 to CHK-15)
|   |   |-- eval/           # Decoupled ground-truth evaluation benchmark harness
|   |-- tests/              # 205 automated Pytest verification tests across 17 modules
|-- data/
|   |-- generated/          # SQLite database storage (cohortly.db, WAL files)
|   |-- ground_truth/       # Quarantined ground-truth anomaly ledgers (anomalies.json)
|   |-- manifests/          # Cryptographic SHA-256 table checksum manifests
|-- docs/                   # Architectural specifications and data governance docs
|   |-- DATA_DICTIONARY.md
|   |-- DATABASE_SCHEMA.md
|   |-- METRIC_DEFINITIONS.md
|   |-- BUSINESS_RULES.md
|   |-- ARCHITECTURE.md
|   |-- VALIDATION_REPORT.md
|   |-- ASSUMPTIONS_AND_LIMITATIONS.md
|-- scripts/                # Reproducibility verification and cache pre-warming scripts
|   |-- reproduce.py        # Dual-run bitwise reproducibility verification harness
|   |-- populate_caches.py  # Cache pre-warming utility
|-- walkthrough5.md         # Comprehensive end-to-end implementation and verification walkthrough
|-- AI_USAGE.md             # Transparent AI disclosure, engineering review, and corrections log
|-- prompt-history/         # Verifiable chronological prompt log (prompts.jsonl)
```

---

## 6. Technology Stack

- **Backend Framework**: Python 3.11, [FastAPI](https://fastapi.tiangolo.com/) (REST APIs, dependency injection, OpenAPI / Swagger documentation).
- **ORM & Database**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/) declarative mapping, [SQLite 3](https://www.sqlite.org/) in Write-Ahead Logging (`WAL`) mode with `PRAGMA foreign_keys = ON;`, `PRAGMA busy_timeout = 30000;`, and covering composite indexes.
- **Data Validation & Schemas**: [Pydantic v2](https://docs.pydantic.dev/) request and response validation models.
- **Frontend Framework**: [React 18](https://react.dev/), [TypeScript](https://www.typescriptlang.org/), [Vite 5](https://vitejs.dev/) build tool.
- **Styling & Visualization**: [Tailwind CSS 3](https://tailwindcss.com/), [Recharts](https://recharts.org/) charting library, [Lucide React](https://lucide.dev/) icons.
- **Testing & Quality Assurance**: [Pytest](https://docs.pytest.org/) (205 tests across 17 modules), TestClient (`httpx`).
- **Reproducibility**: Standard library cryptographic utilities (`hashlib.sha256`, `random.Random` with seed `20261022`).

---

## 7. Data Model & Core Business Logic

### 7.1 Relational Data Model (13 Normalized Entities)

The platform is built on 13 normalized relational tables:
1. `instructors`: Course author and instructor profiles.
2. `learners`: Student identities, regional metadata, and source IANA timezones.
3. `courses`: Course definitions, difficulty levels, and curricular categories.
4. `cohorts`: Cohort groupings with start and target completion dates.
5. `enrollments`: Student-to-course pairings with lifecycle states (`ACTIVE`, `COMPLETED`, `DROPPED`).
6. `content_items`: Hierarchical course curriculum modules and lessons with durations.
7. `activity_events`: Student interaction stream with UTC timestamps, local dates, and idempotency keys.
8. `assessments`: Quizzes and exams with passing score criteria.
9. `attempts`: Sequentially numbered student assessment submissions and scores.
10. `completion_rules`: Governing versioned course completion criteria.
11. `course_outcomes`: Student completion evaluations with version snapshots and condition checklists.
12. `exceptions`: Operational ledger of detected data-quality anomalies.
13. `state_history`: Append-only audit trail of lifecycle status and triage transitions.

### 7.2 Two-Tier Event Deduplication
- **Tier 1 (Exact Duplicates)**: Computed via deterministic SHA-256 idempotency key:
  $$\text{SHA-256}(\text{learner\_id} \parallel \text{course\_id} \parallel \text{content\_id} \parallel \text{event\_type} \parallel \text{timestamp})$$
  The canonical original record is retained while subsequent duplicate submissions are tagged and automatically excluded from analytical engagement counts.
- **Tier 2 (Near-Duplicates)**: Multiple events from the same learner on the same content with the same event type occurring within $\le 5.0$ seconds. These represent candidate rapid-fire retries; they are flagged for inspection but are **not** automatically censored from analytics without human review.

### 7.3 Timezone Handling
- All occurrence timestamps are persisted in canonical UTC (`event_timestamp_utc`).
- Student device calendar dates (`event_date`) are evaluated against the derived local calendar date using the student's registered IANA timezone (`DATE(timezone_convert(event_timestamp_utc, source_timezone))`).
- Events crossing midnight in local time are verified consistent and not erroneously flagged as anomalies.

### 7.4 Explainable Completion Decision Engine
- Evaluates student progress against three rules:
  1. Content Completion Percentage $\ge \text{minimum\_content\_completion\_percentage}$.
  2. Final Assessment Score $\ge \text{minimum\_assessment\_score}$.
  3. All Mandatory Assessments Completed (if required by rule).
- When rules change, new outcome records are inserted with incremented `outcome_version`, referencing `supersedes_outcome_id` and updating `is_current = 1`, while historical snapshots remain preserved for auditing.

### 7.5 Engagement Metric Definitions (WALER vs WAEER)
To eliminate mathematical anomalies and avoid dividing dissimilar entities:
- **WALER (Weekly Active Learner Engagement Rate)**:
  $$\text{WALER}(w) = \frac{\text{Distinct Active Eligible Learners with } \ge 1 \text{ event in window } w}{\text{Distinct Eligible Learners in window } w} \times 100$$
- **WAEER (Weekly Active Enrollment Engagement Rate)**:
  $$\text{WAEER}(w) = \frac{\text{Distinct Active Eligible Enrollments with } \ge 1 \text{ event in window } w}{\text{Distinct Eligible Enrollments in window } w} \times 100$$
- **Point-in-Time Historical Eligibility**: Denominators for historical weeks are evaluated using immutable event-time lifecycle milestones (`l.registration_date <= window_end`, `en.enrolled_at <= window_end`, `en.dropped_at >= window_start`, `en.completed_at >= window_start`). Learners who graduated or dropped in later weeks are preserved in earlier weekly denominators, eliminating survivorship bias.

---

## 8. Security & Demo Roles

Cohortly implements Role-Based Access Control (RBAC) across 27 canonical API operations:

| Role Name | Scope & Permissions | Key Restrictions |
|---|---|---|
| `PLATFORM_ADMIN` | Full superuser access across all 27 operations. | None. |
| `ACADEMIC_ADMIN` | Platform analytics, cohorts, curriculum, audit, and benchmark reports. | Cannot trigger synthetic data generation or raw database reset. |
| `INSTRUCTOR` | Courses, curriculum, student progress, analytics, and exception triage. | Cannot view cross-platform financial/administrative audit reports. |
| `SUPPORT_STAFF` | Learners directory, activity streams, exception triage, and learner assistance. | Cannot modify completion rules or view executive cohort benchmarks. |
| `LEARNER` | Self-service access to own profile (`/api/learners/{id}`) and activity (`/api/learners/{id}/activity`). | **Strictly restricted**: Cannot access other learners' profiles, view the learners roster, access exceptions triage, or view data generator routes. Changing ID in URL returns **HTTP 403 Forbidden**. |

### Critical Security & Demo Disclaimer
> [!IMPORTANT]
> **Evaluation Demo Authentication Boundary**: The `X-Demo-Role` and `X-Demo-Learner-Id` HTTP headers are client-controlled demo headers provided strictly for evaluation convenience and local UI role switching. They do not constitute cryptographically secure or production-grade authentication. In an enterprise deployment, user identity, permissions, and learner scopes must be derived exclusively from server-verified JSON Web Tokens (JWT) or OpenID Connect (OIDC) claims issued by an institutional identity provider.

---

## 9. Dataset Generation & Reproducibility

Cohortly includes a deterministic data generation engine ([`backend/app/generators/generate.py`](backend/app/generators/generate.py)) and reproducibility verification harness ([`scripts/reproduce.py`](scripts/reproduce.py)).

### 9.1 Dataset Profiles

| Dimension | Starter Profile | Full-Scale Synthetic Benchmark Profile |
|---|---|---|
| **Intended Use** | Fast local development, quick testing, CI/CD | Full-scale performance benchmark & integrity audit |
| **Learners** | 200 | 20,000 |
| **Instructors** | 20 | 200 |
| **Courses** | 20 | 500 |
| **Cohorts** | 10 | 50 |
| **Enrollments** | 500 | 100,000 |
| **Content Items** | 240 | 6,000 |
| **Activity Events** | 10,007 (10k valid + 7 injected) | 2,000,007 (2M valid + 7 injected) |
| **Assessments** | 40 | 1,000 |
| **Assessment Attempts** | 640 | 127,610 |
| **Completion Rules** | 20 | 500 |
| **Course Outcomes** | 501 (500 valid + 1 premature) | 100,001 (100k valid + 1 premature) |
| **Exceptions** | 8 | 8 |
| **State History Records** | 671 (baseline) | 132,824 (132,794 baseline + 30 test triage audit records) |
| **Total Database Rows** | **12,857** | **2,488,700** |
| **Database Size on Disk** | **~10 MB** | **1,899,036,672 bytes (~1.899 GB)** |
| **Generation Runtime** | **~2 seconds** | **~2,066 seconds (~34.4 minutes)** |

### 9.2 Generating the Dataset

To generate the Starter profile:
```bash
python -m backend.app.generators.generate --profile starter --seed 20261022
```

To generate the Full-scale benchmark profile:
```bash
python -m backend.app.generators.generate --profile full --seed 20261022
```

### 9.3 Cryptographic Reproducibility Verification

Run the automated dual-generation reproducibility harness:
```bash
python scripts/reproduce.py --profile starter --seed 20261022
```

The script performs two independent generation runs (`Run A` vs `Run B`) into isolated SQLite databases and verifies that all 13 relational tables produce bit-for-bit identical SHA-256 table digests.

### 9.4 Decoupled Anomaly Evaluation Benchmark

The anomaly benchmark evaluates detection rules against **8 deliberately injected synthetic anomalies** recorded in the quarantined ground-truth ledger (`data/ground_truth/anomalies.json`):
- 5 `DUPLICATE_ACTIVITY_EVENT`
- 1 `UNENROLLED_LEARNER_ACTIVITY`
- 1 `PREMATURE_COMPLETION`
- 1 `TIMEZONE_DATE_MISMATCH`

Results against the 8 injected benchmark cases:
- **Precision**: 100.0% (8 / 8)
- **Recall**: 100.0% (8 / 8)
- **F1 Score**: 1.0000

*(Note: This benchmark quantitatively validates detection rule isolation against known injected synthetic anomalies; it does not represent detection performance over unconstrained, noisy production LMS telemetry).*

---

## 10. Installation & Setup

### Prerequisites
- **Python**: Version 3.11+ (tested on Python 3.11.7)
- **Node.js**: Version 18+ (tested on Node.js v22.17.0)
- **npm**: Version 9+ (tested on npm 10.9.2)

### Step 1: Clone Repository & Setup Virtual Environment

Run from the project root directory:

```bash
# Clone repository
git clone https://github.com/<your-username>/Cohortly.git
cd Cohortly

# Create and activate Python virtual environment
# Windows:
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux:
python3 -m venv venv
source venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt
```

### Step 2: Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

---

## 11. Running the Application

### Option A: Quick Start with Starter Dataset

```bash
# 1. Generate starter dataset (runs in ~2 seconds)
python -m backend.app.generators.generate --profile starter --seed 20261022

# 2. Start backend API server (runs on port 8000)
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

In a separate terminal:
```bash
# 3. Start frontend development server (runs on port 5173)
cd frontend
npm run dev
```

### Option B: Running with Pre-Generated Full-Scale Dataset

If `data/generated/cohortly.db` is already present (1.899 GB), simply launch the backend and frontend servers without re-running data generation:
```bash
# Terminal 1: Backend
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

### Service Endpoints
- **Web Interface**: `http://localhost:5173`
- **Interactive Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc Documentation**: `http://127.0.0.1:8000/redoc`
- **Health Diagnostic Endpoint**: `http://127.0.0.1:8000/api/health`

---

## 12. API Documentation

Key API router prefixes available on `http://127.0.0.1:8000`:

| Router | Prefix | Key Endpoints | Description |
|---|---|---|---|
| **Dashboard** | `/api/dashboard` | `GET /overview`<br>`GET /engagement-trend`<br>`GET /completion-trend` | Platform KPIs, 8-week WALER/WAEER trends, cohort graduation rates. |
| **Learners** | `/api/learners` | `GET /`<br>`GET /{id}`<br>`GET /{id}/activity` | Learner directory, profile drawer, transparent outcome checklist, activity timeline. |
| **Courses** | `/api/courses` | `GET /`<br>`GET /{id}`<br>`GET /{id}/analytics` | 500-course catalog (page size 50), curriculum hierarchy tree, completion rules, drop-off funnel. |
| **Cohorts** | `/api/cohorts` | `GET /`<br>`GET /{id}`<br>`GET /compare` | Cohort cards, retention curves, multi-cohort comparison. |
| **Assessments** | `/api/assessments` | `GET /`<br>`GET /{id}`<br>`GET /{id}/analytics` | Assessment inventory, score distributions, pass/fail ratios. |
| **Analytics** | `/api/analytics` | `GET /engagement`<br>`GET /content-usage`<br>`GET /completion` | Module-level engagement, video drop-off rates, device breakdown. |
| **Exceptions** | `/api/exceptions` | `GET /`<br>`GET /{id}`<br>`PATCH /{id}/status` | Anomaly ledger, evidence payloads, status triage updates. |
| **Data** | `/api/data` | `GET /status`<br>`GET /validation`<br>`GET /manifest`<br>`GET /benchmark`<br>`GET /export` | Generation status, 15-point validation report, SHA-256 manifests, benchmark evaluation, streaming exports. |
| **System** | `/api` | `GET /health` | System health check and connectivity diagnostic. |

---

## 13. Automated Testing

Cohortly includes 205 automated tests across 17 test modules:

```bash
# Run complete Pytest test suite
pytest backend/tests/ -v

# Run specific RBAC verification suite
pytest backend/tests/test_role_rbac_comprehensive.py -v

# Run frontend build verification (TypeScript + Vite)
cd frontend
npm run build
cd ..
```

### Test Suite Execution Runtimes
- **Initial Baseline Full Run**: 205 passed in **313.66s**.
- **Authoritative Final Verification & Regression Run**: 205 passed in **341.45s** (0:05:41) with 0 failures, executed after implementing course ID deterministic sorting and catalog pagination.
- **Frontend Production Build**: Clean build in **13.53s** (`tsc && vite build`, 0 errors).

---

## 14. Documentation Index

Detailed architectural, schema, and governance documentation:

- [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md): Complete data dictionary covering all 13 relational tables and 70+ columns.
- [`docs/DATABASE_SCHEMA.md`](docs/DATABASE_SCHEMA.md): DDL schema, foreign key cascade behaviors, composite B-Tree indexes, and SQLite PRAGMA tuning.
- [`docs/METRIC_DEFINITIONS.md`](docs/METRIC_DEFINITIONS.md): Mathematical formulations for WAL, WALER, WAEER, and graduation rates.
- [`docs/BUSINESS_RULES.md`](docs/BUSINESS_RULES.md): Governing completion rules, two-tier deduplication, and anomaly detection rules.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): Architectural design, caching strategies, and RBAC matrix.
- [`docs/VALIDATION_REPORT.md`](docs/VALIDATION_REPORT.md): 15-point validation report, cryptographic SHA-256 digests, and benchmark scorecard.
- [`docs/ASSUMPTIONS_AND_LIMITATIONS.md`](docs/ASSUMPTIONS_AND_LIMITATIONS.md): Documented edge cases, design decisions, and demo boundaries.
- [`walkthrough5.md`](walkthrough5.md): Comprehensive end-to-end implementation and full-scale production verification walkthrough.
- [`AI_USAGE.md`](AI_USAGE.md): Transparent disclosure of AI assistance, human engineering review, and corrections log.
- [`prompt-history/prompts.jsonl`](prompt-history/prompts.jsonl): Chronological log of engineering prompts.

---

## 15. Limitations & Future Improvements

1. **Database Engine Concurrency**:
   - SQLite WAL mode with 30-second busy timeout and connection recycling handles multi-threaded concurrent reads efficiently across 24 workers. However, SQLite remains fundamentally a single-writer architecture. For high-throughput multi-tenant production environments, transitioning to PostgreSQL with horizontal read replicas is recommended.
2. **Authentication Boundary**:
   - The current `X-Demo-Role` and `X-Demo-Learner-Id` header-based switching is designed strictly for local evaluation ergonomics. Enterprise deployments must implement cryptographically signed JWT/OIDC authentication with OAuth 2.0 institutional identity providers.
3. **Decoupled Anomaly Evaluation Scope**:
   - The 100% precision and recall scores were obtained against 8 deliberately injected synthetic benchmark anomalies in the test harness. Real-world LMS telemetry exhibits more complex, unconstrained error patterns requiring continuous validation and human-in-the-loop review.
4. **Synthetic Data versus Organic Telemetry**:
   - While the synthetic generation engine incorporates realistic Poisson and Gaussian distributions for session durations, assessment scores, and drop-off rates, real-world learner behavior includes unstructured interactions (discussion forums, real-time chats, peer reviews) not captured in this benchmark schema.

---

## 16. AI Usage Disclosure

In compliance with challenge requirements, AI assistance (Google DeepMind Antigravity / Gemini) was utilized during the development of this project for boilerplate generation, scaffolding, schema declarations, and initial draft documentation. 

Every AI-assisted output was subjected to rigorous human engineering review, static analysis, and verification. Critical flaws in early AI proposals—such as timezone date-rollover misclassifications, single-tier deduplication data loss risks, unique constraints that destroyed completion history, and asymmetric WALER definitions—were manually identified, redesigned, and corrected.

For a detailed breakdown of human engineering corrections versus AI generation, refer to [`AI_USAGE.md`](AI_USAGE.md). The chronological prompt record is preserved in [`prompt-history/prompts.jsonl`](prompt-history/prompts.jsonl).
