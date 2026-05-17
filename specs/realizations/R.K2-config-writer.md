---
id: R.K2
title: src/ledgerloom/config.py — write side
layer: realizations
kind: spec
parents: [K.2]
peers_depends_on: []
verdict:
  mechanism: automated_check
  check: "test -f src/ledgerloom/config.py && grep -qE '(yaml\\.safe_dump|yaml\\.dump)' src/ledgerloom/config.py"
  status: unknown
---

# R.K2 — src/ledgerloom/config.py write side

## artifacts

- `src/ledgerloom/config.py` — the only module in the project allowed to write YAML (per constraint I.4).

## verification

The check confirms the file exists AND contains a YAML dump call. If `config.py` ever loses its writer, this verdict flips to violated.
