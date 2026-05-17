---
id: C.6
title: /subscriptions — recurring charge audit
layer: capabilities
kind: spec
parents: [I.1]
peers_depends_on: [C.10]
verdict:
  mechanism: llm_judge
  status: unknown
contract:
  version: 0.1.0
  locked: false
  field_anchors: [summary]
---

# C.6 — /subscriptions

## summary

Audits every recurring charge across bank, credit card, and PayPal — including ones the user has forgotten about. Cross-references against email confirmations where available. Surfaces the annual cost of each, and the date of last visible value (logged in, used).
