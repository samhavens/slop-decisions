# Set up a model

Source files go to the provider you select. Use a local server to keep source on your machine.
The default provider is OpenAI, with `gpt-6-luna` and the Decisions API.
“Jev-style” describes a decision about a defined condition; this package does not call the Jev API.

## Local models

Start an OpenAI-compatible server and load a model.
The default URL is `http://127.0.0.1:11434/v1`, for Ollama.

Install [Ollama](https://ollama.com/download).
Start the app, or run `ollama serve` in a separate terminal.
Download the model:

```sh
ollama pull qwen3:8b
```

Run a code check:

```sh
slop-decisions check lib/orders.ex --provider local --model qwen3:8b \
  --rule success_shaped_failure
```

For another server, supply its URL and the name of its loaded model:

```sh
slop-decisions check lib/orders.ex --provider local \
  --base-url http://127.0.0.1:8080/v1 --model MODEL_NAME \
  --rule success_shaped_failure
```

The URL must include `/v1`. Replace `MODEL_NAME` with your model name.
If the server requires a key, set `LOCAL_API_KEY`.
`--provider local` requires `--model`; it never selects a cloud model for you.

Servers such as LM Studio, llama.cpp, vLLM, and MLX can use this connection type.
See [Ollama's API guide](https://docs.ollama.com/api/openai-compatibility) for its supported options.

## OpenAI

Set `OPENAI_API_KEY` in your environment. Use `--model` to change the default model.
For a result with a written reason, use Responses:

```sh
slop-decisions check lib/orders.ex --provider openai --api responses \
  --model gpt-6-luna --rule success_shaped_failure
```

For predicate probabilities, use `--api decisions`. This is the OpenAI default.
Use `--api chat` for Chat Completions.

Decisions also asks whether the supplied code is sufficient for the check.
If that probability is below `--context-threshold`, the result is `unassessed`.
The fallback is 0.8. A [calibration study](calibration.md) tested both thresholds;
the fitted profile failed validation. Use `--calibration` only with a passing profile.

See OpenAI's [Decisions guide](https://developers.openai.com/api/docs/guides/decisions)
and [structured output guide](https://developers.openai.com/api/docs/guides/structured-outputs).

## OpenRouter

Set `OPENROUTER_API_KEY` in your environment.
Replace `MODEL_ID` with a model ID from OpenRouter:

```sh
slop-decisions check lib/orders.ex --provider openrouter \
  --model MODEL_ID --rule success_shaped_failure
```

OpenRouter uses Chat Completions. See its [API guide](https://openrouter.ai/docs/api/reference/overview).

## Request options

For Responses or Chat Completions, the default is `--json-mode schema`.
If the model does not support JSON Schema, try `object` or `none`.
The checker still requires a valid JSON result in either mode.

| Option | Use |
| --- | --- |
| `--base-url URL` | Select a different server. Include `/v1`. |
| `--key-env NAME` | Select the environment variable that contains the key. |
| `--timeout SECONDS` | Set the request timeout. The default is 60 seconds. |
| `--retries COUNT` | Set the retry limit. The default is one retry. |
| `--max-tokens COUNT` | Limit the generated reply. The default is 1,200 tokens. |
| `--temperature VALUE` | Set a temperature only if the model supports it. |

Remote servers require HTTPS. Local servers can use HTTP.
The checker does not follow redirects or change providers after a failed request.
Local requests do not use cloud keys unless you explicitly select one with `--key-env`.
