# Codex review results

Codex with `slop-review` v0.6.0 matched **18/20 public-source labels** and
**56/56 authored-case labels**. It made no false warnings. It abstained on two
public cases that the dataset labels as issues.

| Set | Labels matched | Issues found | False warnings on clean code | Missing context identified |
| --- | ---: | ---: | ---: | ---: |
| Public source | 18/20 | 6/8 | 0/12 | No missing-context labels |
| Published calibration holdout | 56/56 | 14/14 | 0/28 | 14/14 |

The public run passed 5/7 before/after pairs. It scored 15/16 on the semantic
track, 1/2 on the design-preference track, and 2/2 on duplicate setup.

## The two abstentions

- **Logflare egress:** the reviewer identified telemetry emitted before a send
  can fail, but could not determine whether the event counts attempts or
  successful delivery. The packet includes the failure path; it omits the metric
  contract and consumers. Failed messages are already marked as failed.
- **Boundary export option:** the reviewer found distinct behavior controlled
  by the option, but lacked the configuration contract needed to call it
  unnecessary. This label is explicitly a design preference, not a proven bug.

Both abstentions count against the score. The labels remain unchanged.

## What the score supports

Four reviewers used **`gpt-6-astra`, max reasoning**, with the frozen skill and
source packets. Each case named one rule to check. Reviewers had no labels or
parent history, and related examples went to different reviewers. They could
run isolated probes but could not retrieve more repository context. See the
[review request](request.txt) and [fixed plan](plan.md).

The [best prior API run](../2026-10-10/README.md) also scored 18/20, using
`gpt-6-luna`. It found 7/8 issues with one false warning. This skill run found
6/8 with no false warnings. The models and workflows differ; there is no matched
comparison with Codex without the skill.

These are small development sets with one trial per case. The authored holdout
was already public and shares its author with the rules. This is a regression
check, not a fresh holdout or an estimate of production accuracy. The 76 cases
cover the original 14 rules; the three new rules have separate
[Phoenix examples](../../evals/phoenix/README.md).

[Scores and disagreements](report.json) · [Source packets and labels](cases.json) ·
[Model, usage, hashes, and review order](run.json) ·
[Review batch 1](batch-1-results.json) · [2](batch-2-results.json) ·
[3](batch-3-results.json) · [4](batch-4-results.json)

The four reviewers used 218,235 uncached input tokens, 3,042,816 cached input
tokens, and 47,174 output tokens. This uses normal Codex allowance. No dollar
charge was reported; parent orchestration is excluded from these counts.
