---
name: sail-research-with-opencode
description: Configure SailResearch (Sail) as an OpenCode provider end to end — register the provider, store the API key in the background service, declare models and reasoning-effort variants, choose balanced/asap completion windows, route agents with #variant, and diagnose failed or reasoning-free Sail requests. Use when connecting Sail or adding a Sail model in OpenCode, tuning reasoning effort or completion windows, or fixing Model unavailable, unsupported_reasoning_effort, a flex 400, or answers that arrive without reasoning.
---

# Sail Research with OpenCode

Sail exposes an OpenAI-compatible Chat Completions API. OpenCode reaches it through a custom provider. The setup is a handful of independent wire fields, and most failures come from conflating two of them: the **completion window** and the **reasoning effort**.

## Two knobs

| Knob | What it controls | OpenCode field | Wire field | Values |
| --- | --- | --- | --- | --- |
| Completion window | Scheduling class: latency and price | model `headers["X-Sail-Completion-Window"]`, or `body.metadata.completion_window` | header, or `metadata.completion_window` | `asap`, `balanced`, `flex` |
| Reasoning effort | Thinking budget | model `settings.reasoningEffort`, selected with `#variant` | `reasoning_effort` | `none`, `minimal`, `low`, `medium`, `high`, `xhigh`, `max` |

`asap` is the low-latency default. `balanced` queues work for cheaper capacity and suits agents. `flex` is the cheapest and only works on background Responses or Batch requests; Chat Completions rejects it with HTTP 400. Set a window on every Sail model; `balanced` is the right default for agent work.

Reasoning effort is per model. Not every model accepts every level, and `none` is a real request that some models refuse. A bare model with no variant uses its `settings.reasoningEffort` fallback; with no fallback, OpenCode sends no `reasoning_effort` at all.

## Procedure

### 1. Put the key in the service environment

OpenCode's TUI and `run` talk to the background service. The service starts from its own environment, so a key exported in the current shell reaches only `--standalone` runs.

```sh
opencode service set env SAIL_API_KEY '<key>'
opencode service restart
opencode service get | jq '.env | keys'   # keys only; never print the value
```

OpenCode stores it in `~/.config/opencode/service.json`; keep that file out of version control and out of the transcript.

Done when `service get` lists `SAIL_API_KEY`. If `service set` reports the command cancelled during a service restart, check `service get` before repeating the write.

### 2. Register the provider

Merge the `providers.sailresearch` object from [reference/provider.json](reference/provider.json) into `~/.config/opencode/opencode.json`. Preserve every unrelated provider, agent, and MCP server.

The V2 shape is `providers` → `package` → `settings`:

```jsonc
"providers": {
  "sailresearch": {
    "name": "SailResearch",
    "env": ["SAIL_API_KEY"],
    "package": "@opencode/ai/providers/openai-compatible",
    "settings": { "baseURL": "https://api.sailresearch.com/v1" },
    "body": { "store": true },
    "models": { /* ... */ }
  }
}
```

Sail's own "Using OpenCode with Sail" page still shows the V1 shape (`provider`, `npm`, `options`, `id`). Do not paste it into a V2 config; use this file's shape.

Done when `opencode models | grep sailresearch` lists the model aliases and `opencode debug config` shows the provider document.

### 3. Declare models with the real IDs and limits

Each entry needs the upstream `modelID`, the OpenCode alias as the map key, `capabilities`, `limit`, a completion-window header, and `cost` so OpenCode can price the session. Use `balanced` for agent work and `asap` for interactive latency; the header value is the whole switch. [reference/routing.md](reference/routing.md) carries the working table; when adding a model, copy an existing entry and replace every field from Sail's model catalog.

Use the server's real upstream ID. `deepseek-v4.1-flash-1017` selects the pinned checkpoint `deepseek-ai/DeepSeek-V4.1-Flash-1017`; the unsuffixed `deepseek-ai/DeepSeek-V4.1-Flash` is a different, moving checkpoint.

Done when each new model answers a one-line run:

```sh
opencode run --model 'sailresearch/<alias>#<variant>' 'Reply with OK'
```

### 4. Declare variants, then pin every consumer

`settings.reasoningEffort` on the model is only the bare-model fallback. The `variants` array is what `#variant` can select.

- A model with no `variants` array gets OpenCode's default set: `low`, `medium`, `high`.
- An explicit `variants` array **replaces** that default set. List every level the model should offer, including the default ones.
- `none` must be declared explicitly; the default set does not include it.
- GLM-5.3 refuses `none` with HTTP 400 `unsupported_reasoning_effort`. Its lowest native tier is `low`.

Select a variant in every agent, command, or run that touches Sail:

```jsonc
{ "model": "sailresearch/glm-5.3#high" }
```

In `opencode.json` this is `agents.<id>.model`; in an agent Markdown file it is the `model:` frontmatter field.

A bare `sailresearch/glm-5.3` sends no `reasoning_effort`; a bare `sailresearch/deepseek-v4-pro-0813` sends its `high` fallback; a bare Flash uses its `low` fallback. The variant is what makes each consumer's intent explicit.

Done when `opencode debug agents` shows every Sail consumer with the intended `variant`, and none is bare.

### 5. Route the agents

The reference routing is in [reference/routing.md](reference/routing.md). Its logic:

- Keep plan and review on different model families so one family's blind spots do not carry from plan into review: GLM-5.3 for planning, DeepSeek V4 Pro for review.
- Put written-plan bulk work, search, compaction, and one-line utility calls on Flash at the lowest effort that still does the job.
- In the reference routing, the main `build` agent stays on the subscription-covered `opencode-go` model and Sail carries the subagents. Without that subscription, point `build` at a Sail model.
- Use Kimi K2.6 only when the task needs image input.

Done when every agent in the routing table resolves to the intended provider, model, and variant.

### 6. Verify on the wire

```sh
opencode debug agents | jq '.[] | select(.model.providerID == "sailresearch") | {id, model}'
opencode models | grep sailresearch
opencode run --thinking --model 'sailresearch/glm-5.3#high' 'Say OK'
```

`/thinking` and `--thinking` only display reasoning blocks; they do not set effort. Run once with `#minimal` or `#none` and once with `#high` to see the difference.

When the wire itself is in doubt, capture the request: [reference/troubleshooting.md](reference/troubleshooting.md) has a local sink cookbook that prints the exact `model`, `reasoning_effort`, and `X-Sail-Completion-Window` OpenCode sends.

Done when the resolved agents match the table, a live run returns text, and the captured request shows the intended effort and window.

## Reference

- [reference/provider.json](reference/provider.json) — the working `sailresearch` provider block.
- [reference/routing.md](reference/routing.md) — model table, agent routing, measured behavior.
- [reference/troubleshooting.md](reference/troubleshooting.md) — symptom → cause → fix, and the request-capture cookbook.
- [scripts/capture-request.py](scripts/capture-request.py) — local OpenAI-compatible sink for wire inspection.
