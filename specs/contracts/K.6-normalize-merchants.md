---
id: K.6
title: normalize raw merchant strings to canonical names
layer: contracts
kind: spec
parents: [C.10]
peers_depends_on: [K.5]
verdict:
  mechanism: llm_judge
  status: unknown
contract:
  version: 0.1.0
  locked: false
  field_anchors: [signature, behaviour]
---

# K.6 — normalize raw merchant strings to canonical names

## signature

- input: a raw merchant string (e.g. `"TIM HORTONS #1234 TORONTO ON"`)
- output: canonical merchant name (e.g. `"Tim Hortons"`)

## behaviour

- Reads canonical mapping from `config/merchants.yaml` via `src/ledgerloom/config.py`.
- Strips known noise (store numbers, city/province codes, payment processor prefixes).
- Falls back to a best-effort cleanup when no mapping exists; flags such merchants for `/categorize`.
