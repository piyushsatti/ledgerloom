---
id: K.3
title: initial /analyze handoff after onboarding
layer: contracts
kind: spec
parents: [C.1]
peers_depends_on: [K.2]
verdict:
  mechanism: llm_judge
  status: unknown
contract:
  version: 0.1.0
  locked: false
  field_anchors: [signature, behaviour]
---

# K.3 — initial /analyze handoff after onboarding

## signature

- input: a freshly-written `config/user_config.yaml`
- output: an analysis transcript shown to the user

## behaviour

- After `K.2` succeeds, prompts the user to drop their statement files into the `data/<source>/` paths declared by the new config.
- Suggests running `uv run python build_db.py` to populate `ledgerloom.db`.
- Then runs the equivalent of `/analyze` (or hands off to `C.4`) to produce the first analysis.
- Does not block onboarding completion if statement files aren't yet present — onboarding is "configured", analysis is "data-dependent".
