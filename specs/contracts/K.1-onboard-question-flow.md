---
id: K.1
title: sequential question flow for onboarding
layer: contracts
kind: spec
parents: [C.1]
peers_depends_on: []
verdict:
  mechanism: llm_judge
  judge_prompt: "Does .claude/commands/onboard.md drive a one-question-at-a-time flow that gathers the documented config fields?"
  status: unknown
contract:
  version: 0.1.0
  locked: false
  field_anchors: [signature, behaviour, non_goals]
---

# K.1 — sequential question flow for onboarding

## signature

- input: an empty (or absent) `config/user_config.yaml`
- output: a populated dict ready for `K.2` to write

## behaviour

- One question per `AskUserQuestion` invocation (CLAUDE.md "How to Guide Users" #2).
- Curiosity-first order: life/work/sleep questions before money questions.
- Required fields gathered: name, income, currency, tax jurisdiction, fixed obligations, data sources (banks).
- Each question's answer is validated before moving to the next.

## non_goals

- Does not write to disk — that's K.2's job.
- Does not run analysis — that's K.3.
