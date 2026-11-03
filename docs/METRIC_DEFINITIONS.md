# Cohortly – Metric Definitions & Mathematical Formulations

This document specifies the exact mathematical formulas, inclusion rules, exclusion filters, edge-case handlings, and boundary conditions for all metrics computed across **Cohortly**.

---

## 1. Weekly Reporting Interval Definition

All standard weekly metrics in Cohortly are anchored to ISO-8601 calendar weeks normalized to UTC:
- **Interval**: Monday 00:00:00.000 UTC through Sunday 23:59:59.999 UTC ($[W_{\text{start}}, W_{\text{end}}]$).
- **Timezone Invariant**: Regardless of the learner's local timezone, events are assigned to week $W$ based strictly on their `event_timestamp_utc`. Local timezone dates (`event_date`) are preserved for comparative cross-timezone analysis.

---

## 2. Event Eligibility & Deduplication Classes

Let $\mathcal{E}$ be the set of all activity events in the ledger.
1. **Valid Engagement Types ($\mathcal{T}_{\text{eng}}$)**:
   $$\mathcal{T}_{\text{eng}} = \{ \text{COURSE\_OPENED}, \text{CONTENT\_VIEWED}, \text{VIDEO\_PROGRESS}, \text{VIDEO\_COMPLETED}, \text{DOCUMENT\_DOWNLOADED}, \text{QUIZ\_SUBMITTED}, \text{COURSE\_COMPLETED} \}$$
   *(Note: Raw `LOGIN`, `QUIZ_STARTED`, and `VIDEO_STARTED` indicate session initialization rather than substantive learning engagement).*
2. **Canonical Deduplicated Events ($\mathcal{E}_{\text{canon}}$)**:
   For any subset of events sharing the exact same `idempotency_key`, only the event with the earliest `ingestion_timestamp` (or lowest `event_id` in case of ties) belongs to $\mathcal{E}_{\text{canon}}$. All other identical rows are flagged as exact duplicates.
3. **Eligible Enrolled Events ($\mathcal{E}_{\text{valid}}(W)$)**:
   $$\mathcal{E}_{\text{valid}}(W) = \{ e \in \mathcal{E}_{\text{canon}} \mid e.\text{event\_type} \in \mathcal{T}_{\text{eng}} \land e.\text{event\_timestamp\_utc} \in [W_{\text{start}}, W_{\text{end}}] \land e.\text{enrollment\_id IS NOT NULL} \}$$
   *(Explicitly excludes unenrolled activity anomalies, exact duplicates, and non-engagement events).*

---

## 3. Weekly Engagement Metrics

### A. Weekly Active Learners (WAL)
Distinct learners who performed at least one valid, deduplicated engagement event linked to an active enrollment during reporting week $W$.

$$\text{WAL}_W = \left| \{ l \in \text{Learners} \mid \exists e \in \mathcal{E}_{\text{valid}}(W) \text{ s.t. } e.\text{learner\_id} = l \} \right|$$

### B. Weekly Active Learner Engagement Rate (WALER)
Measures the percentage of eligible learners who were actively engaged during week $W$.
- **Denominator (Eligible Enrolled Learners)**: Distinct learners holding at least one enrollment that was active during week $W$:
  $$\mathcal{L}_{\text{elig}}(W) = \{ l \in \text{Learners} \mid \exists enr \in \text{Enrollments} \text{ s.t. } enr.\text{learner\_id} = l \land enr.\text{enrolled\_at} \le W_{\text{end}} \land (enr.\text{completed\_at IS NULL} \lor enr.\text{completed\_at} \ge W_{\text{start}}) \land (enr.\text{dropped\_at IS NULL} \lor enr.\text{dropped\_at} \ge W_{\text{start}}) \land enr.\text{enrollment\_status} \in (\text{'ACTIVE'}, \text{'COMPLETED'}) \}$$
- **Formula**:
  $$\text{WALER}_W = \begin{cases} \dfrac{\text{WAL}_W}{|\mathcal{L}_{\text{elig}}(W)|} \times 100, & \text{if } |\mathcal{L}_{\text{elig}}(W)| > 0 \\ 0.0, & \text{otherwise} \end{cases}$$

### C. Weekly Active Enrollment Engagement Rate (WAEER)
Measures the engagement rate at the enrollment level (distinguishing students who take multiple simultaneous courses).
- **Numerator (Weekly Active Enrollments)**:
  $$\text{WAE}_W = \left| \{ enr\_id \mid \exists e \in \mathcal{E}_{\text{valid}}(W) \text{ s.t. } e.\text{enrollment\_id} = enr\_id \} \right|$$
- **Denominator (Total Eligible Enrollments)**:
  $$\mathcal{R}_{\text{elig}}(W) = \{ enr \in \text{Enrollments} \mid enr.\text{enrolled\_at} \le W_{\text{end}} \land (enr.\text{completed\_at IS NULL} \lor enr.\text{completed\_at} \ge W_{\text{start}}) \land (enr.\text{dropped\_at IS NULL} \lor enr.\text{dropped\_at} \ge W_{\text{start}}) \land enr.\text{enrollment\_status} \in (\text{'ACTIVE'}, \text{'COMPLETED'}) \}$$
