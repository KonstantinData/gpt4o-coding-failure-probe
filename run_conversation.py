"""Send the 3-turn conversation to GPT-4o via OpenRouter and export the full interaction.

Produces:
  openrouter_interaction.json  – complete chat with all GPT-4o responses + verification

Usage:
    set OPENROUTER_API_KEY=<your-key>      (or create .env from .env.example)
    python run_conversation.py
"""

import json, os, re, subprocess, sys, textwrap
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

# Load .env if present
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
    (
        'Schreibe eine Python-Funktion `remap_keys(obj, mapping)`, die ein beliebig tief '
        'verschachteltes JSON-kompatibles Objekt (dicts, lists, primitive Werte) rekursiv '
        'durchläuft und alle Dictionary-Keys gemäß dem `mapping`-Dict umbenennt. Keys, die '
        'nicht im Mapping vorkommen, bleiben unverändert. Die Funktion soll ein neues Objekt '
        'zurückgeben, ohne das Original zu verändern.\n\n'
        'Beispiel:\n'
        '  remap_keys({"name": "Alice", "address": {"city": "Berlin"}}, '
        '{"name": "full_name", "city": "town"})\n'
        '  → {"full_name": "Alice", "address": {"town": "Berlin"}}'
    ),
    # Turn 2
    (
        'Erweitere die Funktion zu `remap_and_transform(obj, mapping, transforms)`.\n\n'
        'Der neue Parameter `transforms` ist ein Dict, das Ziel-Key-Namen (also die NEUEN '
        'Namen nach dem Remapping) auf Transformationsfunktionen abbildet. Wenn ein Key nach '
        'dem Remapping einen Eintrag in `transforms` hat, wird die zugehörige Funktion auf '
        'den Wert angewendet (nur auf Blatt-Werte, nicht auf verschachtelte Dicts/Listen).\n\n'
        'Beispiel:\n'
        '  remap_and_transform(\n'
        '      {"name": "Alice", "age": 29.7, "address": {"city": "Berlin"}},\n'
        '      {"name": "full_name", "city": "town"},\n'
        '      {"full_name": str.upper, "town": lambda s: s[:3]}\n'
        '  )\n'
        '  → {"full_name": "ALICE", "age": 29.7, "address": {"town": "Ber"}}'
    ),
    # Turn 3
    (
        'Letzte Erweiterung. Ändere die Signatur zu:\n\n'
        '  remap_and_transform(obj, rules, transforms)\n\n'
        '`rules` ist jetzt eine Liste von Pfad-basierten Regeln. Jede Regel hat die Form:\n'
        '  {"path": "<pfad-pattern>", "mapping": <dict>}\n\n'
        'Ein Pfad-Pattern beschreibt, WO im Objekt das Mapping angewendet wird:\n'
        '- "." bedeutet: auf das Top-Level-Dict\n'
        '- "address" bedeutet: auf das Dict, das unter dem Key "address" liegt\n'
        '- "address.geo" bedeutet: auf das Dict unter "address" → "geo"\n'
        '- "*" ist ein Wildcard und matcht EINEN beliebigen Key auf dieser Ebene\n'
        '- "**" matcht NULL ODER MEHR Ebenen (wie bei Glob-Patterns)\n\n'
        'Spezifitäts-Regel: Wenn mehrere Regeln auf dasselbe Dict matchen, gewinnt die '
        'SPEZIFISCHSTE Regel (die mit den wenigsten Wildcards). Bei Gleichstand gewinnt '
        'die Regel, die in der Liste ZUERST steht. Es wird pro Dict nur EINE Regel angewendet '
        '(die Gewinner-Regel), nicht mehrere.\n\n'
        '`transforms` funktioniert wie bisher.\n\n'
        'Teste mit:\n'
        '  data = {\n'
        '      "id": 1,\n'
        '      "name": "Alice",\n'
        '      "address": {\n'
        '          "city": "Berlin",\n'
        '          "geo": {"lat": 52.52, "lon": 13.405}\n'
        '      },\n'
        '      "tags": [\n'
        '          {"key": "role", "value": "admin"},\n'
        '          {"key": "dept", "value": "engineering"}\n'
        '      ]\n'
        '  }\n\n'
        '  rules = [\n'
        '      {"path": "**",          "mapping": {"key": "k", "value": "v"}},\n'
        '      {"path": ".",           "mapping": {"name": "full_name", "id": "identifier"}},\n'
        '      {"path": "address",     "mapping": {"city": "town"}},\n'
        '      {"path": "address.geo", "mapping": {"lat": "latitude", "lon": "longitude"}},\n'
        '      {"path": "tags.*",      "mapping": {"key": "tag_key", "value": "tag_value"}}\n'
        '  ]\n\n'
        '  transforms = {\n'
        '      "full_name": str.upper,\n'
        '      "town": lambda s: s[:3],\n'
        '      "latitude": str,\n'
        '      "longitude": str\n'
        '  }\n\n'
        '  remap_and_transform(data, rules, transforms)\n\n'
        'Erwartetes Ergebnis:\n'
        '  {\n'
        '      "identifier": 1,\n'
        '      "full_name": "ALICE",\n'
        '      "address": {\n'
        '          "town": "Ber",\n'
        '          "geo": {"latitude": "52.52", "longitude": "13.405"}\n'
        '      },\n'
        '      "tags": [\n'
        '          {"tag_key": "role", "tag_value": "admin"},\n'
        '          {"tag_key": "dept", "tag_value": "engineering"}\n'
        '      ]\n'
        '  }\n\n'
        'Beachte: Die "**"-Regel matcht zwar auf alle Dicts, aber sie verliert überall dort, '
        'wo eine spezifischere Regel existiert. Sie würde nur greifen, wenn es ein Dict gäbe, '
        'auf das keine andere Regel passt.'
    ),
]

