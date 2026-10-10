# Case format

Use these fixtures to test check behavior and the calibration tools.
They are small authored examples, not a sample of production code.
Do not use their published holdout as a new unseen test.

`cases.jsonl` contains one JSON object per line:

| Field | Meaning |
| --- | --- |
| `case_id` | Unique case name. |
| `family` | Group for related code and revisions. A family must stay in one split. |
| `split` | `calibration` or `holdout`. |
| `dimension` | A name from `slop-decisions checks`. |
| `expected` | `defect`, `clean`, or `unassessable`. |
| `packet` | Model input: `target` plus `files`. See the example below. |
| `basis` | Label evidence: `executable` or `source_review`. |
| `rationale` | Reason for the label. Not sent to the model. |
| `witness` | Elixir assertion code, or `null`. Not sent to the model. |

```json
{
  "target": {"path": "sample.ex", "start_line": 1, "end_line": 3, "focus": "run/1"},
  "files": [{"path": "sample.ex", "start_line": 1, "end_line": 3,
    "content": "defmodule Sample do\n  def run(x), do: x\nend\n"}]
}
```

`build_suite.py` is the source of the published fixtures. It makes 112 cases:
one defect, its repair, a valid look-alike, and a missing-source case for each check in each split.
The required patterns come from the check definitions. The same author wrote the labels and rubrics;
there was no independent human label review. Semantic labels can be disputed.

Forty-five cases have executable assertions. Some show output equivalence;
others show a failure path or reject a simple test mutant. Assertions do not prove
performance bounds or subjective design claims. The remaining labels depend on source review.
The framework fixtures refer to
[Plug 1.16 header access](https://github.com/elixir-plug/plug/blob/v1.16.0/lib/plug/conn.ex#L661)
and [Elixir 1.18 regular expressions](https://hexdocs.pm/elixir/1.18.4/Regex.html).

Commit your labels and [selection policy](../docs/calibration-plan.md) before model calls.
Keep labels, witnesses, case names, and split names out of `packet`.
The loader rejects duplicate IDs, identical source across splits, and families that cross splits.
The fitter accepts complete calibration runs only. Refusals and failed requests stay unassessed.
