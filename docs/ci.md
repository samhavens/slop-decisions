# Use with tests and CI

Keep your normal tests and static checks as required CI steps. Use
[the Codex skill](codex.md) to review changed code after those checks. Turn
confirmed defects and test gaps into regression tests that CI can run without a
model. A model review is not a test pass.

In an existing Codex session:

```text
$slop-review Review changes against origin/main. Use the test results above and verify each finding.
```

To start a separate review from a script, install the skill, sign in to Codex,
and run this from your project's Git root:

```sh
codex exec --sandbox read-only \
  --output-last-message slop-review.md \
  '$slop-review Review changes against origin/main. Do not edit source files.'
```

Fetch the base branch before the review. The command starts a new Codex session
and uses its model allowance. A zero exit code means the session finished;
it does not mean the code passed review. Read or upload `slop-review.md` as a
review artifact. Tests that need build output may not run in a read-only sandbox;
the report must say which evidence is missing.

For a hosted runner, use the [Codex GitHub Action](https://developers.openai.com/codex/github-action/)
with the same skill and prompt. See [Codex automation](https://developers.openai.com/codex/noninteractive/)
for authentication and output options.

For explicit per-rule API experiments, including JUnit and ExUnit, use
[the API test setup](api-ci.md). It supports local models, OpenAI, and OpenRouter.
