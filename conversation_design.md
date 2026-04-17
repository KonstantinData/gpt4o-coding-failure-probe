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

### Erwartete Wirkung (Modellversagen)

GPT-4o wird mit hoher Wahrscheinlichkeit an der Kombination mehrerer Anforderungen scheitern:

1. **Pfad-Tracking durch die Rekursion:** Der aktuelle Pfad muss bei jedem rekursiven
   Abstieg korrekt mitgeführt werden. Bei Listen muss der Pfad den Listen-Key enthalten,
   aber die Liste selbst nicht als Pfad-Segment zählen (die Dicts IN der Liste matchen
   auf "tags.*", nicht auf "tags.0" oder "tags.list.*").

2. **Wildcard-Matching mit Spezifitäts-Vorrang:** Das Modell muss für jedes Dict alle
   matchenden Regeln finden, dann nach Spezifität sortieren (wenigste Wildcards gewinnt),
   und nur die Gewinner-Regel anwenden. GPT-4o implementiert häufig entweder:
   - alle matchenden Regeln kumulativ (statt nur die spezifischste), oder
   - die erste matchende Regel (statt die spezifischste), oder
   - Wildcards falsch (z.B. "*" matcht mehrere Ebenen, oder "**" wird nicht korrekt
     als "null oder mehr Ebenen" implementiert).

3. **"**"-Globbing:** Die Doppel-Wildcard "**" muss null oder mehr Ebenen matchen.
   Das bedeutet, sie matcht auf JEDES Dict im Baum. GPT-4o implementiert "**" häufig
   als "genau eine oder mehr Ebenen" und vergisst den Null-Fall (Top-Level).

### Objektive Fehleranzeichen

- `"key"/"value"` statt `"tag_key"/"tag_value"` in den Tags (Spezifität von "tags.*"
  nicht erkannt, "**" gewinnt fälschlich)
- `"key"/"value"` statt `"k"/"v"` UND statt `"tag_key"/"tag_value"` (Wildcards
  funktionieren gar nicht)
- `"lat"/"lon"` statt `"latitude"/"longitude"` (Pfad "address.geo" nicht korrekt gematcht)
- Transforms nicht angewendet oder auf falsche Keys angewendet
- Crash bei Listen-Traversierung

---

## Identifizierte Modellgrenze

**Pfad-basiertes Pattern-Matching mit Spezifitäts-Vorrang in rekursiver Baumtransformation.**

GPT-4o kann einfache rekursive Transformationen und einfaches Pattern-Matching separat gut
implementieren. Die Kombination von:
- Pfad-Tracking durch verschachtelte Dicts und Listen,
- Wildcard-Matching mit "*" und "**",
- Spezifitäts-basierter Regelauswahl (nicht erste, nicht alle, sondern spezifischste),
- korrekte Behandlung von Listen (Pfad geht durch, aber Liste ist kein Pfad-Segment)

überfordert das Modell typischerweise. Es löst ein oder zwei der Constraints korrekt,
aber nicht alle gleichzeitig.

**Warum Turn 1 und Turn 2 nicht betroffen sind:**
- Turn 1: Ein einziges globales Mapping, kein Pfad-Tracking.
- Turn 2: Ein einziges globales Mapping + einfache Transforms. Kein Pfad-Tracking.

**Was sich in Turn 3 ändert:**
- Mappings werden pfadabhängig mit Wildcards.
- Spezifitäts-Vorrang erfordert Vergleich aller matchenden Regeln.
- Listen erfordern spezielle Pfad-Behandlung.
- "**" erfordert korrektes Globbing über null oder mehr Ebenen.
