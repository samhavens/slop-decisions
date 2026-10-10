# slop-decisions

Tests can pass while code hides errors or repeats work.
slop-decisions uses a model to find these defects before you merge Elixir code.

Use a [local model](docs/models.md#local-models), [OpenAI](docs/models.md#openai),
or [OpenRouter](docs/models.md#openrouter).

## Start

Install Python 3.11 or later and [uv](https://docs.astral.sh/uv/getting-started/installation/).

```sh
uv tool install git+https://github.com/samhavens/slop-decisions.git
```

Start [Ollama and load a model](docs/models.md#local-models). Then run:

```sh
slop-decisions check lib/orders.ex \
  --model qwen3:8b --dimension success_shaped_failure
```

Replace `lib/orders.ex` with your file. Examine each result before you change code.

## Guides

- [Choose checks and read results](docs/usage.md)
- [Compare models](docs/run-eval.md) · [Calibrate thresholds](docs/calibration.md)
- [Results and limits](docs/results.md)
- [Contribute](CONTRIBUTING.md) · [MIT license](LICENSE)
