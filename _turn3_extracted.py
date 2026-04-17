def match_path(path, pattern):
    """
    Hilfsfunktion, um Pfad-Matches zwischen dem aktuellen Pfad und dem Pattern zu überprüfen.
    """
    path_parts = path.split('.')
    pattern_parts = pattern.split('.')
    
    i, j = 0, 0
    while i < len(path_parts) and j < len(pattern_parts):
        if pattern_parts[j] == '**':
            return True
        elif pattern_parts[j] == '*':
            i += 1
            j += 1
        elif path_parts[i] == pattern_parts[j]:
            i += 1
            j += 1
        else:
            return False
    return i == len(path_parts) and j == len(pattern_parts)

def find_best_rule(path, rules):
    """
    Suche die beste Matching-Regel für einen gegebenen Pfad.
    """
    matches = [rule for rule in rules if match_path(path, rule['path'])]
    if not matches:
        return None
    # Sortiere Treffer nach Spezifität: weniger Wildcards sind spezifischer
    matches.sort(key=lambda rule: (rule['path'].count('**'), rule['path'].count('*'), rules.index(rule)))
    return matches[0]

def remap_and_transform_helper(obj, path, rules, transforms):
    """
    Rekursive Hilfsfunktion zur Verarbeitung von Objekten basierend auf Pfad-basierten Regeln.
    """
    if isinstance(obj, dict):
        rule = find_best_rule(path, rules)
        if rule:
            mapping = rule['mapping']
        else:
            mapping = {}
        
        new_dict = {}
        for key, value in obj.items():
            new_key = mapping.get(key, key)
            new_value = remap_and_transform_helper(value, f"{path}.{new_key}", rules, transforms)
            if new_key in transforms and not isinstance(new_value, (dict, list)):
                new_value = transforms[new_key](new_value)
            new_dict[new_key] = new_value
        return new_dict

    elif isinstance(obj, list):
        return [remap_and_transform_helper(element, f"{path}.*", rules, transforms) for element in obj]

    else:
        return obj

def remap_and_transform(obj, rules, transforms):
    return remap_and_transform_helper(obj, '.', rules, transforms)

# Beispieldaten und Regeln
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
    {"path": "**", "mapping": {"key": "k", "value": "v"}},
    {"path": ".", "mapping": {"name": "full_name", "id": "identifier"}},
    {"path": "address", "mapping": {"city": "town"}},
    {"path": "address.geo", "mapping": {"lat": "latitude", "lon": "longitude"}},
    {"path": "tags.*", "mapping": {"key": "tag_key", "value": "tag_value"}}
]

transforms = {
    "full_name": str.upper,
    "town": lambda s: s[:3],
    "latitude": str,
    "longitude": str
}

# Funktion aufrufen
result = remap_and_transform(data, rules, transforms)
print(result)


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
