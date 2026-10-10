# slop-decisions

Model-assisted checks for code defects that depend on contracts and context:
failed work reported as success, tests that let broken behavior pass, unnecessary
repeated traversal, and related patterns. The initial rubrics and evaluation
set focus on Elixir. This is not an AI-authorship detector.

**Local models, OpenAI Decisions/Responses, and OpenRouter use the same checker
and evaluation pipeline.** Missing context, refusals, malformed output, and
failed requests remain unassessed. They never become clean results.

The project includes 14 named rubrics, 20 pinned development targets, seven
before/after pairs, executable behavioral witnesses, and published model runs.
See [measured results](docs/results.md) and the [evaluation contract](docs/evaluation.md).
Thresholds are experimental; the development set is too small for a deployment
precision claim.

## Install

Requires Python 3.11+. Install directly from GitHub; no PyPI release is assumed:

```sh
uv tool install git+https://github.com/samhavens/slop-decisions.git
slop-decisions
slop-decisions checks
```

For development:

```sh
git clone https://github.com/samhavens/slop-decisions.git
cd slop-decisions
uv sync --locked
uv run slop-decisions dataset
```

## Check your code

With a model already installed and served by Ollama:

```sh
slop-decisions check lib/my_app/orders.ex \
  --provider local --model qwen3:8b \
  --dimension success_shaped_failure \
  --lines 20:60 --related lib/my_app/repo.ex
```

Paths are relative to `--root` (the current directory by default). Omit `--lines`
to mark the whole file. Repeat `--dimension` and `--related` to choose checks and
supporting files. Multiple input files are allowed. The default check selection
is failure honesty, test discrimination, and repeated traversal. Input files
are explicit; the checker does not silently upload a whole repository.

Inspect a request without calling a model:

```sh
slop-decisions check examples/failure.ex --model qwen3:8b \
  --dimension success_shaped_failure --dry-run --format json
```

Use `--context target`, `window`, or `file` to control source selection. All source
is treated as untrusted evidence. `--max-checks` bounds the request plan, and
`--max-chars` rejects oversized context instead of truncating it.

### Providers

| Provider | Transport | Default base URL | Credential environment variable |
| --- | --- | --- | --- |
| `local` | Chat Completions | `http://127.0.0.1:11434/v1` | Optional `LOCAL_API_KEY` |
| `openai` | Decisions; `--api responses` or `--api chat` | `https://api.openai.com/v1` | `OPENAI_API_KEY` |
| `openrouter` | Chat Completions | `https://openrouter.ai/api/v1` | `OPENROUTER_API_KEY` |

The local adapter works with OpenAI-compatible servers such as Ollama, LM Studio,
llama.cpp, vLLM, and MLX. Choose their URL and installed model explicitly:

```sh
# LM Studio (start its server and load a model first)
slop-decisions check examples/failure.ex --model YOUR_LOADED_MODEL \
  --provider local --base-url http://127.0.0.1:1234/v1 --json-mode object

# OpenAI Decisions (set OPENAI_API_KEY in your environment first)
slop-decisions check examples/failure.ex --provider openai --model gpt-6-luna \
  --dimension success_shaped_failure

# OpenAI generative assessment, including a reason
slop-decisions check examples/failure.ex --provider openai --api responses \
  --model gpt-6-luna --dimension success_shaped_failure

# OpenRouter (set OPENROUTER_API_KEY first; use a model available to your account)
slop-decisions check examples/failure.ex --provider openrouter \
  --model openai/gpt-6-luna --dimension success_shaped_failure
```

`--json-mode schema` is the default for generative transports. For servers or
models without JSON Schema support, select `object` or `none`. Even in `none`
mode the returned JSON is validated. There is no automatic provider or format
fallback. Local requests never inherit a cloud API key. `--key-env` can name an
alternative variable; never pass the secret itself in arguments. Remote servers
require HTTPS; loopback servers may use HTTP. HTTP redirects are not followed.

