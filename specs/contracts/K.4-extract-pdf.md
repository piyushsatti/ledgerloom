---
id: K.4
title: extract PDF to text with SHA-256 caching
layer: contracts
kind: spec
parents: [C.10]
peers_depends_on: []
verdict:
  mechanism: llm_judge
  status: unknown
contract:
  version: 0.1.0
  locked: false
  field_anchors: [signature, behaviour, error]
---

# K.4 — extract PDF to text with SHA-256 caching

## signature

- input: path to a PDF statement file
- output: extracted text (string)

## behaviour

- Invokes `pdftotext` via subprocess.
- Caches output keyed by SHA-256 of the PDF bytes under `cache/extracted/`.
- Cache hit returns immediately without re-invoking `pdftotext`.

## error

- Raises if `pdftotext` is not on PATH (clear remediation message: `brew install poppler` / `apt install poppler-utils`).
- Raises if the PDF is unreadable; does not write an empty cache entry.
