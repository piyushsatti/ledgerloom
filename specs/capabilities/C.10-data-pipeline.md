---
id: C.10
title: data pipeline — extract → parse → normalize → categorize → ingest
layer: capabilities
kind: spec
parents: [I.2]
peers_depends_on: []
verdict:
  mechanism: llm_judge
  judge_prompt: "Does build_db.py orchestrate the documented pipeline correctly, and does each stage have a corresponding module under src/ledgerloom/?"
  status: unknown
contract:
  version: 0.1.0
  locked: false
  field_anchors: [summary, stages, non_goals]
---

# C.10 — data pipeline

## summary

The backbone capability that turns raw statement files into queryable SQLite rows. Every analysis command (C.4–C.8) depends on this. Adding a bank (`/parser`) extends it; relabeling merchants (`/categorize`) feeds it.

## stages

1. **extract** — PDF → text via `pdftotext`, cached by SHA-256 under `cache/extracted/`.
2. **parse** — text → transactions, dispatched per-bank via `src/ledgerloom/parsers/<bank>.py`.
3. **normalize** — raw merchant strings → canonical names via `config/merchants.yaml`.
4. **categorize** — transactions → categories via `config/categories.yaml` rule engine.
5. **ingest** — atomic insert into `ledgerloom.db` (SQLite); idempotent on re-runs.

Orchestrated by `build_db.py` at the repo root.

## non_goals

- Does NOT expose a live query API at runtime; analysis commands read directly from the SQLite db via `src/ledgerloom/queries.py`.
- Does NOT auto-detect new banks; that's `/parser`'s job.