Decisions uses two predicates: context sufficiency and defect probability.
The default context gate and warning threshold are both 0.8 and are **not
calibrated**. Generative probability estimates need separate calibration.
`--temperature` is omitted by default because some reasoning models reject it.
`--timeout`, `--retries`, and `--max-tokens` control request bounds.

Official protocol references: [Decisions](https://developers.openai.com/api/docs/guides/decisions),
[Responses structured output](https://developers.openai.com/api/docs/guides/structured-outputs),
[OpenRouter](https://openrouter.ai/docs/api/reference/overview),
[Ollama compatibility](https://docs.ollama.com/api/openai-compatibility).

## Run the eval

```sh
slop-decisions fetch
slop-decisions packet identity-partial --format json

# Preflight does not need a key or running server.
slop-decisions eval --provider local --model qwen3:8b \
  --out runs/local --dry-run --format json

slop-decisions eval --provider local --model qwen3:8b --out runs/local
slop-decisions eval --provider openai --model gpt-6-luna --out runs/decisions
slop-decisions eval --provider openai --api responses --model gpt-6-luna \
  --max-tokens 2000 --out runs/responses
slop-decisions eval --provider openrouter --model openai/gpt-6-luna --out runs/router
```

`fetch` downloads public files at pinned revisions and verifies their SHA256.
Downloaded source stays in an ignored cache under its upstream license. It is
not included in the wheel. See [provenance](THIRD_PARTY.md).

Use `--limit 3` for a bounded pilot, `--dimension NAME` to isolate a check, or
`--track semantic` to exclude preference and deterministic-baseline cases.
`--resume` reuses completed rows only when the request plan and labels match.
New runs refuse to overwrite existing output.

Saved artifacts contain settings, manifest/rubric snapshots, per-target results,
context hashes, latency, and provider-reported token usage. Cost is unknown when
the provider does not report it. Errors and abstentions remain in every report.

Score or sweep saved predictions without paying for another model call:

```sh
slop-decisions score runs/responses/predictions.jsonl --threshold 0.8 --format json
slop-decisions sweep runs/responses/predictions.jsonl \
  --thresholds 0.5,0.65,0.8,0.9,0.95 --format json
```

Score expects the whole selected split, counting missing predictions as
unassessed. For a bounded pilot use repeated `--case-id` flags to declare its
intended target set. For threshold tuning on a single dimension, use an explicit
case subset and its matching predictions. Sweeps refuse holdout labels.

Compare `--prompt minimal` with `examples`, then vary `--context` separately.
Supply `--rubrics custom.json` to experiment with different questions/examples.
Keep labels fixed. The [results](docs/results.md) include unsuccessful variants.

## Output and integration

Stdout defaults to TOON; `--format json` returns ordinary JSON. Progress goes to
stderr. Commands never prompt for input or install editor hooks.

| Exit code | Meaning |
| --- | --- |
| 0 | Command completed; for `check`, no warnings and all selected checks assessed |
| 1 | One or more checks/eval targets unassessed |
| 2 | Invalid arguments, configuration, data, or file/network preflight failure |
| 3 | `check` found warnings at the chosen threshold |
| 130 | Interrupted; completed eval rows can be resumed |

`eval` does not gate on accuracy. Inspect the report before choosing a CI policy.
Model findings require review; the tool does not modify source files.

Python API:

```python
from pathlib import Path
from slop_decisions.context import build_packet
from slop_decisions.providers import Provider, ProviderConfig
from slop_decisions.rubrics import load_rubrics

packet = build_packet(Path('.'), 'examples/failure.ex', 1, 10)
with Provider(ProviderConfig(provider='local', model='qwen3:8b')) as model:
    result = model.assess(packet, load_rubrics()['success_shaped_failure'])
print(result)
```

For offline tests, packaging, and Elixir witnesses, see [contributing](CONTRIBUTING.md).
