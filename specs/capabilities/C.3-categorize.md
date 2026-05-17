---
id: C.3
title: /categorize — label uncategorized merchants
layer: capabilities
kind: spec
parents: [I.2]
peers_depends_on: [C.10]
verdict:
  mechanism: llm_judge
  status: unknown
contract:
  version: 0.1.0
  locked: false
  field_anchors: [summary, interface]
---

# C.3 — /categorize

## summary

Walk uncategorized merchants from the SQLite db, propose canonical names + categories, write `config/merchants.yaml` and (where rules emerge) `config/categories.yaml`.

## interface

- `/categorize` — invokes the slash command. Shows uncategorized merchants in order of total spend so the highest-impact labeling happens first.
