"""Send the three-turn conversation to GPT-4o via OpenRouter and verify outputs.

Usage:
    set OPENROUTER_API_KEY=<your-key>
    python run_conversation.py
"""

import json, os, re, sys, textwrap
from urllib.request import Request, urlopen

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-4o"

with open("conversation.json", encoding="utf-8") as f:
    spec = json.load(f)


def chat(messages: list[dict]) -> str:
    body = json.dumps({"model": MODEL, "messages": messages}).encode()
    req = Request(URL, data=body, headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    })
    with urlopen(req) as resp:
        return json.loads(resp.read())["choices"][0]["message"]["content"]


def extract_python(text: str) -> str:
    blocks = re.findall(r"```python\s*\n(.*?)```", text, re.DOTALL)
    return "\n\n".join(blocks) if blocks else text


# ── Turn-by-turn execution ──────────────────────────────────────────

history: list[dict] = []
responses: list[str] = []

for turn_spec in spec["turns"]:
    turn_num = turn_spec["turn"]
    # Collect only user messages for this turn (skip assistant placeholders)
    user_msgs = [m for m in turn_spec["messages"] if m["role"] == "user"]
    new_user_msg = user_msgs[-1]  # the last user message is the new one

    history.append(new_user_msg)
    print(f"\n{'='*60}\nTurn {turn_num} – sending {len(history)} messages …\n{'='*60}")

    reply = chat(history)
    responses.append(reply)
    history.append({"role": "assistant", "content": reply})

    print(f"\n--- GPT-4o response (Turn {turn_num}) ---")
    print(reply[:2000] + ("\n[…truncated]" if len(reply) > 2000 else ""))

# ── Verification ─────────────────────────────────────────────────────

print(f"\n{'='*60}\nVerification\n{'='*60}")

code = extract_python(responses[-1])  # Turn 3 code

# Write extracted code to temp file and exec it with the test case
test_code = code + textwrap.dedent("""

# --- automated verification ---
result = remap_and_transform(
    {"a": 1, "b": 2, "c": 3, "nested": {"a": 10, "b": 20}},
    {"a": "b", "b": "c", "c": "a"},
    {"b": lambda x: x * 100},
)
print("ACTUAL OUTPUT:", result)
expected = {"b": 100, "c": 2, "a": 3, "nested": {"b": 1000, "c": 20}}
if result == expected:
    print("RESULT: PASS ✅  (model solved the cyclic case correctly)")
else:
    print("RESULT: FAIL ❌  (model produced wrong output – failure mode confirmed)")
    print("EXPECTED:", expected)
""")

tmp = "_turn3_extracted.py"
with open(tmp, "w", encoding="utf-8") as f:
    f.write(test_code)

print(f"\nExtracted Turn-3 code → {tmp}")
print("Running verification …\n")
os.system(f"{sys.executable} {tmp}")
