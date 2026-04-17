# gpt4o-coding-failure-probe

Designs and documents a three-turn GPT-4o coding interaction where early turns succeed and the final turn reveals a targeted model failure.

## Task

Recursive JSON key-remapping in Python with path-based wildcard rules and specificity precedence as the failure trigger.

## Deliverables

| File | Content |
|---|---|
| `conversation_design.md` | Full conversation design with three turns, success criteria, and failure analysis (DE) |
| `conversation.json` | Structured JSON conversation template for reproducible testing |
| `conversation_en.md` | Complete English reference translation of all three prompts |
| `analysis_note_en.md` | English analysis: task logic, failure mode, correct solution sketch |
| `openrouter_interaction.json` | Exported full interaction with GPT-4o responses and verification |

## Failure Mode

**Path-based pattern matching with wildcards and specificity precedence in recursive tree transformation.**

Turns 1–2 use simple global mappings where GPT-4o produces correct code. Turn 3 introduces path-based rules with `*` and `**` wildcards, specificity-based rule selection, and list traversal semantics. GPT-4o fails on the combination of these constraints: path matching through lists, `**` zero-or-more globbing, and most-specific-rule-wins precedence.
