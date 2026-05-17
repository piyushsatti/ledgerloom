---
id: C.1
title: /onboard — first-time setup
layer: capabilities
kind: spec
parents: [I.2]
peers_depends_on: []
verdict:
  mechanism: llm_judge
  judge_prompt: "Does .claude/commands/onboard.md drive a sequential question flow that produces a valid config/user_config.yaml and triggers an initial analysis?"
  status: unknown
contract:
  version: 0.1.0
  locked: false
  field_anchors: [summary, interface, behaviour]
---

# C.1 — /onboard

## summary

One-question-at-a-time interactive setup. Gathers user context (name, income, currency, tax jurisdiction, fixed obligations), writes `config/user_config.yaml`, and runs an initial `/analyze` to give immediate value.

## interface

- `/onboard` — invokes the slash command from anywhere in the project.
- Output: `config/user_config.yaml`, then an analysis transcript.

## behaviour

- Uses `AskUserQuestion` per CLAUDE.md "How to Guide Users" #2.
- Curiosity-first: asks about life/work/sleep before asking about money.
- Writes config atomically; refuses to overwrite an existing `config/user_config.yaml` without explicit confirmation.
