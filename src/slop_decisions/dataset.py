"""Pinned-source manifests and separately stored labels."""

import hashlib
import json
import re
import textwrap
from importlib.resources import files
from pathlib import Path
from urllib.parse import quote

import httpx

from slop_decisions.context import build_packet, safe_path, source_fragment


def read_jsonl(path) -> list[dict]:
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                row = json.loads(line)
            except ValueError as error:
                raise ValueError(f"invalid JSON on line {number}") from error
            if not isinstance(row, dict):
                raise ValueError(f"line {number} must be an object")
            rows.append(row)
    return rows


def data_file(name: str, directory: Path | None = None):
    return directory / name if directory else files("slop_decisions").joinpath("data/seed", name)


def load_dataset(directory: Path | None = None):
    sources = json.loads(data_file("sources.json", directory).read_text(encoding="utf-8"))
    targets = read_jsonl(data_file("targets.jsonl", directory))
    labels = read_jsonl(data_file("labels.jsonl", directory))
    validate(sources, targets, labels)
    return sources, targets, labels


def validate(sources, targets, labels):
    if not sources or not targets or not labels:
        raise ValueError("dataset cannot be empty")
    by_source = {}
    for source in sources:
        if (
            not re.fullmatch(r"[\w.-]+/[\w.-]+", source["repo"])
            or not re.fullmatch(r"[0-9a-f]{40}", source["revision"])
            or not re.fullmatch(r"[0-9a-f]{64}", source["sha256"])
        ):
            raise ValueError("sources require a repository, full commit SHA, and SHA256")
        safe_path(Path("/dataset"), source["path"])
        if source["id"] in by_source:
            raise ValueError("duplicate source id")
        by_source[source["id"]] = source
    by_target = {}
    repo_splits, group_splits = {}, {}
    for target in targets:
        case_id = target["case_id"]
        if case_id in by_target:
            raise ValueError("duplicate target id")
        by_target[case_id] = target
        src = by_source[target["source_id"]]
        if target["split"] not in {"dev", "calibration", "holdout"}:
            raise ValueError("unknown split")
        if (
            type(target["start_line"]) is not int
            or type(target["end_line"]) is not int
            or not 1 <= target["start_line"] <= target["end_line"]
        ):
            raise ValueError("invalid target range")
        for mapping, key in ((repo_splits, src["repo"]), (group_splits, target["group_id"])):
            if key in mapping and mapping[key] != target["split"]:
                raise ValueError("repository or PR family leaks across splits")
            mapping[key] = target["split"]
        for other in target["related"]:
            if (by_source[other]["repo"], by_source[other]["revision"]) != (
                src["repo"],
                src["revision"],
            ):
                raise ValueError("related source must come from the same pinned snapshot")
    seen = set()
    pairs = {}
    pair_labels = {}
    for label in labels:
        case_id = label["case_id"]
        if case_id in seen or case_id not in by_target or type(label["label"]) is not bool:
            raise ValueError("duplicate, unmatched, or non-boolean label")
        seen.add(case_id)
        target = by_target[case_id]
        if (label["dimension"], label["split"]) != (target["dimension"], target["split"]):
            raise ValueError("label and target disagree")
        if "track" in label and label["track"] != target["track"]:
            raise ValueError("label and target tracks disagree")
        if type(label["hard_negative"]) is not bool:
            raise ValueError("hard_negative must be boolean")
        if label["hard_negative"] and label["label"]:
            raise ValueError("hard negative must be negative")
        if label.get("pair_id"):
            pair = (label["dimension"], label["pair_id"])
            family = target["group_id"], target["split"]
            if pair in pairs and pairs[pair] != family:
                raise ValueError("pair crosses PR family or split")
            pairs[pair] = family
            pair_labels.setdefault(pair, []).append(label["label"])
    if seen != set(by_target):
        raise ValueError("every target needs a separate label")
    if any(len(values) != 2 or set(values) != {True, False} for values in pair_labels.values()):
        raise ValueError("each manifest pair needs exactly one positive and one negative")


def source_path(cache: Path, source: dict) -> Path:
    return safe_path(cache, f"{source['repo']}/{source['revision']}/{source['path']}")


def verify_source(cache: Path, source: dict) -> Path:
    path = source_path(cache, source)
    if hashlib.sha256(path.read_bytes()).hexdigest() != source["sha256"]:
        raise ValueError(f"source hash mismatch: {source['id']}")
    return path


def fetch_sources(sources: list[dict], cache: Path) -> dict:
    downloaded = cached = 0
    with httpx.Client(timeout=30, follow_redirects=False) as client:
        for source in sources:
            destination = source_path(cache, source)
            if destination.exists():
                verify_source(cache, source)
                cached += 1
                continue
            url = (
                f"https://raw.githubusercontent.com/{source['repo']}/{source['revision']}/"
                f"{quote(source['path'], safe='/')}"
            )
            response = client.get(url)
            if response.status_code != 200:
                raise ValueError(
                    f"source fetch returned HTTP {response.status_code}: {source['id']}"
                )
            if hashlib.sha256(response.content).hexdigest() != source["sha256"]:
                raise ValueError(f"download hash mismatch: {source['id']}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(response.content)
            downloaded += 1
    return {"sources": len(sources), "downloaded": downloaded, "cached_verified": cached}


def packet_for(target: dict, sources: list[dict], cache: Path, mode="file", max_chars=100_000):
    by_id = {s["id"]: s for s in sources}
    source = by_id[target["source_id"]]
    path = verify_source(cache, source)
    if target.get("extract_fixture"):
        # Do not send the enclosing test name or assert_issue/refute_issues oracle.
        fragment = source_fragment(
            "fixture.ex", path.read_text(encoding="utf-8"), target["start_line"], target["end_line"]
        )
        code = textwrap.dedent(fragment["content"])
        packet = {
            "target": {"path": "fixture.ex", "start_line": 1, "end_line": len(code.splitlines())},
            "files": [source_fragment("fixture.ex", code, 1, len(code.splitlines()))],
        }
        if len(json.dumps(packet)) > max_chars:
            raise ValueError("context exceeds character budget")
        return packet
    related = []
    if mode != "target":
        for other_id in target["related"]:
            other = by_id[other_id]
            verify_source(cache, other)
            related.append(other["path"])
    root = cache / source["repo"] / source["revision"]
    packet = build_packet(
        root,
        source["path"],
        target["start_line"],
        target["end_line"],
        mode=mode,
        related=tuple(related),
        max_chars=max_chars,
    )
    if target.get("focus"):
        packet["target"]["focus"] = target["focus"]
    if len(json.dumps(packet, ensure_ascii=False)) > max_chars:
        raise ValueError("context exceeds character budget")
    return packet
