# Sail Research 与 OpenCode

[English](README.md) | **简体中文**

一个 [OpenCode](https://opencode.ai) 技能，端到端地把 [SailResearch](https://sailresearch.com) 配置为模型提供商：注册提供商、处理 API 密钥、固定模型 ID、推理强度变体、完成窗口、智能体路由，以及请求级的调试方法。

[![validate](https://github.com/ValDagon/sail-research-with-opencode/actions/workflows/validate.yml/badge.svg)](https://github.com/ValDagon/sail-research-with-opencode/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 为什么需要这个技能

Sail 提供与 OpenAI 兼容的 Chat Completions API，所以接进 OpenCode 看起来只是改一点配置。实际上这套设置包含若干彼此独立的开关，其中两个特别容易被混为一谈：

- **完成窗口**（`asap`、`balanced`、`flex`）是调度等级：决定延迟与价格。
- **推理强度**（`none` … `max`）是思考预算。

一套可用的配置还需要把 API 密钥放进 OpenCode 的后台服务、写明显式的模型 ID 与限额，并给每个智能体固定一个变体。这个技能记录了一套经过验证的配置，更重要的是记录了当实际发出的请求与配置不一致时该怎么查。

## 安装

要求：OpenCode V2（已在 2.0.28 上测试），以及带 API 密钥的 SailResearch 账号。

### 全局安装（推荐）

```sh
git clone https://github.com/ValDagon/sail-research-with-opencode.git \
  ~/.agents/skills/sail-research-with-opencode
```

`~/.agents/skills` 是 OpenCode 的全局兼容路径。原生路径同样可用：

```sh
git clone https://github.com/ValDagon/sail-research-with-opencode.git \
  ~/.config/opencode/skills/sail-research-with-opencode
```

更新：

```sh
git -C ~/.agents/skills/sail-research-with-opencode pull
```

## 使用

OpenCode 会自动发现这个技能。用自然语言直接提问即可：

- “把 SailResearch 接成 OpenCode 的提供商。”
- “添加 GLM-5.3，高推理强度，balanced 调度。”
- “把我的子智能体换成低强度的 Flash。”
- “为什么我的 Sail 智能体回答时没有推理过程？”

也可以显式调用 `@sail-research-with-opencode`。

该技能分六步，每步都有完成判据：

1. 把 `SAIL_API_KEY` 放进后台服务的环境。
2. 以 V2 配置结构注册 `sailresearch` 提供商。
3. 用真实的上游 ID、限额、能力和价格声明模型。
4. 声明强度变体，并用 `#variant` 固定每一个调用方。
5. 按模型家族与强度等级路由智能体。
6. 核对解析后的智能体，并检查实际发出的请求。

## 产出内容

会得到这样一段 provider 配置（完整版本见 [`reference/provider.json`](reference/provider.json)）：

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

之后每个调用方都显式写明自己的强度：

```jsonc
{ "model": "sailresearch/glm-5.3#high" }
```

## 已验证行为

下面的结论都在真实 API 上测量过，并通过抓取 OpenCode 发出的请求得到确认（OpenCode 2.0.28，2026-10-24）：

| 行为 | 结果 |
| --- | --- |
| 未声明 `variants` 数组的模型 | OpenCode 只提供 `low`、`medium`、`high` |
| 显式声明 `variants` 数组 | 会替换默认集合；`none` 必须显式声明 |
| 未指定变体的 GLM-5.3 | 不发送 `reasoning_effort`；请固定为 `#high` |
| GLM-5.3 使用 `none` | HTTP 400 `unsupported_reasoning_effort`；请改用 `low` |
| 在 Chat Completions 上使用 `flex` | HTTP 400；请改用 `asap` 或 `balanced` |
| 密钥只放在 shell 中 | 后台服务看不到；仅 `--standalone` 可用 |
| 密钥放在 `service.json` 中 | 服务从文件读取，不从 shell 继承；对服务执行 `ps eww` 看不到 `SAIL_API_KEY` |
| 写入密钥 | 需执行 `opencode service restart` 后生效；请比较服务启动时间与文件修改时间 |
| 缺少密钥 | `Missing or invalid Authorization header` |

完整测量数据与各模型的变体见 [`reference/routing.md`](reference/routing.md)。

## 调试实际请求

`scripts/capture-request.py` 是一个本地 OpenAI 兼容接收端。把临时项目的 `settings.baseURL` 指向它，运行一次 OpenCode 调用；它会记录确切的 `model`、`reasoning_effort` 和 `X-Sail-Completion-Window`，并返回 `OK`。完整操作步骤见 [`reference/troubleshooting.md`](reference/troubleshooting.md)。

```sh
python3 scripts/capture-request.py --port 8765 --log /tmp/sail-request.jsonl
```

脚本在写入日志前会对 `authorization` 和 `x-api-key` 做脱敏。

## 仓库结构

```text
.
├── SKILL.md                  # OpenCode 加载的技能
├── reference/
│   ├── provider.json         # 可用的 provider 配置
│   ├── routing.md            # 模型表、智能体路由、测量数据
│   └── troubleshooting.md    # 症状、检查步骤、请求抓取指南
├── scripts/
│   └── capture-request.py    # 本地请求接收端
├── .github/workflows/validate.yml
├── CHANGELOG.md
├── LICENSE
├── README.md                 # 英文（基准版本）
└── README.zh-CN.md           # 简体中文
```

## 本地化

英文 README 是基准版本，[`README.zh-CN.md`](README.zh-CN.md) 是与它保持同步的完整译文。当你在其中一份里改动行为、测量结论或命令时，请同时改动另一份；如果译文暂时落后，请在 pull request 里说明，而不是留下无声的不一致。

## 贡献

欢迎 issue 与 pull request。请保持“已验证行为”表格诚实：OpenCode 或 Sail 发生变化时重新测量，并注明所用的版本与日期。绝不要粘贴 API 密钥、完整请求头，或包含密钥的会话记录。

本项目与 SailResearch、OpenCode 均无隶属关系。

## 许可证

MIT © 2026 Valentin Kazantsev。见 [`LICENSE`](LICENSE)。
