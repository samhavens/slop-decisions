# Test review discovery

These cases test whether a reviewer finds problems in ordinary diffs without a
rule hint. Each case has related files and a Git base; one includes history that
explains a compatibility exception. The 21 authored cases cover nine new rules,
with nine findings, nine valid lookalikes, and three missing-contract cases.
They are development fixtures, not unseen production data.

## Run a comparison

Prepare separate arms with the same inputs. The default pilot has twelve cases:
the five priority rules each have a finding and a valid lookalike, plus two cases
with missing contracts. `--all` includes all 21.

```sh
uv run python scripts/skill_eval.py --destination /tmp/review-plain
uv run python scripts/skill_eval.py --destination /tmp/review-current --skill skills/slop-review
```

For an older skill, export its complete folder at a pinned commit and pass that
folder with `--skill`. Give each fresh reviewer only its arm's `request.txt` and
directory. Keep `cases.json`, source snapshots, witnesses and other arms hidden.
Use the same model, effort, tools, task order and budget. Do not include rule names
in the task. Let the reviewer read related files, local history and run local
probes. Keep inputs fixed and preserve raw `results.json` files.

Grade each finding against the cause and evidence in `cases.json`. A matching
rule name is insufficient; another name for the same supported cause is valid.
Record missed causes, unsupported extra findings, and missing-context responses
separately. Audit disagreements before making a performance claim. Keep original
labels and raw output when adding an adjudication. Report model settings, scope,
usage, execution limits and the number of trials with the results.

[The measured pilot](../../reports/discovery-2026-10-10/README.md) compares v0.6.0,
v0.7.0 and plain review. It uses one reviewer per arm; related cases share that
reviewer's context. This small pilot cannot establish a general accuracy gain.

## Verify the fixtures

```sh
uv run pytest -q tests/test_discovery.py
```

With Elixir installed, tests parse every snapshot and exercise actual fixture
code. Witnesses cover equivalent behavior, brittle assertions, private state
coupling, concurrent reservations, lost replies, captured data, two client
instances, macro behavior and downstream attempt counts. They use local stand-ins,
not real databases or carrier APIs. The reservation witness adds a barrier between
existing calls to select a legal interleaving. The capture witness inspects the
closure environment; it does not measure production memory or latency.

The abstraction and macro labels include maintenance judgment. The witnesses
establish behavior or a dependency, not the value of every proposed refactoring.
Keep these fixtures separate from the published API and calibration inputs.
