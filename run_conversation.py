"""Send the 3-turn conversation to GPT-4o via OpenRouter and export the full interaction.

Produces:
  openrouter_interaction.json  – complete chat with all GPT-4o responses
  _turn3_extracted.py          – extracted Turn-3 code for verification

Usage:
    set OPENROUTER_API_KEY=<your-key>
    python run_conversation.py
"""

import json, os, re, subprocess, sys, textwrap
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

# Load .env if present (no external dependency needed)
_env = Path(__file__).with_name(".env")
if _env.exists():
    for line in _env.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
if not API_KEY:
    sys.exit("ERROR: set OPENROUTER_API_KEY or create a .env file (see .env.example).")

URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-4o"

PROMPTS = [
    # Turn 1
    'Schreibe eine Python-Funktion `remap_keys(obj, mapping)`, die ein beliebig tief verschachteltes JSON-kompatibles Objekt (dicts, lists, primitive Werte) rekursiv durchläuft und alle Dictionary-Keys gemäß dem `mapping`-Dict umbenennt. Keys, die nicht im Mapping vorkommen, bleiben unverändert. Die Funktion soll ein neues Objekt zurückgeben, ohne das Original zu verändern.\n\nBeispiel:\n  remap_keys({"name": "Alice", "address": {"city": "Berlin"}}, {"name": "full_name", "city": "town"})\n  → {"full_name": "Alice", "address": {"town": "Berlin"}}',
    # Turn 2
    'Erweitere die Funktion zu `remap_and_transform(obj, mapping, transforms)`.\n\nDer neue Parameter `transforms` ist ein Dict, das Ziel-Key-Namen (also die NEUEN Namen nach dem Remapping) auf Transformationsfunktionen abbildet. Wenn ein Key nach dem Remapping einen Eintrag in `transforms` hat, wird die zugehörige Funktion auf den Wert angewendet (nur auf Blatt-Werte, nicht auf verschachtelte Dicts/Listen).\n\nBeispiel:\n  remap_and_transform(\n      {"name": "Alice", "age": 29.7, "address": {"city": "Berlin"}},\n      {"name": "full_name", "city": "town"},\n      {"full_name": str.upper, "town": lambda s: s[:3]}\n  )\n  → {"full_name": "ALICE", "age": 29.7, "address": {"town": "Ber"}}',
    # Turn 3
    'Jetzt ein anspruchsvollerer Fall. Ändere `remap_and_transform` so, dass auch zirkuläre Mappings korrekt funktionieren.\n\nMit "zirkulär" meine ich: Das Mapping kann Zyklen enthalten, z.B. {"a": "b", "b": "c", "c": "a"}. Jeder Key muss exakt einmal umbenannt werden, basierend auf dem URSPRÜNGLICHEN Key-Namen im Input-Objekt – nicht basierend auf einem Zustand, der durch bereits umbenannte Geschwister-Keys in derselben Dict-Ebene entsteht.\n\nKonkret: Wenn ein Dict {"a": 1, "b": 2, "c": 3} mit Mapping {"a": "b", "b": "c", "c": "a"} verarbeitet wird, muss das Ergebnis {"b": 1, "c": 2, "a": 3} sein.\n\nEs darf NICHT passieren, dass "a" zuerst zu "b" wird und dann das Mapping für "b" → "c" erneut greift. Jeder Key wird genau einmal transformiert, basierend auf seinem Original-Namen.\n\nBehalte die `transforms`-Funktionalität bei. Transforms beziehen sich weiterhin auf die NEUEN Key-Namen nach dem Remapping.\n\nTeste mit:\n  remap_and_transform(\n      {"a": 1, "b": 2, "c": 3, "nested": {"a": 10, "b": 20}},\n      {"a": "b", "b": "c", "c": "a"},\n      {"b": lambda x: x * 100}\n  )\n  Erwartetes Ergebnis:\n  {"b": 100, "c": 2, "a": 3, "nested": {"b": 1000, "c": 20}}\n\nErkläre kurz, wie dein Code sicherstellt, dass kein Key doppelt umbenannt wird.',
]

EXPECTED_T3 = {"b": 100, "c": 2, "a": 3, "nested": {"b": 1000, "c": 20}}


def chat(messages):
    body = json.dumps({"model": MODEL, "messages": messages}).encode()
    req = Request(URL, data=body, headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    })
    try:
        with urlopen(req) as resp:
            return json.loads(resp.read())["choices"][0]["message"]["content"]
    except Exception as e:
        # Print response body for debugging
        if hasattr(e, 'read'):
            print(f"API error: {e.read().decode()}", file=sys.stderr)
        raise


def extract_python(text):
    blocks = re.findall(r"```python\s*\n(.*?)```", text, re.DOTALL)
    return "\n\n".join(blocks) if blocks else text


# ── Execute turns ────────────────────────────────────────────────────

history = []
export = {
    "meta": {
        "model": MODEL,
        "provider": "openrouter",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task": "recursive-json-key-remapping-cyclic-failure-probe",
    },
    "turns": [],
}

for i, prompt in enumerate(PROMPTS, 1):
    history.append({"role": "user", "content": prompt})
    print(f"\n{'='*60}\nTurn {i} – sending …\n{'='*60}")

    reply = chat(history)
    history.append({"role": "assistant", "content": reply})

    export["turns"].append({
        "turn": i,
        "user": prompt,
        "assistant": reply,
    })
    print(reply[:2000] + ("\n[…truncated]" if len(reply) > 2000 else ""))

# ── Verify Turn 3 ───────────────────────────────────────────────────

code = extract_python(export["turns"][2]["assistant"])
test_code = code + textwrap.dedent("""

# --- automated verification ---
_result = remap_and_transform(
    {"a": 1, "b": 2, "c": 3, "nested": {"a": 10, "b": 20}},
    {"a": "b", "b": "c", "c": "a"},
    {"b": lambda x: x * 100},
)
import json as _json
print("ACTUAL:", _json.dumps(_result, sort_keys=True))
""")

tmp = "_turn3_extracted.py"
with open(tmp, "w", encoding="utf-8") as f:
    f.write(test_code)

print(f"\n{'='*60}\nVerification\n{'='*60}")
exit_code = os.system(f"{sys.executable} {tmp}")

# Capture actual output for export
proc = subprocess.run([sys.executable, tmp], capture_output=True, text=True)
actual_line = [l for l in proc.stdout.splitlines() if l.startswith("ACTUAL:")]
actual = json.loads(actual_line[0].split("ACTUAL:")[1]) if actual_line else None

passed = actual == EXPECTED_T3
export["verification"] = {
    "turn3_expected": EXPECTED_T3,
    "turn3_actual": actual,
    "turn3_pass": passed,
}

verdict = "PASS ✅  (model solved cyclic case)" if passed else "FAIL ❌  (failure mode confirmed)"
print(f"\n{verdict}")
export["verification"]["verdict"] = verdict

# ── Export ────────────────────────────────────────────────────────────

out_file = "openrouter_interaction.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(export, f, indent=2, ensure_ascii=False)

print(f"\nFull interaction exported → {out_file}")
