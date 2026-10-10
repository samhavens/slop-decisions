"""JUnit output for test runners; an unassessed check is an error, never a pass."""

import re
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


def outcome(row: dict, threshold: float) -> str:
    result = row["result"]
    if result["status"] == "unassessed":
        return "error"
    return "failure" if result["probability"] >= threshold else "pass"


def xml_text(value: object) -> str:
    # XML 1.0 cannot encode these controls, even as character references.
    return re.sub(r"[^\x09\x0a\x0d\x20-\ud7ff\ue000-\ufffd\U00010000-\U0010ffff]", "", str(value))


def prepare_junit(path: Path, inputs: list[Path]) -> None:
    if any(path.resolve() == source.resolve() for source in inputs):
        raise ValueError("--junit must not overwrite an input file")
    if path.exists() and not path.is_file():
        raise ValueError("--junit requires a file path")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryFile(dir=path.parent):
        pass  # Check that reports can be written before any model requests.


def write_junit(path: Path, results: list[dict], threshold: float) -> None:
    statuses = [outcome(row, threshold) for row in results]
    suite = ET.Element(
        "testsuite",
        {
            "name": "slop-decisions",
            "tests": str(len(results)),
            "failures": str(statuses.count("failure")),
            "errors": str(statuses.count("error")),
        },
    )
    for row, status in zip(results, statuses, strict=True):
        target = row["target"]
        case = ET.SubElement(
            suite,
            "testcase",
            {
                "classname": xml_text(target["path"]),
                "name": xml_text(row["dimension"]),
                "file": xml_text(target["path"]),
                "line": str(target["start_line"]),
            },
        )
        if status != "pass":
            result = row["result"]
            message = result.get("reason") or f"Defect probability {result['probability']:.3f}"
            node = ET.SubElement(case, status, {"message": xml_text(message)})
            node.text = xml_text(message)
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(suite)
    with tempfile.TemporaryDirectory(prefix=".slop-report-", dir=path.parent) as directory:
        temporary = Path(directory) / "report.xml"
        ET.ElementTree(suite).write(temporary, encoding="utf-8", xml_declaration=True)
        temporary.replace(path)
