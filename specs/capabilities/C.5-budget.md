---
id: C.5
title: /budget — three-tier budget with savings projections
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

# C.5 — /budget

## summary

Generates three budget tiers — Strict, Semi-Strict, Lenient — each with monthly category caps and projected savings over 6/12/24 months. Tiers are derived from the user's actual spending patterns, not generic envelopes.
