# Sail Research with OpenCode

An [OpenCode](https://opencode.ai) skill that configures [SailResearch](https://sailresearch.com) as a model provider end to end: provider registration, API key handling, pinned model IDs, reasoning-effort variants, completion windows, agent routing, and a wire-level debugging recipe.

[![validate](https://github.com/ValDagon/sail-research-with-opencode/actions/workflows/validate.yml/badge.svg)](https://github.com/ValDagon/sail-research-with-opencode/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Why this exists

Sail exposes an OpenAI-compatible Chat Completions API, so connecting it to OpenCode looks like a small config change. In practice the setup has several independent knobs, and two of them are easy to conflate:

- **Completion window** (`asap`, `balanced`, `flex`) is the scheduling class: latency and price.
- **Reasoning effort** (`none` … `max`) is the thinking budget.

A working setup also needs the API key in the OpenCode background service, explicit model IDs and limits, and a variant pinned on every agent. The skill captures a tested configuration and, more importantly, the diagnostic path for when the wire disagrees with the config.

## Install

Requirements: OpenCode V2 (tested with 2.0.28) and a SailResearch account with an API key.

### Global (recommended)

```sh
git clone https://github.com/ValDagon/sail-research-with-opencode.git \
  ~/.agents/skills/sail-research-with-opencode
```

`~/.agents/skills` is OpenCode's global compatibility path. The native path works too:

```sh
git clone https://github.com/ValDagon/sail-research-with-opencode.git \
  ~/.config/opencode/skills/sail-research-with-opencode
```

Update:

```sh
git -C ~/.agents/skills/sail-research-with-opencode pull
```

## Use

OpenCode advertises the skill automatically. Ask in plain language:

- "Connect SailResearch as an OpenCode provider."
- "Add GLM-5.3 with high reasoning effort and balanced scheduling."
- "Move my subagents to Flash at low effort."
- "Why does my Sail agent answer without reasoning?"

Or invoke it explicitly with `@sail-research-with-opencode`.

The skill walks through six steps, each with a completion check:

1. Put `SAIL_API_KEY` in the background service environment.
2. Register the `sailresearch` provider in V2 config shape.
3. Declare models with real upstream IDs, limits, capabilities, and costs.
4. Declare effort variants and pin every consumer with `#variant`.
5. Route agents across families and effort levels.
6. Verify resolved agents and inspect the actual request.

## What it produces

A provider block like this (see [`reference/provider.json`](reference/provider.json) for the full version):

```jsonc
"providers": {
  "sailresearch": {
    "name": "SailResearch",
    "env": ["SAIL_API_KEY"],
    "package": "@opencode/ai/providers/openai-compatible",
    "settings": { "baseURL": "https://api.sailresearch.com/v1" },
    "body": { "store": true },
    "models": {
      "glm-5.3": {
        "modelID": "zai-org/GLM-5.3",
        "headers": { "X-Sail-Completion-Window": "balanced" }
      }
    }
  }
}
```

Every consumer then names its effort explicitly:

```jsonc
{ "model": "sailresearch/glm-5.3#high" }
```

## Verified behavior

The claims that matter, measured against the live API and by capturing OpenCode's outgoing requests (OpenCode 2.0.28, 2026-10-24):

| Behavior | Result |
| --- | --- |
| Model with no `variants` array | OpenCode offers `low`, `medium`, `high` only |
| Explicit `variants` array | Replaces the default set; `none` must be declared |
| Bare GLM-5.3 | Sends no `reasoning_effort`; pin `#high` |
| GLM-5.3 with `none` | HTTP 400 `unsupported_reasoning_effort`; use `low` |
| `flex` on Chat Completions | HTTP 400; use `asap` or `balanced` |
| Key only in the shell | Invisible to the background service; `--standalone` only |
| Missing key | `Missing or invalid Authorization header` |

Full measurements and per-model variants: [`reference/routing.md`](reference/routing.md).

## Debugging the wire

`scripts/capture-request.py` is a local OpenAI-compatible sink. Point a throwaway project's `settings.baseURL` at it and run one OpenCode call; it records the exact `model`, `reasoning_effort`, and `X-Sail-Completion-Window` and answers `OK`. The full cookbook is in [`reference/troubleshooting.md`](reference/troubleshooting.md).

```sh
python3 scripts/capture-request.py --port 8765 --log /tmp/sail-request.jsonl
```

The script redacts `authorization` and `x-api-key` before writing the log.

## Repository layout

```text
.
├── SKILL.md                  # the skill OpenCode loads
├── reference/
│   ├── provider.json         # working provider block
│   ├── routing.md            # model table, agent routing, measurements
│   └── troubleshooting.md    # symptoms, checks, request-capture cookbook
├── scripts/
│   └── capture-request.py    # local request sink
├── .github/workflows/validate.yml
├── CHANGELOG.md
├── LICENSE
└── README.md
```

## Contributing

Issues and pull requests are welcome. Keep the measured-behavior table honest: re-measure when OpenCode or Sail changes, and say which version and date you used. Never paste API keys, full request headers, or session transcripts containing secrets.

This project is not affiliated with SailResearch or OpenCode.

## License

MIT © 2026 Valentin Kazantsev. See [`LICENSE`](LICENSE).
