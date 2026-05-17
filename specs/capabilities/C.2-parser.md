---
id: C.2
title: /parser — add a new bank/card parser from a sample
layer: capabilities
kind: spec
parents: [I.2]
peers_depends_on: [C.10]
verdict:
  mechanism: llm_judge
  status: unknown
contract:
  version: 0.1.0
  locked: false
  field_anchors: [summary, interface]
---

# C.2 — /parser

## summary

Given a sample statement (PDF or CSV) in `data/<bank>/`, generate a parser at `src/ledgerloom/parsers/<bank>.py` that extracts transactions in the canonical schema. Register the parser in `ingest.py` and append the corresponding `sources:` block to `config/user_config.yaml`.

## interface

- `/parser` — runs interactively; user points at the sample file.
- Output: `src/ledgerloom/parsers/<bank>.py`, updated `ingest.py`, updated `config/user_config.yaml`.
