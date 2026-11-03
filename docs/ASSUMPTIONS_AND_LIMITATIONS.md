# Cohortly – Assumptions & Limitations

This document explicitly enumerates the domain assumptions, modeling choices, edge-case handlings, and deliberate system limitations implemented in **Cohortly**.

---

## 1. Domain & Modeling Assumptions

1. **Fixed Synthetic Reference Clock**:
   - All synthetic datasets and relative timelines are anchored to `2026-10-22T00:00:00Z`.
   - Business timestamps in database tables are deterministic offsets from this anchor to guarantee reproducibility across independent runs.
2. **Weekly Reporting Window**:
   - Reporting weeks are defined strictly as Monday 00:00:00 UTC through Sunday 23:59:59 UTC.
   - For learners operating in disparate timezones, events are attributed to reporting weeks based on UTC occurrence, preventing boundary drift when comparing regional cohorts.
3. **Inactivity Threshold**:
   - Inactive learners are defined as active enrollments with no valid engagement event for $\ge 14$ consecutive days prior to the anchor date.
4. **Graduation Rule Precedence**:
   - A course completion rule is effective if the calculation date falls within `[effective_from, effective_to]`. If multiple versions overlap, the highest `rule_version` takes precedence.
5. **Post-Completion Review**:
   - Activity events occurring after an enrollment's `completed_at` are treated as legitimate review activity (e.g. revisiting a reference article). They are tracked in content usage analytics but do not retroactively alter the course completion criteria.
6. **Append-Only State History**:
   - Lifecycle mutations on enrollments and exceptions must create immutable audit records in `state_history`. Previous states are never modified or purged.

---

## 2. Technical Limitations & Demo Boundaries

1. **Local SQLite Engine**:
   - The platform uses SQLite with WAL mode and memory cache pragmas. While benchmarked to handle 2,000,000 events locally, high-concurrency production deployments would transition to PostgreSQL or Amazon Aurora.
2. **Demo Role Context & Security Limitations**:
   - Role switching is powered by client-side toggling and server-side `X-Demo-Role` header validation for demonstration simplicity.
   - It does **not** provide cryptographic signature verification, password hashing, session tokens, or token revocation. Production deployment would integrate enterprise OAuth2 / OpenID Connect (OIDC) JWT tokens.
3. **Near-Duplicate Analytics Inclusion Policy**:
   - Exact duplicates (matching `idempotency_key`) are automatically excluded from engagement metrics.
   - Near-duplicates ($\le 5.0\text{s}$ delta) are flagged as candidates in the Exceptions ledger for investigator review, but **are NOT automatically excluded** from engagement calculations to avoid undercounting legitimate rapid interactions.
4. **Ground-Truth Isolation**:
   - Ground truth anomaly labels are isolated from the operational runtime. Precision and recall metrics are accessible exclusively through the validation benchmark view.
5. **Standardized 15-Point Cross-Entity Validation**:
   - System integrity is audited against a strictly defined 15-point validation suite (CHK-01 through CHK-15) covering relational integrity, lifecycle ordering, score ranges, deduplication, timezone alignment, and cross-entity course consistency.

