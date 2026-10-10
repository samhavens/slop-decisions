"""Build source-only packets. Never accept evaluation metadata as model context."""

import hashlib
import json
from pathlib import Path


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()
    ).hexdigest()


def safe_path(root: Path, path: str) -> Path:
    candidate = (root / path).resolve()
    if Path(path).is_absolute() or not candidate.is_relative_to(root.resolve()):
        raise ValueError("source path must stay inside the selected root")
    return candidate


def source_fragment(path: str, text: str, start: int, end: int) -> dict:
    lines = text.splitlines()
    if type(start) is not int or type(end) is not int or not 1 <= start <= end <= len(lines):
        raise ValueError(f"invalid line range for {path}: {start}:{end} ({len(lines)} lines)")
    return {
        "path": path,
        "start_line": start,
        "end_line": end,
        "content": "\n".join(lines[start - 1 : end]),
    }


def build_packet(
    root: Path,
    path: str,
    start: int,
    end: int,
    *,
    mode: str = "file",
    related: tuple[str, ...] = (),
    max_chars: int = 100_000,
) -> dict:
    text = safe_path(root, path).read_text(encoding="utf-8")
    source_fragment(path, text, start, end)  # Validate even in whole-file mode.
    if mode not in {"target", "window", "file"}:
        raise ValueError("context mode must be target, window, or file")
    lo, hi = start, end
    if mode == "file":
        lo, hi = 1, len(text.splitlines())
    elif mode == "window":
        lo, hi = max(1, start - 40), min(len(text.splitlines()), end + 40)
    files = [source_fragment(path, text, lo, hi)]
    for other in dict.fromkeys(related):
        if other == path:
            continue
        body = safe_path(root, other).read_text(encoding="utf-8")
        files.append(source_fragment(other, body, 1, len(body.splitlines())))
    packet = {"target": {"path": path, "start_line": start, "end_line": end}, "files": files}
    if len(json.dumps(packet, ensure_ascii=False)) > max_chars:
        raise ValueError("context exceeds character budget; select narrower context explicitly")
    return packet
