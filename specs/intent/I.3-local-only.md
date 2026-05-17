---
id: I.3
title: Local-only — financial data never leaves the machine
layer: intent
kind: constraint
parents: []
peers_depends_on: []
applies_to:
  layer: realizations
  filter: ""
verdict:
  mechanism: automated_check
  check: "! grep -rE '^import (boto3|googleapiclient|azure|google\\.cloud)' src/ 2>/dev/null"
  status: unknown
  evidence_ref: ""
---

# I.3 — Local-only

## why

Bank statements, salary data, debt levels, and merchant patterns are among the most sensitive data a person owns. Routing them through a SaaS finance app means trusting that vendor's security, their breach-notification timing, and their staff's discretion forever. The project exists in part because that trust is unwarranted.

## constraint

No Python module under `src/` may import a cloud SDK (`boto3`, `googleapiclient`, `azure`, `google.cloud`). Network I/O for the analysis pipeline is forbidden. (Claude Code itself talks to Anthropic — that's outside this constraint's scope; this rule is about the project's own code.)

## verification

The verdict check `grep`s for cloud SDK imports under `src/`. An import inside a `try/except ImportError` is over-flagged but the check is conservative on purpose.
