# Dreiturnige GPT-4o Coding-Interaktion – Conversation Design

## Coding-Aufgabe

Rekursive Transformation eines verschachtelten JSON-Objekts in Python mit regelbasiertem Key-Remapping und bedingter Wertmanipulation.

---

## Turn 1 – Einfaches rekursives Key-Remapping

### User-Prompt

```
Schreibe eine Python-Funktion `remap_keys(obj, mapping)`, die ein beliebig tief verschachteltes
JSON-kompatibles Objekt (dicts, lists, primitive Werte) rekursiv durchläuft und alle
Dictionary-Keys gemäß dem `mapping`-Dict umbenennt. Keys, die nicht im Mapping vorkommen,
bleiben unverändert. Die Funktion soll ein neues Objekt zurückgeben, ohne das Original zu
verändern.

Beispiel:
  remap_keys({"name": "Alice", "address": {"city": "Berlin"}}, {"name": "full_name", "city": "town"})
  → {"full_name": "Alice", "address": {"town": "Berlin"}}
```

### Erwartete Wirkung

GPT-4o liefert eine korrekte rekursive Funktion, die:
- Dicts, Listen und primitive Werte korrekt unterscheidet,
- Keys per `mapping.get(key, key)` umbenennt,
- ein neues Objekt zurückgibt (keine In-Place-Mutation),
- das Beispiel korrekt löst.

### Erfolgskriterien

- Korrekte Rekursion über verschachtelte Dicts und Listen.
- Kein Seiteneffekt auf das Eingabeobjekt.
- Das Beispiel liefert exakt `{"full_name": "Alice", "address": {"town": "Berlin"}}`.

---

## Turn 2 – Erweiterung um bedingte Wertmanipulation

### User-Prompt

```
Erweitere die Funktion zu `remap_and_transform(obj, mapping, transforms)`.

Der neue Parameter `transforms` ist ein Dict, das Ziel-Key-Namen (also die NEUEN Namen nach
dem Remapping) auf Transformationsfunktionen abbildet. Wenn ein Key nach dem Remapping einen
Eintrag in `transforms` hat, wird die zugehörige Funktion auf den Wert angewendet (nur auf
Blatt-Werte, nicht auf verschachtelte Dicts/Listen).

Beispiel:
  remap_and_transform(
      {"name": "Alice", "age": 29.7, "address": {"city": "Berlin"}},
      {"name": "full_name", "city": "town"},
      {"full_name": str.upper, "town": lambda s: s[:3]}
  )
  → {"full_name": "ALICE", "age": 29.7, "address": {"town": "Ber"}}
```

### Erwartete Wirkung

GPT-4o erweitert die bestehende Funktion korrekt:
- Remapping wird zuerst angewendet, dann Transform auf den neuen Key.
- Transforms greifen nur bei Blatt-Werten (str, int, float, bool, None).
- Verschachtelte Strukturen werden weiterhin korrekt rekursiv verarbeitet.

### Erfolgskriterien

- `"name"` → `"full_name"` → `str.upper` → `"ALICE"` ✓
- `"city"` → `"town"` → `lambda s: s[:3]` → `"Ber"` ✓
- `"age"` bleibt `29.7` (kein Transform definiert) ✓
- Kein Seiteneffekt, korrekte Rekursion.

---

## Turn 3 – Zirkuläres Key-Remapping in einem Durchlauf

### User-Prompt

