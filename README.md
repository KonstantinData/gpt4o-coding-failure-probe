# gpt4o-coding-failure-probe

Designs and documents a three-turn GPT-4o coding interaction where early turns succeed and the final turn reveals a targeted model failure.

## Task

Recursive JSON key-remapping in Python with cyclic mapping chains as the failure trigger.

## Deliverables

| File | Content |
|---|---|
| `conversation_design.md` | Full conversation design with three turns, success criteria, and failure analysis (DE) |
| `conversation.json` | Structured JSON chat file for reproducible testing |
| `analysis_note_en.md` | English reference: task logic, failure mode, correct solution sketch |
| `remap.py` | Executable reference implementation with assertions for all three turns |
| `run_conversation.py` | Sends the 3-turn conversation to GPT-4o via OpenRouter and verifies Turn 3 output |

## Usage

```bash
# 1. Verify the reference solution locally
python remap.py

# 2. Run the conversation against GPT-4o on OpenRouter
set OPENROUTER_API_KEY=<your-key>
python run_conversation.py
```

## Failure Mode

**Simultaneous vs. sequential state update on cyclic key mappings.**

Turns 1–2 use non-cyclic mappings where sequential iteration is correct. Turn 3 introduces a cyclic mapping (`a→b, b→c, c→a`) that requires snapshot-based remapping. GPT-4o typically generates sequential code that double-remaps keys.
