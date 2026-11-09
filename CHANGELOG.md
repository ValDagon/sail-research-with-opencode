# Changelog

All notable changes to this project are documented in this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.4] - 2026-11-09

### Changed

- The vision alias is now `kimi-k3.1-pro` (`moonshotai/Kimi-K3.1-Pro`), replacing `kimi-k2.6`, which Sail dropped from its model catalog. It costs 1.20 / 8.00 with a 0.15 cache read and declares `none`–`high` with a `high` fallback.
- DeepSeek V4.1 Flash 1017 is declared multimodal (`text` + `image`). Sail accepts image input on it, so screenshots no longer need a 36× more expensive Kimi call.
- GLM-5.3 context limit is 262,144 (verified on the wire with a 266,677-token request) and it now declares the `xhigh` variant Sail accepts.
- The routing rule sends image input to Flash first and keeps Kimi K3.1 Pro as the heavyweight vision fallback.

## [0.1.3] - 2026-11-03

### Fixed

- Routing reference now matches the current `opencode.json`: `build` runs `#high`, DeepSeek V4.1 Flash 1017 is configured with a 500,000-token window, and DeepSeek V4 Pro 0813 declares `none`–`high` explicitly.
- GLM-5.3 no longer advertises `none`; Sail rejects it with HTTP 400. The bare-model fallback is now `high`, not an absent field.

## [0.1.2] - 2026-10-24

### Added

- Simplified Chinese translation of the README (`README.zh-CN.md`), with language links on both pages.
- Localization section documenting that English is canonical and translations are kept in sync.
- CI check that both READMEs exist, link to each other, and keep the same number of code fences and section headings.

## [0.1.1] - 2026-10-24

### Added

- Key-handling material in step 1: exact `service set` argument order, the `service.json` location, and the measured fact that the service reads the key from that file instead of inheriting it from the shell.
- Troubleshooting section "Checking the key itself" with the three questions — stored, in effect, valid — plus a start-time versus mtime check and a direct Sail probe.

## [0.1.0] - 2026-10-24

### Added

- OpenCode skill for configuring SailResearch as a provider: service-environment credentials, V2 provider shape, model IDs and limits, reasoning-effort variants, completion windows, and agent routing.
- Reference provider block for GLM-5.3, Kimi K2.6, DeepSeek V4.1 Flash 1017, and DeepSeek V4 Pro 0813.
- Measured behavior table covering default variants, bare-model effort, GLM-5.3 `none`, and `flex` on Chat Completions.
- Troubleshooting guide with a verification ladder and a local request-capture sink.
