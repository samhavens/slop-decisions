# Threshold study plan

Freeze this plan and the case labels before model requests. Do not change them
in response to holdout scores.

Scope: OpenAI Decisions, `gpt-6-luna`, the current fourteen checks, the `examples`
prompt, and complete source packets. Thresholds belong to this exact request
contract. They must not transfer to another model, API, prompt, or check bank.

Add an authored Elixir suite with separate calibration and holdout families.
Each check has a defect, its repair, a hard negative, and a case with insufficient
source in each split. Keep related revisions in one family and one split.
Expected answers and witnesses stay outside model input. Run executable witnesses
for behavioral claims; mark judgments that depend on a stated code-design policy.
These fixtures test the check contracts. They are not a random sample of user code.
Keep the original public-source set as a separate development regression check.

Keep both raw predicate scores, including scores below the context gate.
Keep refusals and failed requests as unassessed. Never infer a missing score.

Select the context gate from 0.00, 0.05, ..., 1.00. Require no more than 10% of
insufficient-context cases to receive an assessment. Among eligible gates,
maximize coverage of sufficient-context cases; break ties with the higher gate.
Require at least 70% coverage of sufficient-context cases.

With that gate fixed, select the warning threshold from the same grid. Minimize
`5 * false_warnings + missed_defects`. A missed defect includes an abstention on
a positive case. The five-to-one cost favors fewer false alarms in code review.
Break ties with the higher warning threshold. Report the old 0.8/0.8 policy too.

Save and hash the selected profile before any holdout model request. Test it once
on the untouched families. Ship it only if holdout coverage is at least 70%,
unsafe context acceptance is at most 10%, and review cost is no worse than the
old defaults. Otherwise publish the failed result without relabeling or tuning
on the holdout. Report per-check counts, uncertainty, and raw-score reliability.
Threshold selection does not establish calibrated probability values.

Start with three calibration cases to verify the protocol. Cap the main study
at 112 authored cases plus the 20 existing development cases. A single Decisions
trial uses input tokens only. At the documented rate of $0.10 per million input
tokens, the expected cost is below $1. Stop on repeated request failures.

Verification before release: tests for censored-score retention, split/family
isolation, threshold tie rules, unknown handling, profile compatibility, explicit
overrides, and end-to-end checker application. Recompute every saved score,
run the witnesses, build the wheel, and require CI to pass.

[Decisions API and pricing](https://developers.openai.com/api/docs/guides/decisions)
