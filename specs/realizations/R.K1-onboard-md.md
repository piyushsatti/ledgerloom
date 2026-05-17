---
id: R.K1
title: .claude/commands/onboard.md
layer: realizations
kind: spec
parents: [K.1]
peers_depends_on: []
verdict:
  mechanism: automated_check
  check: "test -f .claude/commands/onboard.md && grep -q 'AskUserQuestion' .claude/commands/onboard.md"
  status: unknown
---

# R.K1 — .claude/commands/onboard.md

## artifacts

- `.claude/commands/onboard.md` — the slash-command prose that drives the question flow.

## verification

The check confirms the file exists AND that the prose actually instructs the agent to use `AskUserQuestion` (the one-question-at-a-time discipline from CLAUDE.md).
