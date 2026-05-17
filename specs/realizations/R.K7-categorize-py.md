---
id: R.K7
title: src/ledgerloom/categorize.py
layer: realizations
kind: spec
parents: [K.7]
peers_depends_on: []
verdict:
  mechanism: automated_check
  check: "test -f src/ledgerloom/categorize.py && grep -q 'categories' src/ledgerloom/categorize.py"
  status: unknown
---

# R.K7 — src/ledgerloom/categorize.py

## artifacts

- `src/ledgerloom/categorize.py` — applies rules from `config/categories.yaml` against canonicalized transactions.

## verification

File exists and references the `categories` config it consumes.
