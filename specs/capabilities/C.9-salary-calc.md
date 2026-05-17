---
id: C.9
title: /salary-calc — net pay + affordability
layer: capabilities
kind: spec
parents: [I.1]
peers_depends_on: []
verdict:
  mechanism: llm_judge
  status: unknown
contract:
  version: 0.1.0
  locked: false
  field_anchors: [summary]
---

# C.9 — /salary-calc

## summary

Jurisdiction-aware net-pay calculator (uses the tax jurisdiction set during `/onboard`). Affordability assessment: given current spending patterns, what salary delta does a contemplated move/job-change require? Read-only — does not require pipeline data, just the user's config.
