---
version: "1.0"
generated: "2026-07-22"
---

# Appendix: json_select

`metawtf/json_select.py` is a single pure function: given a parsed JSON dict
and a dotted key like `payload.count`, return the scalar at that path or raise
`JsonSelectError`. It exists apart from `field_extract` because it walks dict
keys, not object attributes.

```python
def select_json_value(data, key: str):
    value = data
    parts = key.split(".")
    for index, part in enumerate(parts):
        if not isinstance(value, dict) or part not in value:
            walked = ".".join(parts[:index]) or "<root>"
            raise JsonSelectError(f"{part!r} not found on {walked} (key {key!r})")
        value = value[part]
    if isinstance(value, (str, int, float)):
        return value
    raise JsonSelectError(f"key {key!r} did not resolve to a scalar: {value!r}")
```

Two details worth noting:

- The error message names the path prefix that *did* resolve (`walked`), so a
  typo three levels deep points at the right level.
- `bool` passes the scalar check because it subclasses `int`; `None`, lists,
  and nested objects are rejected — only plottable scalars reach a CSV cell.
