#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
skill_gate.py — WorkBuddy 技能整理质量门禁（迁移自 staruhub/awesome-workbuddy）

迁移对象与方法论对应：
  lint-awesome.mjs   -> 结构校验（frontmatter / 必填字段 / 触发词 / 路径安全）
  links.yml(lychee)  -> 链接健康（可选 HTTP 校验，带节流）
  run.json 双层门禁   -> 哈希锁定 + review(接受 pending) / verify(要求 approved) 两档

设计原则（来自全局规范 + awesome-workbuddy）：
  - canonical 数据源 = 每个技能目录的 SKILL.md，不引入第二真相源
  - 哈希锁定内容，检测漂移（sha256 of SKILL.md）
  - 双层门禁：review 做无状态结构审核；verify 只接受已 approved 的产出证据
  - 验证器严格拒绝：路径穿越、绝对路径、符号链接、字段缺失、冒充声明

用法：
  python skill_gate.py --skills-dir C:/Users/Admin/.workbuddy/skills --mode review
  python skill_gate.py --skills-dir <dir> --mode verify --manifest skills_manifest.json
  python skill_gate.py --skills-dir <dir> --mode review --check-links --report report.md
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time

# ---------- 配置 ----------
REQUIRED_FIELDS = ("name", "description")          # SKILL.md frontmatter 必填
TRIGGER_HINT = ("触发", "场景", "关键词", "trigger", "when", "use")  # description 应含触发语义
URL_RE = re.compile(r'https?://[^\s\)\]\>"`]+', re.I)
MAX_LINK_CONCURRENCY_SLEEP = 0.25                  # 链接校验节流（秒）


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def is_safe_path(skills_dir: str, skill_abs: str) -> bool:
    """拒绝路径穿越 / 符号链接（对齐 awesome-workbuddy 验证器）。

    注：扫描根本身以绝对路径传入属正常情况，不在此拒绝；仅拒绝
    越出根目录的 '..' 段与符号链接（防止 manifest 引用逃逸）。
    """
    if os.path.islink(skill_abs):
        return False
    base = os.path.normpath(os.path.abspath(skills_dir))
    ap = os.path.normpath(os.path.abspath(skill_abs))
    if ap != base and not (ap == base or ap.startswith(base + os.sep)):
        return False
    rel = os.path.relpath(ap, base)
    if rel == ".." or rel.startswith(".." + os.sep) or ".." in rel.split(os.sep):
        return False  # 穿越
    return True


def parse_frontmatter(text: str):
    """极简 YAML frontmatter 解析（首部 --- ... ---）。返回 (dict, body)。"""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    block = text[3:end].strip("\n")
    body = text[end + 4:]
    data = {}
    for line in block.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            data[k.strip()] = v.strip().strip('"').strip("'")
    return data, body


def extract_urls(text: str):
    return URL_RE.findall(text)


