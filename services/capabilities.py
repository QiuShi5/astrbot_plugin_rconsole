"""Capability diagnostics for account/adapter-coupled R-plugin features."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from typing import Any

from .common import ROutput, get_config_value

try:  # real AstrBot runtime
    import astrbot.api.message_components as Comp
except Exception:  # pragma: no cover
    Comp = None


@dataclass
class CapabilityItem:
    name: str
    ok: bool
    detail: str


class CapabilityService:
    """Report whether runtime prerequisites exist for platform-coupled features.

    This does not fake扫码/群文件/云盘成功. It gives operators a concrete checklist
    and detects the parts that can be inspected inside AstrBot.
    """

    def __init__(self, config: Any):
        self.config = config

    def probe(self, event: Any | None = None) -> ROutput:
        items = self._items(event)
        lines = ["R插件 AstrBot版能力诊断"]
        for item in items:
            lines.append(f"{'✅' if item.ok else '⚠️'} {item.name}: {item.detail}")
        lines.append("")
        lines.append(
            "说明：扫码登录、网易云云盘上传、群文件/群语音属于账号或适配器强耦合能力；只有当对应 Cookie/API/适配器能力全部满足后才可真实执行。"
        )
        return ROutput(text="\n".join(lines))

    def _items(self, event: Any | None) -> list[CapabilityItem]:
        items = []
        items.append(
            CapabilityItem(
                "AstrBot 富媒体组件",
                Comp is not None,
                "Plain/Image/Record/Video/File 组件可用" if Comp else "当前环境未提供 astrbot.api.message_components",
            )
        )
        if Comp is not None:
            for name in ["Image", "Record", "Video", "File"]:
                ok = hasattr(Comp, name)
                items.append(CapabilityItem(f"组件 {name}", ok, "可构造" if ok else "缺失"))
        adapter = (
            getattr(getattr(event, "message_obj", None), "platform_name", "")
            or getattr(event, "platform_name", "")
            or "未知"
        )
        items.append(CapabilityItem("当前适配器", adapter != "未知", str(adapter)))
        bili_sessdata = get_config_value(self.config, "bilibili.sessdata", "")
        items.append(
            CapabilityItem(
                "B站 SESSDATA", bool(bili_sessdata), "已配置" if bili_sessdata else "未配置，扫码/高权限内容不可验证"
            )
        )
        items.append(
            CapabilityItem(
                "网易云 Cookie",
                bool(get_config_value(self.config, "netease.cookie", "")),
                "已配置" if get_config_value(self.config, "netease.cookie", "") else "未配置，会员/受限歌曲可能不可用",
            )
        )
        items.append(
            CapabilityItem(
                "网易云云盘 Cookie",
                bool(get_config_value(self.config, "netease.cloud_cookie", "")),
                "已配置"
                if get_config_value(self.config, "netease.cloud_cookie", "")
                else "未配置，云盘列表/上传不可执行",
            )
        )
        items.append(
            CapabilityItem(
                "网易云云盘 API",
                bool(get_config_value(self.config, "netease.cloud_api_server", "")),
                get_config_value(self.config, "netease.cloud_api_server", "") or "未配置自建云盘 API",
            )
        )
        items.append(
            CapabilityItem(
                "ffmpeg", shutil.which("ffmpeg") is not None, shutil.which("ffmpeg") or "未安装；语音转码不可执行"
            )
        )
        items.append(
            CapabilityItem(
                "BBDown", shutil.which("BBDown") is not None, shutil.which("BBDown") or "未安装；B站专用下载链不可执行"
            )
        )
        items.append(
            CapabilityItem(
                "tdl", shutil.which("tdl") is not None, shutil.which("tdl") or "未安装；Telegram 下载链不可执行"
            )
        )
        items.append(
            CapabilityItem(
                "aria2c", shutil.which("aria2c") is not None, shutil.which("aria2c") or "未安装；aria2 下载链不可执行"
            )
        )
        return items
