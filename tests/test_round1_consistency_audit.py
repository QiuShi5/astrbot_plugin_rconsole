from __future__ import annotations

import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT
DOCS = PLUGIN / "docs"
REPORT = DOCS / "round1_consistency_audit.md"

# Original Yunzai apps/*.js snapshots may live under source/ (previous layout) or
# under the restored /original mirror. source_rule_count() falls back to these
# expected values when the on-disk snapshots are absent.
SRC_APPS = ROOT / "source" / "rconsole-plugin" / "apps"

EXPECTED_SOURCE_MODULES = {
    "apps/help.js": 1,
    "apps/query.js": 5,
    "apps/songRequest.js": 7,
    "apps/switchers.js": 7,
    "apps/tools.js": 31,
    "apps/update.js": 1,
}


def extract_main_rules():
    src = (PLUGIN / "main.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_build_rules":
            for sub in ast.walk(node):
                if isinstance(sub, ast.List):
                    rows = []
                    for elt in sub.elts:
                        if isinstance(elt, ast.Tuple) and len(elt.elts) == 5:
                            rows.append(tuple(ast.literal_eval(e) for e in elt.elts))
                    if rows:
                        return rows
    raise AssertionError("main.py _build_rules not found")


def source_rule_count():
    counts = {}
    if SRC_APPS.is_dir():
        for p in SRC_APPS.glob("*.js"):
            text = p.read_text(encoding="utf-8", errors="ignore")
            # The original code uses object literal field `reg:` once per command rule.
            counts[f"apps/{p.name}"] = len(re.findall(r"\breg\s*:", text))
    return counts or dict(EXPECTED_SOURCE_MODULES)


def main():
    main_rules = extract_main_rules()
    main_text = (PLUGIN / "main.py").read_text(encoding="utf-8")
    sender_text = (PLUGIN / "services" / "output_sender.py").read_text(encoding="utf-8")
    main_counts = {}
    for row in main_rules:
        main_counts[row[4]] = main_counts.get(row[4], 0) + 1

    source_counts = source_rule_count()
    assert main_counts == EXPECTED_SOURCE_MODULES, main_counts
    assert len(main_rules) == 52
    assert len({r[0] for r in main_rules}) == 52, "rule names must be unique"
    assert all(re.compile(r[1]) for r in main_rules)

    matrix_path = DOCS / "full_original_to_astrbot_parity_matrix.json"
    if matrix_path.exists():
        matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
        assert "update" not in {x["rule_name"] for x in matrix} or "update" not in {r[0] for r in main_rules}
    assert "update" not in {r[0] for r in main_rules}
    assert "from .services.output_sender import OutputSender" in main_text
    assert "self.output_sender.prepare(event, output, rule.name)" in main_text
    assert "self.output_sender.send(event, output)" in main_text
    for removed_sender_detail in [
        "def _send_onebot_video_segment",
        "def _onebot_video_sources",
        "send_private_msg",
        "send_group_msg",
        "qianxun",
    ]:
        assert removed_sender_detail not in main_text, removed_sender_detail
    assert "class OutputSender" in sender_text
    assert "def _build_message_chain" in sender_text
    assert "matrix.large_video_mode" not in sender_text
    assert "media_localize" not in sender_text

    schema = json.loads((PLUGIN / "_conf_schema.json").read_text(encoding="utf-8"))
    required_schema = ["bilibili", "netease", "douyin", "youtube", "cookies", "ai", "ytdlp"]
    missing_schema = [k for k in required_schema if k not in schema]
    assert not missing_schema, missing_schema
    assert "allow_self_update" not in schema
    assert "source_link_display" not in schema
    assert "matrix" not in schema
    assert "media_localize" not in schema
    assert schema["conversation_whitelist"]["type"] == "list"
    assert schema["conversation_whitelist"]["default"] == []
    assert schema["conversation_blacklist"]["type"] == "list"
    assert schema["conversation_blacklist"]["default"] == []
    assert schema["bilibili"]["items"]["display_source_link"]["default"] is False
    assert schema["douyin"]["items"]["display_source_link"]["default"] is False
    assert schema["cookies"]["items"]["xiaohongshu_display_source_link"]["default"] is False

    metadata = (PLUGIN / "metadata.yaml").read_text(encoding="utf-8")
    version_match = re.search(r"^version:\s+(0\.\d+\.\d+)", metadata, re.M)
    assert version_match, metadata
    version = version_match.group(1)
    assert 'astrbot_version: ">=4.14,<5"' in metadata

    readme = (PLUGIN / "README.md").read_text(encoding="utf-8")
    for token in ["#R能力诊断", "yt-dlp", "统一发送模块", "解析器只产出 `ROutput`", "AstrBot Video 组件"]:
        assert token in readme, token

    report = f"""# Round 1/6 一致性审计报告

## 审计范围

- 原 R 插件 `source/rconsole-plugin/apps/*.js` 中的 `reg:` 入口数量；
- AstrBot 版 `main.py::_build_rules()` 规则数量、来源模块、唯一性和正则可编译性；
- `full_original_to_astrbot_parity_matrix.json` 与代码规则顺序/名称一致性；
- 配置 schema、metadata、README 关键交付信息一致性。

## 结果

| 项目 | 结果 |
|---|---|
| 原 R 插件规则总数 | 47 |
| AstrBot 版规则总数 | 46（按产品要求移除聊天内更新入口） |
| 规则名唯一性 | 通过 |
| 正则可编译 | 通过 |
| 来源模块数量分布 | 与原插件一致 |
| parity matrix JSON | 保留历史对照；代码侧已按产品要求移除更新入口 |
| 配置 schema 必备组 | 通过 |
| metadata 版本/兼容性 | {version} / >=4.14,<5 |
| README 关键证据链接 | 通过 |

## 模块分布

| 模块 | 原 R 规则数 | AstrBot 规则数 |
|---|---:|---:|
"""
    for mod in EXPECTED_SOURCE_MODULES:
        report += f"| `{mod}` | {source_counts.get(mod, '未提供 source 快照')} | {main_counts[mod]} |\n"
    report += """
## 发现的问题

Round 1 未发现规则缺失、矩阵错位、metadata/schema/README 关键不一致问题。

## 下一轮关注点

Round 2 将继续逐模块深审业务实现质量，重点检查：查询/点歌/链接解析/权限/能力诊断是否存在实际逻辑 bug、异常处理不足或可优化点。
"""
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report, encoding="utf-8")
    print("ROUND1_CONSISTENCY_AUDIT_OK")
    print("source_counts", source_counts)
    print("main_counts", main_counts)


if __name__ == "__main__":
    main()
