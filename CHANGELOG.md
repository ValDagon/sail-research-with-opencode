# Changelog

All notable changes to this project are documented in this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
