---
id: C.4
title: /analyze — comprehensive spending analysis
layer: capabilities
kind: spec
parents: [I.1]
peers_depends_on: [C.10]
verdict:
  mechanism: llm_judge
  status: unknown
contract:
  version: 0.1.0
  locked: false
  field_anchors: [summary]
---

# C.4 — /analyze

## summary

Comprehensive spending breakdown by category, merchant, and time window. Surfaces leaks (subscriptions you forgot, small recurring charges, category drift). Behavioral framing is the default voice — the report is written to a reader who wants to act, not just see numbers.
