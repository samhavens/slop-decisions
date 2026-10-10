# Skill evaluation contract

Freeze the v0.6.0 skill and score it against all 20 public-source targets and all
56 cases in the published calibration holdout. Report these sets separately.
The published holdout is a regression set here, not a new unseen benchmark.

Use independent Codex reviewers without parent history. Give each reviewer the
skill, selected rule, original source packet, and a neutral case identifier.
Exclude labels, original case names, witnesses, split names, and prior results.
Assign related revisions and authored variants to different reviewers. Each
reviewer handles a batch; this is not one independent model call per case.

Require a finding, no finding, or missing context, with source evidence for each
case. Keep all results, including abstentions and disagreements. Freeze the raw
responses before revealing labels. Do not tune the skill or rerun errors to
improve the score. Check disputed evidence against the original source and label
contract, without silently changing the scored verdict.

Report defect recall, false warnings, missing-context handling, before/after
pairs, and rule coverage. Preserve packet and skill hashes for reproduction.
Do not interpret a source-review score as production accuracy or evidence that
the skill improves Codex without a matched no-skill comparison. Prior API scores
use a different model and request workflow. No provider checker calls are needed.