- **Formula**:
  $$\text{WAEER}_W = \begin{cases} \dfrac{\text{WAE}_W}{|\mathcal{R}_{\text{elig}}(W)|} \times 100, & \text{if } |\mathcal{R}_{\text{elig}}(W)| > 0 \\ 0.0, & \text{otherwise} \end{cases}$$

---

## 4. Course Progress & Completion Metrics

### A. Content Completion Percentage
For enrollment $e$ in course $C$:
Let $\mathcal{C}_{\text{req}}(C) = \{ c \in \text{content\_items} \mid c.\text{course\_id} = C \land c.\text{is\_required} = 1 \}$.
Let $\mathcal{C}_{\text{done}}(e) = \{ c \in \mathcal{C}_{\text{req}}(C) \mid \exists \text{ valid event on } c \text{ with status completed} \}$.

$$\text{ContentCompletion}(e) = \begin{cases} \dfrac{|\mathcal{C}_{\text{done}}(e)|}{|\mathcal{C}_{\text{req}}(C)|} \times 100, & \text{if } |\mathcal{C}_{\text{req}}(C)| > 0 \\ 100.0, & \text{otherwise} \end{cases}$$

### B. Assessment Progress Percentage
For enrollment $e$ in course $C$:
Let $\mathcal{A}_{\text{req}}(C) = \{ a \in \text{assessments} \mid a.\text{course\_id} = C \land a.\text{is\_required} = 1 \}$.
Let $\mathcal{A}_{\text{att}}(e) = \{ a \in \mathcal{A}_{\text{req}}(C) \mid \exists \text{ attempt with status } \in (\text{'SUBMITTED'}, \text{'GRADED'}, \text{'PASSED'}, \text{'FAILED'}) \}$.

$$\text{AssessmentProgress}(e) = \begin{cases} \dfrac{|\mathcal{A}_{\text{att}}(e)|}{|\mathcal{A}_{\text{req}}(C)|} \times 100, & \text{if } |\mathcal{A}_{\text{req}}(C)| > 0 \\ 100.0, & \text{otherwise} \end{cases}$$

### C. Assessment Pass Rate Percentage
For assessment $A$ or course $C$:
$$\text{AssessmentPassRate} = \dfrac{\text{Count of Attempts with } \text{score} \ge \text{passing\_score}}{\text{Total Graded Attempts}} \times 100$$

### D. Course Completion Rate
For course $C$ or cohort $K$:
$$\text{CourseCompletionRate} = \dfrac{\text{Enrollments with current outcome } \text{completion\_status} = \text{'COMPLETED'}}{\text{Total Eligible Enrollments in } C \text{ or } K} \times 100$$

---

## 5. Inactive Learners Metric

- **Inactivity Period**: 14 consecutive calendar days ($\Delta t = 14\text{ days}$).
- **Anchor Reference**: Evaluated relative to the system reference clock ($T_{\text{ref}}$).
- **Condition**: An active enrollment ($enr.\text{enrollment\_status} = \text{'ACTIVE'}$) is categorized as **Inactive / At-Risk** if:
  $$\max(\{ e.\text{event\_timestamp\_utc} \mid e \in \mathcal{E}_{\text{valid}} \land e.\text{enrollment\_id} = enr.\text{enrollment\_id} \} \cup \{ enr.\text{enrolled\_at} \}) < T_{\text{ref}} - 14\text{ days}$$

---

## 6. Deduplication Accounting Metrics

Exposed via `/api/dashboard/overview` and `/api/analytics/engagement`:
1. **`raw_event_count`**: Total records in table `activity_events`.
2. **`exact_duplicate_count`**: Total records matching an existing `idempotency_key` beyond the canonical record.
3. **`potential_near_duplicate_count`**: Total records sharing `(learner_id, course_id, content_id, event_type, session_id)` within $\le 5$ seconds.
4. **`unique_engagement_event_count`**: Count of canonical records belonging to $\mathcal{T}_{\text{eng}}$.
5. **`deduplicated_engagement_count`**: Final event count utilized for active engagement rate calculations.

---

## 7. UTC vs Local Timezone Aggregation Differences

- **UTC Aggregation**: Standard across Cohortly for institutional consistency across multi-region cohorts.
- **Local Date Aggregation**: Aggregates by `event_date` (`DATE(convert_tz(timestamp_utc, source_timezone))`).
- **Boundary Shift Demonstration**:
  - Event at `2026-09-06T23:30:00Z` from Tokyo (`Asia/Tokyo`, UTC+9) has local time `2026-09-07T08:30:00`.
  - In UTC, this falls on Sunday (Week 36).
  - In local Tokyo time, this falls on Monday (Week 37).
  - Cohortly's Analytics service exposes this variance to explain reporting reconciliation differences across global enterprise clients.
