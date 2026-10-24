# Models and routing

The prices below are the values configured in `opencode.json` at the time of writing. Treat them as configuration, not eternal truth; re-check [Sail pricing](https://docs.sailresearch.com/pricing.md) and the [model catalog](https://docs.sailresearch.com/models.md) when adding or re-pricing a model. Accurate `cost` fields drive OpenCode's session price display.

## Model table

| OpenCode alias | Upstream `modelID` | Context / output | Input | Bare default | Selectable variants | Configured $/M in / out / cache read |
| --- | --- | --- | --- | --- | --- | --- |
| `glm-5.3` | `zai-org/GLM-5.3` | 200,000 / 128,000 | text | none — field absent | default `low`, `medium`, `high` | 0.50 / 2.50 / 0.12 |
| `kimi-k2.6` | `moonshotai/Kimi-K2.6` | 262,144 / 65,536 | text + image | none — field absent | default `low`, `medium`, `high` | 0.45 / 3.00 / 0.20 |
| `deepseek-v4.1-flash-1017` | `deepseek-ai/DeepSeek-V4.1-Flash-1017` | 200,000 / 128,000 | text | `low` | declared `none`, `minimal`, `low`, `medium`, `high` | 0.07 / 0.22 / 0.005 |
| `deepseek-v4-pro-0813` | `deepseek-ai/DeepSeek-V4-Pro-0813` | 200,000 / 128,000 | text | `high` | default `low`, `medium`, `high` | 0.74 / 2.22 / 0.03 |

The aliases are pinned checkpoints. Keep the date suffix and never silently swap in the unsuffixed Sail ID; that entry can move under you.

## Agent routing

| Agent | Model | Variant | Job |
| --- | --- | --- | --- |
| `build` | `opencode-go/deepseek-v4.1-flash` | `max` | Main coding, subscription-covered |
| `plan` | `sailresearch/glm-5.3` | `high` | Planning; GLM family |
| `planner` | `sailresearch/glm-5.3` | `high` | Cross-repo or unmapped planning |
| `reviewer` | `sailresearch/deepseek-v4-pro-0813` | `high` | Review on a second family |
| `worker` | `sailresearch/deepseek-v4.1-flash-1017` | `low` | Bulk edits behind a written plan |
| `explore` | `sailresearch/deepseek-v4.1-flash-1017` | `minimal` | Broad search and multi-file reading |
| `general` | `sailresearch/deepseek-v4.1-flash-1017` | `medium` | Multi-step work outside plan/review |
| `compaction` | `sailresearch/deepseek-v4.1-flash-1017` | `low` | Session compaction |
| `title` | `sailresearch/deepseek-v4.1-flash-1017` | `minimal` | Session titles |
| `summary` | `sailresearch/deepseek-v4.1-flash-1017` | `minimal` | Session summaries |
| `strix` | `sailresearch/glm-5.3` | `high` | Security agent (optional; requires Strix) |

Rules behind the table:

- **Pin every Sail consumer.** The variant is what makes each consumer's effort explicit. GLM sends nothing without it, Pro falls back to `high`, Flash to `low`, Kimi to nothing.
- **Different families for plan and review.** Planning runs on GLM-5.3; review runs on DeepSeek V4 Pro.
- **Cheap work at low effort.** Search, bulk edits, compaction, titles, and summaries do not need a thinking budget.
- **`#max` belongs to `opencode-go`.** Sail agents top out at `#high` in the reference routing, even though Sail accepts `xhigh` and `max` on GLM-5.3, Flash, and Pro. Keeping one convention makes routing unambiguous. Without an OpenCode Go subscription, move `build` to `sailresearch/deepseek-v4.1-flash-1017#high` and leave the rest unchanged.
- **Kimi only for vision.** In the reference routing it has no agent slot; select it ad hoc when a task needs image input.

## Adding a model

1. Find the exact upstream ID in Sail's model catalog or `GET /v1/models`.
2. Add an entry under `providers.sailresearch.models`: alias, `modelID`, `name`, `capabilities`, `limit`, `headers`, `cost`.
3. Add a `variants` array only if the default `low`/`medium`/`high` set is insufficient. An explicit array replaces the default set, so list every level the model should offer.
4. Pin a consumer to `sailresearch/<alias>#<variant>`, or select it ad hoc with the same reference.
5. Verify with `opencode models | grep sailresearch` and a one-line `opencode run`.

## Measured behavior

Measured on 2026-10-24 with OpenCode 2.0.28, by capturing OpenCode's outgoing requests and by calling Sail's Chat Completions endpoint directly with the configured models.

| Observation | Result |
| --- | --- |
| Bare Pro request | `reasoning_effort: high` on the wire |
| Bare Flash request | `reasoning_effort: low` on the wire |
| Bare GLM request | `reasoning_effort` absent |
| Bare Kimi request | `reasoning_effort` absent |
| Flash `#minimal` request | `reasoning_effort: minimal`, `X-Sail-Completion-Window: balanced`, `store: true` |
| Variant set with no `variants` array | `low`, `medium`, `high`; `none`, `minimal`, `xhigh`, `max` all fail with “Variant unavailable” |
| Variant set with Flash's explicit array | `none`, `minimal`, `low`, `medium`, `high`; `xhigh` and `max` unavailable |
| GLM `reasoning_effort: none` | HTTP 400 `unsupported_reasoning_effort`, message directs to `low` |
| `X-Sail-Completion-Window: flex` on Chat Completions | HTTP 400: flex is only for background Responses or Batch |
| `asap` and `balanced` on Chat Completions | Accepted |
| Trivial prompt, Pro bare | 0 reasoning tokens |
| Trivial prompt, Pro `#high` | 14 reasoning tokens |
| Trivial prompt, Flash `#minimal` | 0 reasoning tokens |
| Trivial prompt, Flash `#high` | 10 reasoning tokens |

Sail also accepts `xhigh` and `max` on GLM-5.3, Flash, and Pro through the API; the limitation is the variant list the reference configuration declares, not the provider.
