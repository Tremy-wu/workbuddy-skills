# skill-quality-gate — WorkBuddy 技能整理质量门禁

迁移自 [`staruhub/awesome-workbuddy`](https://github.com/staruhub/awesome-workbuddy) 的三道质量门禁，应用于本机 6994 个技能的整理流程。

## 迁移映射

| awesome-workbuddy | 本工具 | 作用 |
|---|---|---|
| `scripts/lint-awesome.mjs` (awesome-lint) | `skill_gate.py` 结构校验 | frontmatter / 必填字段 / 路径安全 |
| `.github/workflows/links.yml` (lychee) | `skill_gate.py --check-links` | URL 健康探测（带节流） |
| `prompts/runs/*.json` 双层门禁 | `skills-runs/` + `skills_manifest.json` | 哈希锁定 + review/verify 两档 |
| `docs/prompt-run-provenance.md` | `SKILL_RUN_SCHEMA.md` | "证明结果"方法论与披露原则 |

## 用法

```bash
# 1) 结构校验（review 模式，默认不探测链接，秒级）
python skill_gate.py --skills-dir C:/Users/Admin/.workbuddy/skills --mode review --report report.md

# 2) 链接健康（可选，较慢，会真实发请求）
python skill_gate.py --skills-dir <dir> --mode review --check-links --report report.md

# 3) 产出核验（verify 模式，要求 manifest 中全 approved）
python skill_gate.py --skills-dir <dir> --mode verify --manifest skills_manifest.json
```

## 门禁语义

- **ERROR（非零退出，阻断）**：缺 SKILL.md、路径不安全（穿越/符号链接）、缺必填 frontmatter 字段（`name` / `description`）。
- **WARN（软警告，不阻断）**：`description` 未含触发语义（场景/关键词），不利自动调用。

## 实测基线（2026-08-03，本机 6988 个技能目录）

| 指标 | 数值 |
|---|---|
| 达标准化门槛（name+description + 安全路径） | 1642 (23.5%) |
| 缺必填 frontmatter 字段 | 937 |
| 路径不安全（符号链接） | 21 |
| 触发语义偏弱（WARN） | 4825 |

结论：本机技能库标准化程度低，连用户自研的 `07-移动端开发专家` 也缺 `name/description`；`global-mandatory-rules` 是合格样本。建议先把自研技能补齐 frontmatter，再逐步治理外部技能。

## 接入 CI

非零退出码便于 GitHub Actions / 定时任务接入：ERROR 存在即失败。可对照 `links.yml` 的 `lychee-action` 编排周期巡检。

## 注意

- 遍历用 `os.listdir`（非系统 `find`），规避 Windows 非 ASCII 路径遗漏（全局规范 §三.6）。
- 链接探测为尽力而为，超时/限流可能导致误报，建议对结果人工复核后再定论。
