# Use in tests and CI

Run the checker after your normal tests. A nonzero exit code fails the step:

```sh
mix test && slop-decisions check --changed origin/main --junit results/slop.xml
```

Use your test command in place of `mix test`. The checker uses OpenAI and all
14 rules by default. [Choose local or OpenRouter](models.md) with the same flags
used for a single file.

## Select changes

`--changed REF` compares your current files with the common ancestor of `HEAD`
and `REF`. It includes committed branch work, staged edits, unstaged edits,
and new files that Git does not ignore. Use `--changed` without a ref for local
changes since `HEAD`.

Only `.ex` and `.exs` files are selected. Each selected file is checked in full,
so a result can identify a defect outside the edited lines. Deleted and empty
files are listed as skipped. A run with no files to check passes without a model
request. Merge conflicts and missing history fail before any request.

Run from the Git root, or set `--root`. Fetch the base branch first. In a shallow
CI checkout, fetch the full history. Inspect the selected source without calls:

```sh
slop-decisions check --changed origin/main --dry-run --format json
```

Each file uses 14 checks by default. Use `--rule NAME` to select fewer rules,
or `--max-checks COUNT` to change the default limit of 200 checks.
Add `--related PATH` when a check needs a caller, helper, or contract.

## Read test results

`--junit PATH` writes one test case per file and rule. A warning is a failure.
An unassessed check is an error. This includes missing context, provider errors,
and invalid replies. The report does not turn an incomplete check into a pass.
Invalid inputs return exit code 2 without a JUnit report.

The command returns 0 for a pass, 3 for warnings, or 1 for unassessed checks.
See [all exit codes](usage.md#read-results). These results depend on the model;
read the [evaluation limits](results.md) before making this a required merge check.

For GitHub Actions, copy [the workflow](../examples/github-actions.yml) to
`.github/workflows/slop.yml`. Add `OPENAI_API_KEY` as a repository secret.
The workflow checks pull requests from branches in your repository and uploads
the JUnit file. It skips fork pull requests, which do not receive that secret.

## Run through ExUnit

Copy [slop_test.exs](../examples/slop_test.exs) to your project's `test/` directory.
Keep model calls separate from routine test runs: add `exclude: [:slop]` to
the existing `ExUnit.start` call in `test/test_helper.exs`.

```elixir
ExUnit.start(exclude: [:slop])
```

Include the check when needed:

```sh
SLOP_BASE=origin/main mix test --include slop
```

For a local model:

```sh
SLOP_BASE=origin/main SLOP_PROVIDER=local SLOP_MODEL=qwen3:8b \
  mix test --include slop
```

`SLOP_BASE` defaults to `HEAD`. Use `SLOP_BASE_URL` for another model server.
The example allows five minutes for the model checks; change its timeout if needed.
See [ExUnit's test setup](https://hexdocs.pm/ex_unit/ExUnit.html) for test configuration.
