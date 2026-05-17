---
id: K.8
title: atomic persist to ledgerloom.db
layer: contracts
kind: spec
parents: [C.10]
peers_depends_on: [K.7]
verdict:
  mechanism: llm_judge
  status: unknown
contract:
  version: 0.1.0
  locked: false
  field_anchors: [signature, behaviour, error]
---

# K.8 — atomic persist to ledgerloom.db

## signature

- input: list of fully-pipelined Transactions
- output: rows written into `ledgerloom.db`'s `transactions` table

## behaviour

- Schema declared in `src/ledgerloom/db.py`. Single source of truth for column names and types.
- Inserts are batched per-source within a single SQLite transaction.
- Idempotent on re-run: duplicate (date + source + amount + raw_merchant) tuples are skipped.

## error

- Raises if `ledgerloom.db` is locked by another writer.
- On schema mismatch, halts before any write so the on-disk db is not partially-updated.
