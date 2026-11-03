# Cohortly – AI Prompt History & Audit Ledger

This directory maintains an immutable, chronological record of every prompt submitted during the engineering and development of **Cohortly: Learning Analytics & Cohort Intelligence Platform**.

## Ledger Files

- [`prompts.jsonl`](file:///c:/Users/manda/FusionProjects/Cohortly/prompt-history/prompts.jsonl): Machine-readable JSONL ledger of prompts with metadata, files affected, engineering review, manual modifications, and validation steps.
- [`../AI_USAGE.md`](file:///c:/Users/manda/FusionProjects/Cohortly/AI_USAGE.md): Narrative disclosure of AI acceleration, architecture decisions, corrections made, and human oversight.

## Log Schema

Each entry in `prompts.jsonl` adheres to the following specification:
```json
{
  "prompt_number": 1,
  "timestamp": "2026-11-03T12:12:01+05:30",
  "ai_tool": "Antigravity (Gemini 3.8 Flash)",
  "prompt_text": "...",
  "purpose": "...",
  "features_affected": ["..."],
  "engineer_review": "...",
  "modifications_made": "...",
  "validation_method": "..."
}
```
