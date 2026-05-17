---
id: I.4
title: All config I/O through ledgerloom.config
layer: intent
kind: constraint
parents: []
peers_depends_on: []
applies_to:
  layer: realizations
  filter: ""
verdict:
  mechanism: automated_check
  check: "! grep -rE 'yaml\\.(safe_load|load|dump|safe_dump)' src/ledgerloom/ --include='*.py' | grep -v 'src/ledgerloom/config.py' 2>/dev/null"
  status: unknown
  evidence_ref: "CLAUDE.md Configuration section"
---

# I.4 — All config I/O through ledgerloom.config

## why

CLAUDE.md is explicit: "All config I/O goes through `src/ledgerloom/config.py` — never read or write YAML directly from any other module." Two YAML files diverging in their interpretation of the same config key is the kind of bug that silently misroutes money. One loader, one writer, one schema.

## constraint

Only `src/ledgerloom/config.py` may call `yaml.safe_load`, `yaml.load`, `yaml.dump`, or `yaml.safe_dump`. Every other module must use the typed accessors (`load_user_config`, `load_categories`, `load_merchants`).

## verification

The check greps for `yaml.(safe_load|load|dump|safe_dump)` under `src/ledgerloom/` and excludes `config.py`. Any match outside config.py is a violation.
