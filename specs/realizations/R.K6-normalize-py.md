---
id: R.K6
title: src/ledgerloom/normalize.py
layer: realizations
kind: spec
parents: [K.6]
peers_depends_on: []
verdict:
  mechanism: automated_check
  check: "test -f src/ledgerloom/normalize.py && grep -q 'merchants' src/ledgerloom/normalize.py"
  status: unknown
---

# R.K6 — src/ledgerloom/normalize.py

## artifacts

- `src/ledgerloom/normalize.py` — canonicalizes raw merchant strings against `config/merchants.yaml`.

## verification

The check confirms the file exists and references `merchants` somewhere (the config mapping it consumes).
