"""Parse every authored packet and execute the separate behavioral witnesses."""

import json
import subprocess
import tempfile
from pathlib import Path

from slop_decisions.calibration import load_cases
from slop_decisions.context import digest


def main():
    cases = load_cases(Path("calibration/cases.jsonl"))
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        for case in cases:
            source = "\n".join(f["content"] for f in case["packet"]["files"])
            path = Path(tmp) / "sample.exs"
            # Parse all packets, including intentionally incomplete-context examples.
            path.write_text(source)
            command = [
                "elixir",
                "-e",
                "Code.string_to_quoted!(File.read!(hd(System.argv())))",
                str(path),
            ]
            parsed = subprocess.run(command, capture_output=True, text=True, timeout=30)
            if parsed.returncode:
                raise RuntimeError(case["case_id"] + "\n" + parsed.stderr)
            if case["witness"] is not None:
                path.write_text(source + "\n" + case["witness"])
                tested = subprocess.run(
                    ["elixir", str(path)], capture_output=True, text=True, timeout=30
                )
                if tested.returncode:
                    raise RuntimeError(case["case_id"] + "\n" + tested.stderr)
            results.append(
                {
                    "case_id": case["case_id"],
                    "parsed": True,
                    "witness": "passed" if case["witness"] is not None else "source_review",
                }
            )
    print(json.dumps({"suite_hash": digest(cases), "cases": results}, indent=2))


if __name__ == "__main__":
    main()
