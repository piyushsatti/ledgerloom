---
id: I.2
title: Adapt to my banks, country, currency, and life
layer: intent
kind: spec
parents: []
peers_depends_on: []
verdict:
  mechanism: human_signoff
  status: satisfied
  evidence_ref: "README.md 'fork-and-personalize' framing + /onboard /parser /categorize commands"
---

# I.2 — Adapt to my banks, country, currency, and life

## why

Personal finance tooling fails when it assumes you live in the US, bank with Chase, and earn a W-2 salary. This project's premise is fork-and-personalize: the same code works for an RBC checking account in Canada or an HDFC credit card in India, because the user is asked one question at a time, banks are added via a parser-generation command, and merchants are labeled interactively against a domain the user lives in.

## success criteria

- A new user can run `/onboard` once and have the tool configured for their banks, country, currency, and tax jurisdiction.
- Adding a new bank requires running `/parser` against a sample file — not editing core code.
- Merchants are categorized through `/categorize` with the user's own taxonomy, not a baked-in one.
- The pipeline (extract → parse → normalize → categorize → ingest) absorbs whatever shape the data arrives in.
