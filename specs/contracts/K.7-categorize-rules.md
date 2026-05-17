---
id: K.7
title: assign category via rule engine
layer: contracts
kind: spec
parents: [C.10]
peers_depends_on: [K.6]
verdict:
  mechanism: llm_judge
  status: unknown
contract:
  version: 0.1.0
  locked: false
  field_anchors: [signature, behaviour]
---

# K.7 — assign category via rule engine

## signature

- input: a Transaction (with `merchant` already canonicalized by K.6)
- output: category name (e.g. `"Coffee/Tea"`, `"Groceries"`)

## behaviour

- Reads rules from `config/categories.yaml` via `src/ledgerloom/config.py`.
- Rules support merchant-exact, merchant-prefix, and regex matching.
- Unmatched transactions get category `"Uncategorized"` and surface in `/categorize`.
