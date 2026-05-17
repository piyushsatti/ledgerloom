---
id: R.K4
title: src/ledgerloom/extract.py
layer: realizations
kind: spec
parents: [K.4]
peers_depends_on: []
verdict:
  mechanism: automated_check
  check: "test -f src/ledgerloom/extract.py && grep -q 'pdftotext' src/ledgerloom/extract.py && grep -q 'sha256' src/ledgerloom/extract.py"
  status: unknown
---

# R.K4 — src/ledgerloom/extract.py

## artifacts

- `src/ledgerloom/extract.py` — invokes `pdftotext`, caches by SHA-256 under `cache/extracted/`.

## verification

The check confirms the file exists, calls `pdftotext`, and uses `sha256` somewhere — the three observable promises K.4 makes.
