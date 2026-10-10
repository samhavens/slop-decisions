"""Small TOON output boundary; records and saved artifacts remain JSON."""

import json
import re


def scalar(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def toon(value, level=0):
    lines = []
    prefix = "  " * level
    for key, item in value.items():
        key = key if re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*", key) else scalar(key)
        if isinstance(item, dict):
            lines.append(f"{prefix}{key}:")
            if item:
                lines.extend(toon(item, level + 1))
        elif isinstance(item, list):
            # JSON-quoted strings and primitives in TOON inline arrays.
            if all(not isinstance(v, (dict, list)) for v in item):
                values = ",".join(scalar(v) for v in item)
                lines.append(f"{prefix}{key}[{len(item)}]:" + (f" {values}" if item else ""))
            else:
                lines.append(f"{prefix}{key}[{len(item)}]:")
                for row in item:
                    if isinstance(row, dict):
                        child = toon(row, level + 2)
                        lines.append(prefix + "  -" + (" " + child[0].lstrip() if child else ""))
                        lines.extend(child[1:])
                    else:
                        raise ValueError("nested arrays require --format json")
        else:
            lines.append(f"{prefix}{key}: {scalar(item)}")
    return lines


def emit(value, format="toon"):
    print(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)
        if format == "json"
        else "\n".join(toon(value))
    )
