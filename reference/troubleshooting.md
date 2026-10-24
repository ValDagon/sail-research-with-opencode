# Troubleshooting

Check in this order: service environment → model list → agent variant → wire request. Most Sail failures are one of those four.

## Symptoms

| Symptom | Cause | Fix |
| --- | --- | --- |
| `Missing or invalid Authorization header` | The background service has no `SAIL_API_KEY`, or the provider's `env` name does not match the variable | Set it with `opencode service set env SAIL_API_KEY <key>`, restart, re-check `service get`. A `--standalone` run needs the key exported in that shell instead. |
| `Model unavailable: sailresearch/<alias>` | Alias absent or disabled, provider inactive, missing credential, or the model key does not match | Check `opencode models \| grep sailresearch`; compare the `models` map key, not `modelID`; check the service key. |
| `Variant unavailable for sailresearch/<alias>: <variant>` | The variant is not in the model's array and not in the default `low`/`medium`/`high` set | Declare it in `variants`, or use `low`/`medium`/`high`. |
| HTTP 400 `unsupported_reasoning_effort` on GLM | GLM-5.3 cannot disable reasoning; `none` is invalid | Use `low`, GLM's lowest native tier. |
| HTTP 400: `completion_window "flex" is only available for background responses ... or Batch work` | `flex` on Chat Completions | Use `asap` or `balanced`; reserve `flex` for background Responses or Batch. |
| Answers arrive without reasoning | Bare GLM sends no `reasoning_effort`; bare Kimi does the same; a low variant may think very little | Pin `#high` on the consumer and compare. `/thinking` only controls display, not effort. |
| Request seems to hang | A `balanced` request waits in Sail's queue; a synchronous stream stays open while it waits | Expected for long-horizon work. Use `asap` for interactive latency. |
| HTTP 503 `model_capacity_unavailable` | `asap` waits briefly, then fails instead of queueing | Honor `Retry-After`; retry, or move the work to `balanced`. |
| HTTP 503 `service_overloaded` | Sail is overloaded before accepting the request | Honor `Retry-After` and retry. |
| Only `low`/`medium`/`high` variants appear | The model has no explicit `variants` array | Add the full array you want; an explicit array replaces the default set. |
| Config edit seems ignored | Config normally reloads automatically; a stale session may hold its model | Run `/reload`; check `opencode debug config` for the winning source. |
| Session cost displays zero | `cost` is missing or zero on the model | Add input, output, and cache-read prices from Sail pricing. |
| Extra Flash requests after a run | If your `title` agent runs on Flash `#minimal`, it generates a title in a separate request | Expected; not a leak in the main agent's routing. |
| `service set` reports the command cancelled | The service restarted underneath the CLI | Check `opencode service get` first; repeat the write only if the key is missing. |

## Verification ladder

Run these in order; the first one that disagrees with the routing table is the failure.

```sh
# 1. The service sees the key (keys only, never values)
opencode service get | jq '.env | keys'

# 2. The provider exposes the aliases
opencode models | grep sailresearch

# 3. Every agent resolves to the intended model and variant
opencode debug agents | jq '.[] | select(.model.providerID == "sailresearch") | {id, model}'

# 4. A live call returns text
opencode run --thinking --model 'sailresearch/deepseek-v4.1-flash-1017#high' 'Say OK'
```

For a `--standalone` run, the shell must carry the key:

```sh
SAIL_API_KEY=<key> opencode run --standalone --model 'sailresearch/glm-5.3#high' 'Say OK'
```

## Capture the exact request

Use the sink when OpenCode's behavior disagrees with the configuration: it is an OpenAI-compatible local server that records the request and answers `OK`. No Sail traffic, no real key needed.

```sh
# 1. Start the sink (from this skill's directory)
python3 scripts/capture-request.py --port 8765 --log /tmp/sail-request.jsonl &

# 2. Point a throwaway project at it
mkdir -p /tmp/sail-probe/.opencode
cat > /tmp/sail-probe/.opencode/opencode.json <<'JSON'
{
  "$schema": "https://opencode.ai/config.json",
  "providers": {
    "sailresearch": {
      "settings": { "baseURL": "http://127.0.0.1:8765/v1" }
    }
  }
}
JSON

# 3. Send one request; the sink accepts any key
cd /tmp/sail-probe
SAIL_API_KEY=test opencode run --standalone --model 'sailresearch/deepseek-v4.1-flash-1017#minimal' 'Say OK'

# 4. Read the wire fields
jq -c '{model: .body.model, effort: .body.reasoning_effort, window: .headers["x-sail-completion-window"], store: .body.store}' /tmp/sail-request.jsonl
```

The project config overrides only `settings.baseURL`; the global provider's models, headers, and body still merge in. `--model` overrides the build agent for the run.

Expect more than one line in the log: OpenCode also calls the `title` agent, so a request tagged `deepseek-ai/DeepSeek-V4.1-Flash-1017` with `reasoning_effort: minimal` is the title, not the model you asked for. Match the `model` field.

The sink redacts `authorization` and `x-api-key` in its log. Keep it that way; never paste a real key into a probe.

## Escalation

If the captured request matches the intended fields but Sail still fails, compare it with the [Chat Completions API reference](https://docs.sailresearch.com/api-reference/chat-completions-api/create-a-chat-completion.md) and the [support matrix](https://docs.sailresearch.com/support.md). If the request OpenCode sends differs from the config, fix the config first; the provider is doing what it was told.
