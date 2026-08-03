# 技能「证明结果」Manifest Schema（迁移自 awesome-workbuddy run.json）

> 对应 `prompts/runs/<id>-<runner>-<date>/run.json`。
> 目标：让高价值技能像提示词一样，每条都附带**可核验的产出证据 + 审核状态**，而非仅靠描述自证。

## 目录约定

```
skills-runs/
  <skill-id>-<runner>-<YYYYMMDD>/
    run.json        # 元数据 + 哈希锁定
    output.md       # 该技能一次真实调用的产出原文（UTF-8）
```

## run.json 字段（Schema v1，对齐 run.json Schema v2）

| 字段 | 含义 | 必填 |
|---|---|---|
| `schema_version` | 固定 `1` | ✅ |
| `run_id` | `<skill-id>-<runner>-<YYYYMMDD>` | ✅ |
| `skill_id` | 技能目录名 | ✅ |
| `skill_sha256` | 完整 SKILL.md 文本 sha256（检测漂移） | ✅ |
| `record_sha256` | 本 manifest 记录的 sha256 | ✅ |
| `runner` | `{product, model, mode, surface}` 如实记录运行者 | ✅ |
| `executed_at` | ISO8601 UTC，禁止未来时间 | ✅ |
| `conversation_url` | 真实运行深链（可空，但需说明） | ⚠️ |
| `input_mode` | `prompt_only` / `synthetic_demo` | ✅ |
| `input_summary` | 输入来源说明 | ✅ |
| `network_research` | bool，是否联网核验 | ✅ |
| `outcome` | `full` / `partial` | ✅ |
| `output_file` | 产出文件名（同目录） | ✅ |
| `output_sha256` | 产出原文 sha256 | ✅ |
| `review` | `{status, reviewer, reviewed_at, scope[]}` | ✅ |
| `limitations` | 限制与披露数组 | ✅ |

## 双层门禁（关键）

- **review 模式**：接受 `review.status = pending` 或 `approved`，只做结构/哈希/路径审核，不改变状态。用于日常整理。
- **verify 模式**：只接受 `approved`，用于"发布/对外宣称"。`pending` 记录禁止进入生产。

## 严格拒绝项（验证器）

- 技能数不等于记录数、重复或缺失
- `skill_sha256` / `record_sha256` / `output_sha256` 漂移
- 路径穿越、绝对路径、符号链接、额外文件
- 冒充 WorkBuddy 的运行者或不精确标识
- 非法/未来执行时间、空白 limitations
- `synthetic_demo` 缺首行声明，或其 outcome 非 `partial`
- `pending` 进入生产发布

## 披露原则（直接沿用）

`synthetic_demo` 的产出首行必须声明：`> 演示输入：合成数据，不代表真实客户/生产结果`。
审核仅确认"可作为效果预览"，不代表真实业务输入或外部事实已核验。
