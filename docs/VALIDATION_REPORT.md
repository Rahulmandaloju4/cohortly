# Cohortly – Data Validation & Integrity Audit Report

This report records the automated validation results, cross-entity relational checks, and ground-truth benchmark metrics executed against the generated datasets of **Cohortly**.

---

## 1. Executive Summary

- **Generated Dataset Profile**: Starter (`profile=starter`, `seed=20261022`)
- **Validation Run Timestamp**: Initialized during Phase 1
- **Overall Status**: PENDING EXECUTION (Awaiting generator run in Phase 2)
- **Integrity Checks Evaluated**: 15 Checks
- **Target Ground-Truth Anomalies**: 4 Labelled Edge Cases

---

## 2. 15-Point Relational & Integrity Check Matrix

| Check ID | Category | Description | Target Criteria | Status |
|---|---|---|---|---|
| **CHK-01** | Primary Keys | Primary key uniqueness across all 11 tables | 0 duplicate keys | PENDING |
| **CHK-02** | Foreign Keys | Referential integrity across all child-parent relations | 0 orphaned records (except unenrolled anomaly) | PENDING |
| **CHK-03** | Enumerations | Valid enumeration strings across status and type columns | 0 invalid enums | PENDING |
| **CHK-04** | Non-Null Fields | Required fields populated across all rows | 0 unexpected nulls | PENDING |
| **CHK-05** | Chronology | Date ordering (`registration <= enrolled <= completed`) | 0 chronological inversions | PENDING |
| **CHK-06** | Lifecycle | Enrollments marked COMPLETED must have `completed_at` | 100% compliant | PENDING |
| **CHK-07** | Attempt Sequence | Assessment attempt numbering is strictly sequential (1, 2, ...) | 0 missing numbers | PENDING |
| **CHK-08** | Score Ranges | Assessment scores strictly within $[0.0, \text{max\_score}]$ | 0 out-of-range scores | PENDING |
| **CHK-09** | Rule Validity | Course completion rules have valid effective date windows | 100% compliant | PENDING |
| **CHK-10** | Deduplication | Exact duplicates properly isolated and canonical designated | Verified | PENDING |
| **CHK-11** | Unenrolled EVTs | Unenrolled activity correctly captured without fake enrollments | Verified | PENDING |
| **CHK-12** | Premature Compl. | Premature completions flagged against business rules | Verified | PENDING |
| **CHK-13** | Timezone Dates | Stored `event_date` matches derived IANA local date | Verified | PENDING |
| **CHK-14** | Cross-Entity | Event/Attempt/Outcome course IDs match enrollment courses | Verified | PENDING |
| **CHK-15** | Content Tree | Child content items share parent course ID | Verified | PENDING |

---

## 3. Anomaly Detection & Ground-Truth Benchmark Evaluation

*(To be computed independently by `app/eval/benchmark.py` following Phase 3 implementation)*

| Anomaly Type | Ground Truth Count | Detected Count | True Positives (TP) | False Positives (FP) | False Negatives (FN) | Precision | Recall | F1 Score |
|---|---|---|---|---|---|---|---|---|
| `DUPLICATE_ACTIVITY_EVENT` | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| `UNENROLLED_LEARNER_ACTIVITY` | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| `PREMATURE_COMPLETION` | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| `TIMEZONE_DATE_MISMATCH` | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| **Aggregate Benchmark** | **TBD** | **TBD** | **TBD** | **TBD** | **TBD** | **TBD** | **TBD** | **TBD** |

---

## 4. Fixed-Seed Reproducibility Verification

- **Fixed Seed**: `20261022`
- **Reference Clock**: `2026-10-22T00:00:00Z`
- **Reproducibility Script**: `scripts/reproduce.py`
- **Verification Status**: PENDING
