---
id: K.2
title: write user_config.yaml atomically
layer: contracts
kind: spec
parents: [C.1]
peers_depends_on: [K.1]
verdict:
  mechanism: llm_judge
  status: unknown
contract:
  version: 0.1.0
  locked: false
  field_anchors: [signature, behaviour, error]
---

# K.2 — write user_config.yaml atomically

## signature

- input: dict produced by K.1
- output: `config/user_config.yaml` on disk

## behaviour

- All YAML I/O routes through `src/ledgerloom/config.py` (enforced by constraint I.4).
- Atomic write: `.tmp` + rename.
- Refuses to overwrite an existing `config/user_config.yaml` without explicit confirmation.

## error

- If `config/user_config.yaml` exists and the user declines to overwrite, halts with a clear message; does not produce a partial file.