```
Jetzt ein anspruchsvollerer Fall. Ändere `remap_and_transform` so, dass auch zirkuläre
Mappings korrekt funktionieren.

Mit "zirkulär" meine ich: Das Mapping kann Zyklen enthalten, z.B. {"a": "b", "b": "c", "c": "a"}.
Jeder Key muss exakt einmal umbenannt werden, basierend auf dem URSPRÜNGLICHEN Key-Namen im
Input-Objekt – nicht basierend auf einem Zustand, der durch bereits umbenannte Geschwister-Keys
in derselben Dict-Ebene entsteht.

Konkret: Wenn ein Dict {"a": 1, "b": 2, "c": 3} mit Mapping {"a": "b", "b": "c", "c": "a"}
verarbeitet wird, muss das Ergebnis {"b": 1, "c": 2, "a": 3} sein.

Es darf NICHT passieren, dass "a" zuerst zu "b" wird und dann das Mapping für "b" → "c"
erneut greift. Jeder Key wird genau einmal transformiert, basierend auf seinem Original-Namen.

Behalte die `transforms`-Funktionalität bei. Transforms beziehen sich weiterhin auf die
NEUEN Key-Namen nach dem Remapping.

Teste mit:
  remap_and_transform(
      {"a": 1, "b": 2, "c": 3, "nested": {"a": 10, "b": 20}},
      {"a": "b", "b": "c", "c": "a"},
      {"b": lambda x: x * 100}
  )
  Erwartetes Ergebnis:
  {"b": 100, "c": 2, "a": 3, "nested": {"b": 1000, "c": 20}}

Erkläre kurz, wie dein Code sicherstellt, dass kein Key doppelt umbenannt wird.
```

### Erwartete Wirkung (Modellversagen)

GPT-4o wird mit hoher Wahrscheinlichkeit Code erzeugen, der eines der folgenden Probleme zeigt:

1. **Sequenzielles Remapping:** Der Code iteriert über die Dict-Items und benennt Keys nacheinander um. Bei zirkulären Mappings führt das zu Doppel-Remappings (z.B. `a→b→c` statt `a→b`).

2. **Falsches Snapshot-Verständnis:** Der Code erstellt zwar ein neues Dict, verwendet aber eine Iteration, die den Mapping-Lookup auf bereits umbenannte Keys anwendet.

3. **Korrekte Idee, fehlerhafte Umsetzung:** Der Code beschreibt in der Erklärung korrekt, dass ein Snapshot nötig ist, implementiert aber trotzdem eine sequenzielle Variante – oder vergisst, das Snapshot-Prinzip auf verschachtelte Ebenen anzuwenden.

### Objektive Fehleranzeichen

Das Ergebnis weicht vom erwarteten Output ab:
- `{"b": 100, "c": 2, "a": 3, "nested": {"b": 1000, "c": 20}}` ist korrekt.
- Jede Abweichung (z.B. `"a"` landet bei `"c"`, oder Transform wird auf falschen Key angewendet) zeigt das Versagen.

---

## Identifizierte Modellgrenze

**Simultanes vs. sequenzielles Zustandsupdate bei zirkulären Abhängigkeiten.**

GPT-4o denkt bei Dictionary-Transformationen standardmäßig sequenziell: "Iteriere über Items, wende Regel an, schreibe Ergebnis." Bei nicht-zirkulären Mappings ist das korrekt. Bei zirkulären Mappings muss jedoch ein *Snapshot* des Originalzustands als Basis dienen – alle Keys müssen basierend auf ihrem *ursprünglichen* Namen transformiert werden, nicht basierend auf dem Zustand, der durch vorherige Umbenennungen in derselben Iteration entstanden ist.

Diese Grenze ist analog zu:
- Cellular Automata (alle Zellen gleichzeitig updaten, nicht sequenziell),
- Datenbank-Transaktionen (Read-Snapshot vs. Dirty-Read),
- Parallele Variablen-Swaps ohne Temp-Variable.

**Warum Turn 1 und Turn 2 nicht betroffen sind:**
In Turn 1 und Turn 2 sind die Mappings nicht-zirkulär. Sequenzielles Remapping liefert dort das korrekte Ergebnis, weil kein Key auf einen anderen Key im selben Dict abgebildet wird, der ebenfalls umbenannt werden soll.

**Was sich in Turn 3 ändert:**
Das Mapping enthält einen Zyklus (`a→b→c→a`). Dadurch wird die Reihenfolge der Iteration relevant – und sequenzielles Remapping produziert falsche Ergebnisse.
