# Tremy WorkBuddy Skills

腾讯 WorkBuddy 自研 / 迁移技能精选合集，由 Tremy.Wu 维护。每个技能均含标准 `SKILL.md`，可直接拷入 WorkBuddy 技能目录使用。

> 本仓库为精选子集（已脱敏，不含内部运营规范）。原始技能库见本地 `~/.workbuddy/skills/`。

## 安装

将 `skills/<技能目录>/` 整体复制到你的 WorkBuddy 技能目录：

```bash
# 用户级（跨项目）
cp -r skills/07-移动端开发专家 "$HOME/.workbuddy/skills/"

# 或项目级
cp -r skills/07-移动端开发专家 "<项目>/.workbuddy/skills/"
```

重启 / 刷新 WorkBuddy 后技能即生效。

## 技能索引

- **07-移动端开发专家** — 
- **Schedule** — Program recurring or one-time tasks. User defines what to do, skill
- **openclawpanel** — Control an OpenClaw LED panel (64x32 HUB75 on ESP32-S3) over HTTP —
- **scrcpy-claw** — >
- **zhiyierxing-auto-phone** — Product-grade deployment and operation skill for Zhipu
- **wendao-partner-qclaw-skill** — 当用户发起任意旅行相关问询时，包含但不限于：预订酒店、机票查询、火车票查询、景点推荐、寻找当地特色玩乐、目的地查询、行程规划、美食住宿攻略、签证、查询旅游攻略、获取旅行建议等场景，
- **openclaw-session-cleanup** — Diagnose and stabilize long-running OpenClaw deployments that
- **qclaw-skill-creator** — Guide for creating effective skills. This skill should be used when
- **qclaw-cron-skill** — >
- **qclaw-env** — OpenClaw skill 全链路环境诊断与安装工具。安装任何 CLI、命令行工具、包管理器、运行时环境时必须使用此
- **qclaw-rules** — |

## 质量门禁（质量工具）

`quality-gate/` 提供一套迁移自 [awesome-workbuddy](https://github.com/staruhub/awesome-workbuddy) 的技能整理质量门禁：结构校验 + 链接健康 + 产出证据双层核验，可本地批量跑数千个技能。详见 `quality-gate/README.md`。

## 提示词范式

`prompts/PROMPT_PARADIGMS.md` — 对 awesome-workbuddy 100 条提效 Prompts 的结构拆解与 5 个可复用范式。

## License

CC0 1.0 Universal（公共领域）。