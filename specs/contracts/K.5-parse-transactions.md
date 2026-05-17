---
id: K.5
title: parse extracted text into transaction rows
layer: contracts
kind: spec
parents: [C.10]
peers_depends_on: [K.4]
verdict:
  mechanism: llm_judge
  status: unknown
contract:
  version: 0.1.0
  locked: false
  field_anchors: [signature, behaviour, non_goals]
---

# K.5 — parse extracted text into transaction rows

## signature

- input: text (from K.4) OR CSV content; source identifier (e.g. "rbc", "amex", "splitwise")
- output: list of canonical Transaction dicts: `{date, amount, raw_merchant, source, account}`

## behaviour

- Dispatches to `src/ledgerloom/parsers/<source>.py` based on the source identifier.
- Each parser exposes a `parse(text_or_csv) -> list[Transaction]` function.
- Canonical Transaction schema is the same regardless of source — diversity is absorbed at this boundary.

## non_goals

- Does not canonicalize merchant names (that's K.6).
- Does not categorize (that's K.7).
- Does not write to the database (that's K.8).
