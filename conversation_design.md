# Conversation Design – Dreiturnige GPT-4o Coding-Interaktion

## Aufgabe

Rekursive Transformation verschachtelter JSON-Objekte in Python. Key-Remapping mit bedingter Wertmanipulation, aufsteigend bis zu pfadbasierten Regeln mit Wildcards.

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

### Erwartung

GPT-4o liefert eine korrekte rekursive Funktion. Standardmuster: Typunterscheidung dict/list/primitiv, Key-Lookup per `mapping.get(key, key)`, neues Objekt statt In-Place-Mutation.

### Erfolgskriterien

- Korrekte Rekursion über verschachtelte Dicts und Listen.
- Kein Seiteneffekt auf das Eingabeobjekt.
- Beispiel liefert exakt `{"full_name": "Alice", "address": {"town": "Berlin"}}`.

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

### Erwartung

Saubere Erweiterung von Turn 1. Erst Remapping, dann Transform-Lookup auf den neuen Key. Transforms nur auf Blatt-Werte, nicht auf verschachtelte Strukturen.

### Erfolgskriterien

- `"name"` → `"full_name"` → `str.upper` → `"ALICE"` ✓
- `"city"` → `"town"` → `lambda s: s[:3]` → `"Ber"` ✓
- `"age"` bleibt `29.7` (kein Transform definiert) ✓
- Kein Seiteneffekt, korrekte Rekursion.

---

## Turn 3 – Pfadbasierte Regeln mit Wildcards und Spezifitäts-Vorrang

### User-Prompt

```
Letzte Erweiterung. Ändere die Signatur zu:

  remap_and_transform(obj, rules, transforms)

`rules` ist jetzt eine Liste von Pfad-basierten Regeln. Jede Regel hat die Form:
  {"path": "<pfad-pattern>", "mapping": <dict>}

Ein Pfad-Pattern beschreibt, WO im Objekt das Mapping angewendet wird:
- "." bedeutet: auf das Top-Level-Dict
- "address" bedeutet: auf das Dict, das unter dem Key "address" liegt
- "address.geo" bedeutet: auf das Dict unter "address" → "geo"
- "*" ist ein Wildcard und matcht EINEN beliebigen Key auf dieser Ebene
- "**" matcht NULL ODER MEHR Ebenen (wie bei Glob-Patterns)

Spezifitäts-Regel: Wenn mehrere Regeln auf dasselbe Dict matchen, gewinnt die
SPEZIFISCHSTE Regel (die mit den wenigsten Wildcards). Bei Gleichstand gewinnt
die Regel, die in der Liste ZUERST steht. Es wird pro Dict nur EINE Regel angewendet
(die Gewinner-Regel), nicht mehrere.

`transforms` funktioniert wie bisher.

Teste mit:
  data = {
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
  }

  rules = [
      {"path": "**",          "mapping": {"key": "k", "value": "v"}},
      {"path": ".",           "mapping": {"name": "full_name", "id": "identifier"}},
      {"path": "address",     "mapping": {"city": "town"}},
      {"path": "address.geo", "mapping": {"lat": "latitude", "lon": "longitude"}},
      {"path": "tags.*",      "mapping": {"key": "tag_key", "value": "tag_value"}}
  ]

  transforms = {
      "full_name": str.upper,
      "town": lambda s: s[:3],
      "latitude": str,
      "longitude": str
  }

  remap_and_transform(data, rules, transforms)

Erwartetes Ergebnis:
  {
      "identifier": 1,
      "full_name": "ALICE",
      "address": {
          "town": "Ber",
          "geo": {"latitude": "52.52", "longitude": "13.405"}
      },
      "tags": [
          {"tag_key": "role", "tag_value": "admin"},
          {"tag_key": "dept", "tag_value": "engineering"}
      ]
  }

Beachte: Die "**"-Regel matcht zwar auf alle Dicts, aber sie verliert überall dort,
wo eine spezifischere Regel existiert. Sie würde nur greifen, wenn es ein Dict gäbe,
auf das keine andere Regel passt.
```

### Erwartung: Modellversagen

GPT-4o scheitert hier an der Kombination mehrerer Anforderungen, die einzeln jeweils lösbar wären:

1. **Pfad-Tracking durch die Rekursion.** Der aktuelle Pfad muss bei jedem Abstieg korrekt mitgeführt werden. Bei Listen muss der Pfad den Listen-Key enthalten, aber die Liste selbst darf kein eigenes Pfad-Segment erzeugen. Dicts innerhalb von Listen matchen auf `"tags.*"`, nicht auf `"tags.0"`.

2. **Wildcard-Matching mit Spezifitäts-Vorrang.** Für jedes Dict müssen alle matchenden Regeln gefunden und nach Spezifität sortiert werden. Nur die spezifischste Regel wird angewendet. GPT-4o implementiert stattdessen typischerweise entweder alle Regeln kumulativ, die erste matchende Regel, oder fehlerhaftes Wildcard-Matching.

3. **`**`-Globbing.** Die Doppel-Wildcard muss null oder mehr Ebenen matchen – also auch das Top-Level-Dict. GPT-4o implementiert `**` häufig als „eine oder mehr Ebenen" und vergisst den Null-Fall.

### Objektive Fehleranzeichen

- `"key"/"value"` statt `"tag_key"/"tag_value"` in den Tags → Spezifität von `"tags.*"` nicht erkannt
- `"lat"/"lon"` statt `"latitude"/"longitude"` → Pfad `"address.geo"` nicht korrekt gematcht
- Transforms nicht angewendet oder auf falsche Keys angewendet
- Crash bei Listen-Traversierung

---

## Modellgrenze

**Pfadbasiertes Pattern-Matching mit Spezifitäts-Vorrang in rekursiver Baumtransformation.**

GPT-4o kann einfache rekursive Transformationen und einfaches Pattern-Matching jeweils gut umsetzen. Die Kombination aus Pfad-Tracking durch verschachtelte Dicts und Listen, Wildcard-Matching mit `*` und `**`, spezifitätsbasierter Regelauswahl und korrekter Listen-Behandlung überfordert das Modell. Es löst typischerweise ein oder zwei dieser Constraints korrekt, aber nicht alle gleichzeitig.

**Warum Turn 1 und 2 nicht betroffen sind:** Beide verwenden ein einziges globales Mapping ohne Pfad-Tracking. Kein Wildcard-Matching, keine Regelauswahl.

**Was sich in Turn 3 ändert:** Mappings werden pfadabhängig. Wildcards erfordern Pattern-Matching. Mehrere Regeln können auf dasselbe Dict matchen, und nur die spezifischste darf gewinnen. Listen erfordern spezielle Pfad-Behandlung.
