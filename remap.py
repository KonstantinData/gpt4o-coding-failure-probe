def remap_and_transform(obj, rules, transforms, _path=()):
    if isinstance(obj, dict):
        # Find the winning rule for this dict's path
        mapping = _select_rule(rules, _path)

        result = {}
        for k, v in obj.items():
            new_key = mapping.get(k, k)
            if isinstance(v, (dict, list)):
                result[new_key] = remap_and_transform(v, rules, transforms, _path + (k,))
            elif new_key in transforms:
                result[new_key] = transforms[new_key](v)
            else:
                result[new_key] = v
        return result

    if isinstance(obj, list):
        # List items get a '*' path segment so that "tags.*" matches dicts inside tags[]
        return [remap_and_transform(item, rules, transforms, _path + ("*",)) for item in obj]

    return obj


def _select_rule(rules, path):
    """Return the mapping dict of the most specific matching rule."""
    best_mapping, best_score = {}, None
    for rule in rules:
        score = _match(rule["path"], path)
        if score is not None:
            if best_score is None or score < best_score:
                best_score = score
                best_mapping = rule["mapping"]
    return best_mapping


def _match(pattern_str, path):
    """Return a specificity score (lower = more specific) or None if no match.

    Score = number of wildcard segments (* counts as 1, ** counts as 2).
    """
    if pattern_str == ".":
        return 0 if len(path) == 0 else None

    parts = pattern_str.split(".")
    return _match_parts(parts, list(path), 0)


def _match_parts(parts, path, wildcards):
    if not parts and not path:
        return wildcards
    if not parts:
        return None
    if parts[0] == "**":
        # ** matches zero or more segments
        # Try consuming 0, 1, 2, ... segments from path
        rest = parts[1:]
        for i in range(len(path) + 1):
            result = _match_parts(rest, path[i:], wildcards + 2)
            if result is not None:
                return result
        return None
    if not path:
        return None
    if parts[0] == "*":
        return _match_parts(parts[1:], path[1:], wildcards + 1)
    if parts[0] == path[0]:
        return _match_parts(parts[1:], path[1:], wildcards)
    return None


if __name__ == "__main__":
    # Turn 1 – einfaches Remapping (using rules format for unified function)
    t1 = remap_and_transform(
        {"name": "Alice", "address": {"city": "Berlin"}},
        [{"path": ".", "mapping": {"name": "full_name"}},
         {"path": "address", "mapping": {"city": "town"}}],
        {},
    )
    assert t1 == {"full_name": "Alice", "address": {"town": "Berlin"}}, f"Turn 1 failed: {t1}"

    # Turn 2 – Remapping + Transforms
    t2 = remap_and_transform(
        {"name": "Alice", "age": 29.7, "address": {"city": "Berlin"}},
        [{"path": ".", "mapping": {"name": "full_name"}},
         {"path": "address", "mapping": {"city": "town"}}],
        {"full_name": str.upper, "town": lambda s: s[:3]},
    )
    assert t2 == {"full_name": "ALICE", "age": 29.7, "address": {"town": "Ber"}}, f"Turn 2 failed: {t2}"

    # Turn 3 – pfadbasiert + Wildcards + Spezifität
    data = {
        "id": 1,
        "name": "Alice",
        "address": {
            "city": "Berlin",
            "geo": {"lat": 52.52, "lon": 13.405},
        },
        "tags": [
            {"key": "role", "value": "admin"},
            {"key": "dept", "value": "engineering"},
        ],
    }
    rules = [
        {"path": "**",          "mapping": {"key": "k", "value": "v"}},
        {"path": ".",           "mapping": {"name": "full_name", "id": "identifier"}},
        {"path": "address",     "mapping": {"city": "town"}},
        {"path": "address.geo", "mapping": {"lat": "latitude", "lon": "longitude"}},
        {"path": "tags.*",      "mapping": {"key": "tag_key", "value": "tag_value"}},
    ]
    transforms = {
        "full_name": str.upper,
        "town": lambda s: s[:3],
        "latitude": str,
        "longitude": str,
    }

    t3 = remap_and_transform(data, rules, transforms)
    expected_t3 = {
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
    assert t3 == expected_t3, f"Turn 3 failed: {t3}"

    print("All turns passed.")
