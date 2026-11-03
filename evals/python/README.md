# Python development cases

These eight small, synthetic programs exercise Python-specific boundaries in the
standalone review skill. They are development examples, not mined upstream
patches, a held-out benchmark, or a measured accuracy claim.

Each file under `inputs/` runs offline with Python 3.11 or later:

```sh
python evals/python/inputs/01.py
```

`cases.json` contains target-level labels and rationales. A file can contain both
a weak test and valuable retained coverage. For a review exercise, give the agent
the input file and the ordinary request below. Do not provide `cases.json` or
`tests/test_python_cases.py`; those are the answer key and mutation witnesses.

```text
Use $slop-review-python to review these Python files for accumulated slop.
Report supported findings and the useful coverage that should remain.
Do not edit the input files.
```

Run the executable controls with:

```sh
python -m pytest -q tests/test_python_cases.py
```

The controls establish a passing baseline, then separately remove an await,
disable a database write, bypass an ownership guard, or change a shared fee
calculation. Weak tests stay green while the relevant independent checks fail.
Other controls check that public validation and capability contracts discriminate,
and that the specified routing contract survives removal of unreachable internal
fallbacks. All databases are temporary local SQLite files. These probes prove
only the contracts modeled here; they do not establish framework, ORM, remote
transport, or full application behavior.
