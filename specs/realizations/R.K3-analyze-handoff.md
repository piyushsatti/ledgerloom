---
id: R.K3
title: .claude/commands/analyze.md (handoff target)
layer: realizations
kind: spec
parents: [K.3]
peers_depends_on: []
verdict:
  mechanism: automated_check
  check: "test -f .claude/commands/analyze.md && test -f .claude/commands/onboard.md"
  status: unknown
---

# R.K3 — .claude/commands/analyze.md

## artifacts

- `.claude/commands/onboard.md` — directs the agent to run `/analyze` after writing the config.
- `.claude/commands/analyze.md` — the analysis command itself.

## verification

The check confirms both files exist. A deeper check would verify the prose in `onboard.md` actually references `/analyze`; left for v0.2 of this spec.
