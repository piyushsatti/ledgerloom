---
id: R.K5
title: src/ledgerloom/parsers/
layer: realizations
kind: spec
parents: [K.5]
peers_depends_on: []
verdict:
  mechanism: automated_check
  check: "test -d src/ledgerloom/parsers && test -f src/ledgerloom/parsers/__init__.py && ls src/ledgerloom/parsers/ | grep -E '\\.py$' | grep -v __init__ | head -1 | grep -q ."
  status: unknown
---

# R.K5 — src/ledgerloom/parsers/

## artifacts

- `src/ledgerloom/parsers/__init__.py` — dispatch table from source name to parser module.
- `src/ledgerloom/parsers/<bank>.py` — per-bank `parse()` entry points (rbc.py, rbc_credit.py, amex.py, splitwise.py).

## verification

The check confirms the directory exists, has an `__init__.py`, and contains at least one per-bank parser file beyond `__init__`. A new bank added by `/parser` should make this still pass.
