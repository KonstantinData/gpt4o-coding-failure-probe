# gpt4o-coding-failure-probe

A three-turn coding conversation with GPT-4o where the first two turns produce correct results and the third turn exposes a specific model failure.

## Task

Recursive JSON key-remapping in Python. The failure trigger is path-based wildcard rules with specificity precedence.

## Deliverables

| File | Content |
|---|---|
| `conversation_design.md` | Three-turn conversation design with success criteria and failure analysis (German) |
| `conversation.json` | Structured JSON conversation template |
| `conversation_en.md` | Full English translation of the conversation, including model responses |
| `analysis_note_en.md` | English analysis note covering task logic, failure mode, and a correct solution sketch |
| `openrouter_interaction.json` | Recorded GPT-4o interaction with verification results |

## Failure Mode

Path-based pattern matching with wildcards (`*`, `**`) and specificity-based rule selection inside a recursive tree transformation.

Turns 1 and 2 use a single global mapping dict — GPT-4o handles these correctly. Turn 3 switches to path-scoped rules with wildcard patterns and a most-specific-rule-wins precedence. GPT-4o fails on the interaction of three things: matching paths through lists, implementing `**` as zero-or-more (not one-or-more), and selecting the most specific rule instead of the first match.