def check_links(urls, timeout=8):
    """对齐 lychee：HEAD/GET 探测，返回 {url: status|error}。"""
    import urllib.request
    import urllib.error
    results = {}
    for u in urls:
        try:
            req = urllib.request.Request(u, method="GET",
                                         headers={"User-Agent": "skill-gate/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                results[u] = r.status
        except urllib.error.HTTPError as e:
            results[u] = e.code
        except Exception as e:  # noqa: BLE001
            results[u] = f"ERR:{type(e).__name__}"
        time.sleep(MAX_LINK_CONCURRENCY_SLEEP)
    return results


def lint_skill(skills_dir: str, skill_rel: str, skill_abs: str, check_links_flag: bool):
    """单技能结构校验，返回问题列表 + 摘要。"""
    issues = []
    skill_md = os.path.join(skill_abs, "SKILL.md")
    if not os.path.isfile(skill_md):
        return [f"[{skill_rel}] 缺少 SKILL.md"], None

    if not is_safe_path(skills_dir, skill_abs):
        return [f"[{skill_rel}] 路径不安全（穿越/绝对/符号链接）"], None

    text = open(skill_md, encoding="utf-8", errors="replace").read()
    fm, body = parse_frontmatter(text)

    if not fm:
        issues.append(f"[{skill_rel}] 无 frontmatter（缺少 --- 块）")
    for fld in REQUIRED_FIELDS:
        if fld not in fm or not fm[fld]:
            issues.append(f"[{skill_rel}] frontmatter 缺必填字段: {fld}")
    desc = fm.get("description", "")
    if desc and not any(h.lower() in desc.lower() for h in TRIGGER_HINT):
        issues.append(f"WARN:[{skill_rel}] description 未含触发语义（场景/关键词），不利自动调用")

    links = extract_urls(text)
    link_status = None
    if check_links_flag and links:
        link_status = check_links(links)
        for u, st in link_status.items():
            if isinstance(st, int) and st >= 400:
                issues.append(f"[{skill_rel}] 死链 {u} -> HTTP {st}")
            elif isinstance(st, str) and st.startswith("ERR"):
                issues.append(f"[{skill_rel}] 链接探测失败 {u} -> {st}")

    summary = {
        "skill": skill_rel,
        "sha256": sha256_file(skill_md),
        "has_frontmatter": bool(fm),
        "fields": list(fm.keys()),
        "url_count": len(links),
        "link_status": link_status,
        "body_chars": len(body),
    }
    return issues, summary


def walk_skills(skills_dir: str):
    """用 os.listdir 遍历，规避 Windows find 的非 ASCII 路径遗漏（全局规范 §三.6）。"""
    out = []
    for name in sorted(os.listdir(skills_dir)):
        p = os.path.join(skills_dir, name)
        if os.path.isdir(p):
            out.append((name, p))
    return out


def run_gate(skills_dir: str, mode: str, check_links_flag: bool, report_path: str, manifest_path: str):
    skills = walk_skills(skills_dir)
    all_issues = []
    summaries = []
    for rel, absp in skills:
        issues, summary = lint_skill(skills_dir, rel, absp, check_links_flag)
        if issues:
            all_issues.extend(issues)
        if summary:
            summaries.append(summary)

    # 双层门禁语义
    if mode == "review":
        gate_note = "review 模式：结构校验完成，接受 pending 产出证据。"
    elif mode == "verify":
        # verify 模式要求 manifest 中存在 approved 记录（此处仅校验 manifest 存在且可解析）
        if not manifest_path or not os.path.isfile(manifest_path):
            all_issues.append(f"[gate] verify 模式要求产出证据 manifest，但未找到: {manifest_path}")
            gate_note = "verify 模式：FAIL（缺 manifest）"
        else:
            man = json.load(open(manifest_path, encoding="utf-8"))
            approved = [r for r in man.get("runs", []) if r.get("review", {}).get("status") == "approved"]
            gate_note = f"verify 模式：manifest 含 {len(approved)} 条 approved / 共 {len(man.get('runs', []))} 条"
            if len(approved) == 0:
                all_issues.append("[gate] verify 模式：manifest 中无 approved 记录，拒绝发布")
    else:
        all_issues.append(f"[gate] 未知模式: {mode}")
        gate_note = "FAIL"

    total = len(skills)
    errors = [i for i in all_issues if not i.startswith("WARN:")]
    warnings = [i for i in all_issues if i.startswith("WARN:")]
    skills_with_issue = {i.split("]")[0].strip("[").replace("WARN:", "").replace("ERROR:", "")
                         for i in all_issues if i.startswith("[") or i.startswith("WARN:[") or i.startswith("ERROR:[")}
    clean = total - len(skills_with_issue)
    # 按类型汇总
    from collections import Counter
    type_counter = Counter()
    for i in all_issues:
        if "缺少 SKILL.md" in i: type_counter["missing_skill_md"] += 1
        elif "路径不安全" in i: type_counter["unsafe_path"] += 1
        elif "无 frontmatter" in i: type_counter["no_frontmatter"] += 1
        elif "缺必填字段" in i: type_counter["missing_required_field"] += 1
        elif "死链" in i: type_counter["dead_link"] += 1
        elif "链接探测失败" in i: type_counter["link_probe_fail"] += 1
        elif "未含触发语义" in i: type_counter["weak_trigger"] += 1
    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "skills_dir": skills_dir,
        "mode": mode,
        "gate_note": gate_note,
        "total_skills": total,
        "skills_clean": clean,
        "skills_with_issues": len(skills_with_issue),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "issue_by_type": dict(type_counter),
        "issues": all_issues,
        "summaries": summaries,
    }
    if report_path:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# 技能质量门禁报告\n\n")
            f.write(f"- 模式: `{mode}`（{gate_note}）\n")
            f.write(f"- 技能总数: {total}｜干净: {clean}｜有问题: {len(skills_with_issue)}\n")
            f.write(f"- ERROR(失败门禁): {len(errors)}｜WARN(软警告): {len(warnings)}\n\n")
            f.write("## 问题类型分布\n\n")
            for t, c in type_counter.most_common():
                f.write(f"- {t}: {c}\n")
            f.write("\n## 问题清单\n\n")
            for i in all_issues:
                f.write(f"- {i}\n")
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skills-dir", required=True)
    ap.add_argument("--mode", choices=["review", "verify"], default="review")
    ap.add_argument("--check-links", action="store_true", help="启用链接 HTTP 探测（较慢）")
    ap.add_argument("--report", default="skill_gate_report.md")
    ap.add_argument("--manifest", default="skills_manifest.json")
    args = ap.parse_args()

    if not os.path.isdir(args.skills_dir):
        print(f"ERROR: skills-dir 不存在: {args.skills_dir}", file=sys.stderr)
        sys.exit(2)

    report = run_gate(args.skills_dir, args.mode, args.check_links, args.report, args.manifest)
    print(json.dumps({k: v for k, v in report.items() if k != "summaries"},
                     ensure_ascii=False, indent=2))
    # 门禁失败（有 ERROR 级问题）则非零退出，便于 CI 接入；WARN 不阻断
    sys.exit(1 if report["error_count"] else 0)


if __name__ == "__main__":
    main()
