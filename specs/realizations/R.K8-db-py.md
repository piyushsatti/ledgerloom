---
id: R.K8
title: src/ledgerloom/db.py
layer: realizations
kind: spec
parents: [K.8]
peers_depends_on: []
verdict:
  mechanism: automated_check
  check: "test -f src/ledgerloom/db.py && grep -qE '(CREATE TABLE|sqlite3|transactions)' src/ledgerloom/db.py"
  status: unknown
---

# R.K8 — src/ledgerloom/db.py

## artifacts

- `src/ledgerloom/db.py` — SQLite schema and atomic insert helpers; the only module that writes to `ledgerloom.db`.

## verification

The check confirms the file exists and references either the SQLite stdlib module or schema/table keywords. If `db.py` ever loses its writer or its schema, this verdict flips.
