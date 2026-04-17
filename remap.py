def remap_and_transform(obj, mapping, transforms):
    if isinstance(obj, dict):
        return {
            mapping.get(k, k): (
                transforms[mapping.get(k, k)](v)
                if mapping.get(k, k) in transforms and not isinstance(v, (dict, list))
                else remap_and_transform(v, mapping, transforms)
            )
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [remap_and_transform(item, mapping, transforms) for item in obj]
    return obj


if __name__ == "__main__":
    # Turn 1 – einfaches Remapping
    t1 = remap_and_transform(
        {"name": "Alice", "address": {"city": "Berlin"}},
        {"name": "full_name", "city": "town"},
        {},
    )
    assert t1 == {"full_name": "Alice", "address": {"town": "Berlin"}}, f"Turn 1 failed: {t1}"

    # Turn 2 – Remapping + Transforms
    t2 = remap_and_transform(
        {"name": "Alice", "age": 29.7, "address": {"city": "Berlin"}},
        {"name": "full_name", "city": "town"},
        {"full_name": str.upper, "town": lambda s: s[:3]},
    )
    assert t2 == {"full_name": "ALICE", "age": 29.7, "address": {"town": "Ber"}}, f"Turn 2 failed: {t2}"

    # Turn 3 – zirkuläres Mapping
    t3 = remap_and_transform(
        {"a": 1, "b": 2, "c": 3, "nested": {"a": 10, "b": 20}},
        {"a": "b", "b": "c", "c": "a"},
        {"b": lambda x: x * 100},
    )
    assert t3 == {"b": 100, "c": 2, "a": 3, "nested": {"b": 1000, "c": 20}}, f"Turn 3 failed: {t3}"

    print("All turns passed.")
