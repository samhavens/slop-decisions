# Review skill: ordinary diffs

Plain review, the previous skill and the upgraded skill each found all five target
problems. This pilot does **not** show that the upgrade detects more than plain
Astra review.

The upgrade adds nine rules and specific ways to test suspected problems. In this
run it added executable evidence for two maintenance findings that the other
reviewers supported by inspection. Use it to guide a review; do not treat this
small authored set as a measured accuracy guarantee.

## Results

Each reviewer used **gpt-6-astra, max reasoning** on the same twelve diffs, with
local tools and Git history. No reviewer received labels or a rule for each case.
All findings were checked against the source and recorded tool results.

| Outcome | Plain review | v0.6.0 | v0.7.0 |
| --- | ---: | ---: | ---: |
| Target problems found, with supported causes | 5/5 | 5/5 | 5/5 |
| Unambiguous clean changes without warnings | 4/4 | 4/4 | 4/4 |
| Missing-contract cases left undecided | 2/2 | 2/2 | 2/2 |
| Ambiguous API change (`change-02`) | Undecided | API hazard | No finding |
| Raw matches with frozen labels | 11/12 | 11/12 | 12/12 |

**The last row overstates the difference.** The fifth intended clean change
replaces `Export.csv/1` and `tsv/1` with `encode/2`, but supplies no callers or
compatibility policy. The abstraction is coherent. Whether removing those public
functions is safe is unresolved. The old skill demonstrated the removed calls
fail and reported an API hazard; plain review requested context. Neither response
establishes a detector error. The labels and all three raw reviews remain unchanged.

The five supported findings cover wrong unification, brittle tests, exposed
process state, a reservation race, and a duplicate shipment after retry. The new
reviewer also ran policy-specialization and private-state replacement probes.
Those probes strengthen the explanation; they do not add detections.

[Case audit](audit.json) · [Raw scores](scores.json) ·
[Plain review](plain-results.json) · [Previous skill](previous-results.json) ·
[Upgraded skill](upgraded-results.json)

## Time and usage

| Reviewer | Elapsed | Uncached input | Cached input | Output |
| --- | ---: | ---: | ---: | ---: |
| Plain | 4m 40s | 29,273 | 1,551,872 | 12,209 |
| v0.6.0 | 5m 05s | 32,679 | 1,422,464 | 12,675 |
| v0.7.0 | 5m 14s | 43,869 | 1,348,992 | 14,828 |

Token counts are cumulative across tool turns, not unique prompt lengths.
Cached and uncached columns partition input; output includes reasoning tokens.
These are reviewer-session counts, excluding development and scoring. The runs
used normal Codex usage and made no separate checker API calls. They are not an
API invoice. The upgrade used more uncached input and output in this trial.

## Scope and reproduction

This is one trial per reviewer on development fixtures authored with the upgrade.
The twelve cases share a context within each reviewer; paired examples are not
independent trials. All three reviewers had fresh contexts, the same task order,
model settings, tools and source. Inputs, labels and skills were frozen at
[`5840b79`](https://github.com/samhavens/slop-decisions/commit/5840b7935705ff684bee3b80b8622a7797aff85e)
before review and were unchanged afterward. No reviewer was rerun or tuned on
these results.

The full fixture set has 21 diffs for all nine additions. The other four rules
have executable regression checks but no blind review result here. Local carrier
models and controlled interleavings establish these examples; they do not test a
real carrier, database deployment, or production workload.

[Run settings, usage and hashes](run.json) · [Plain request](plain-request.txt) ·
[Skill request](skill-request.txt) · [Verification plan](plan.md) ·
[Prepare and score a run](../../evals/discovery/README.md) ·
[Earlier guided-rule eval](../skill-2026-10-10/README.md)
