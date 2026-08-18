"""Help and version data services."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None

from .card_renderer import CardRenderer
from .common import ROutput, strip_html


class HelpVersionService:
    def __init__(self, resources_dir: Path, output_dir: Path | None = None):
        self.resources_dir = resources_dir
        self.renderer = CardRenderer(resources_dir, output_dir=output_dir)

    def help_data(self) -> list[dict[str, Any]]:
        path = self.resources_dir / "config" / "help.yaml"
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        if yaml is not None:
            try:
                data = yaml.safe_load(text) or []
                if isinstance(data, list):
                    return data
            except Exception:
                pass
        groups: list[dict[str, Any]] = []
        current_group: dict[str, Any] | None = None
        current_item: dict[str, str] | None = None
        for line in text.splitlines():
            group = re.match(r"\s*-\s+group:\s*(.+)", line)
            icon = re.match(r"\s*-\s+icon:\s*(.+)", line)
            title = re.match(r"\s*title:\s*[\"']?(.+?)[\"']?\s*$", line)
            desc = re.match(r"\s*desc:\s*[\"']?(.+?)[\"']?\s*$", line)
            if group:
                current_group = {"group": group.group(1).strip(), "list": []}
                groups.append(current_group)
            elif icon and current_group is not None:
                current_item = {"icon": icon.group(1).strip(), "title": "", "desc": ""}
                current_group["list"].append(current_item)
            elif title and current_item is not None:
                current_item["title"] = title.group(1).strip()
            elif desc and current_item is not None:
                current_item["desc"] = desc.group(1).strip()
        return groups

    def version_data(self) -> tuple[str, list[str]]:
        path = self.resources_dir / "config" / "version.yaml"
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        version_match = re.search(r"version:\s*([^,\n}]+)", text)
        version = version_match.group(1).strip() if version_match else "0.1.0"
        raw_items = re.findall(
            r"<span class=\"cmd\">(.*?)</span>|新增<span class=\"cmd\">(.*?)</span>|"
            r"优化<span class=\"cmd\">(.*?)</span>|支持<span class=\"cmd\">(.*?)</span>|"
            r"重构<span class=\"cmd\">(.*?)</span>|增强<span class=\"cmd\">(.*?)</span>",
            text,
        )
        flat: list[str] = []
        for item in raw_items:
            if isinstance(item, tuple):
                flat.extend([strip_html(x).strip() for x in item if x])
            elif item:
                flat.append(strip_html(item).strip())
        return version, flat or ["已移植到 AstrBot 版"]

    def help_text(self) -> ROutput:
        groups = self.help_data()
        lines: list[str] = []
        for group in groups:
            lines.append(f"\n【{group.get('group', '功能')}】")
            for item in group.get("list", []):
                lines.append(f"- {item.get('title', '')}：{item.get('desc', '')}")
        body = "\n".join(lines).strip() or "帮助数据读取失败"
        out = ROutput(text=f"R-Plugin\n{body}\n\nCreated By Yunzai-Bot & R-Plugin")
        try:
            version, _ = self.version_data()
            out.images.append(self.renderer.render_help(groups, version=version))
        except Exception:
            pass
        return out

    def version_text(self) -> ROutput:
        version, items = self.version_data()
        highlights = "\n".join(f"- {x}" for x in items[:18]) or "- 已移植到 AstrBot 版"
        out = ROutput(text=f"R插件版本：v{version}\n{highlights}")
        try:
            out.images.append(self.renderer.render_version(version, items[:18]))
        except Exception:
            pass
        return out