EXPECTED_T3 = {
    "identifier": 1,
    "full_name": "ALICE",
    "address": {
        "town": "Ber",
        "geo": {"latitude": "52.52", "longitude": "13.405"},
    },
    "tags": [
        {"tag_key": "role", "tag_value": "admin"},
        {"tag_key": "dept", "tag_value": "engineering"},
    ],
}


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
        if hasattr(e, "read"):
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
        "task": "recursive-json-key-remapping-path-wildcards-specificity",
    },
    "turns": [],
}

for i, prompt in enumerate(PROMPTS, 1):
    history.append({"role": "user", "content": prompt})
    print(f"\n{'='*60}\nTurn {i} – sending …\n{'='*60}")

    reply = chat(history)
    history.append({"role": "assistant", "content": reply})

    export["turns"].append({"turn": i, "user": prompt, "assistant": reply})
    print(reply[:2000] + ("\n[…truncated]" if len(reply) > 2000 else ""))

# ── Verify Turn 3 ───────────────────────────────────────────────────

code = extract_python(export["turns"][2]["assistant"])
test_code = code + textwrap.dedent("""

# --- automated verification ---
_result = remap_and_transform(
    {
        "id": 1,
        "name": "Alice",
        "address": {
            "city": "Berlin",
            "geo": {"lat": 52.52, "lon": 13.405}
        },
        "tags": [
            {"key": "role", "value": "admin"},
            {"key": "dept", "value": "engineering"}
        ]
    },
    [
        {"path": "**",          "mapping": {"key": "k", "value": "v"}},
        {"path": ".",           "mapping": {"name": "full_name", "id": "identifier"}},
        {"path": "address",     "mapping": {"city": "town"}},
        {"path": "address.geo", "mapping": {"lat": "latitude", "lon": "longitude"}},
        {"path": "tags.*",      "mapping": {"key": "tag_key", "value": "tag_value"}}
    ],
    {
        "full_name": str.upper,
        "town": lambda s: s[:3],
        "latitude": str,
        "longitude": str
    }
)
import json as _json
print("ACTUAL:", _json.dumps(_result, sort_keys=True))
""")

tmp = "_turn3_extracted.py"
with open(tmp, "w", encoding="utf-8") as f:
    f.write(test_code)

print(f"\n{'='*60}\nVerification\n{'='*60}")

proc = subprocess.run([sys.executable, tmp], capture_output=True, text=True)
print(proc.stdout)
if proc.stderr:
    print("STDERR:", proc.stderr[:2000])

actual_line = [l for l in proc.stdout.splitlines() if l.startswith("ACTUAL:")]
if actual_line:
    actual = json.loads(actual_line[0].split("ACTUAL:", 1)[1])
else:
    actual = None
    print("WARNING: Could not extract output (code may have crashed)")

passed = actual == EXPECTED_T3
verdict = "PASS (model solved it)" if passed else "FAIL (failure mode confirmed)"
print(f"\n{verdict}")

export["verification"] = {
    "turn3_expected": EXPECTED_T3,
    "turn3_actual": actual,
    "turn3_pass": passed,
    "turn3_stderr": proc.stderr[:2000] if proc.stderr else None,
    "verdict": verdict,
}

# ── Export ────────────────────────────────────────────────────────────

out_file = "openrouter_interaction.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(export, f, indent=2, ensure_ascii=False)

print(f"\nFull interaction exported → {out_file}")
