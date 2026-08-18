"""Unified AstrBot output preparation and sending.

Resolvers produce platform-neutral ``ROutput`` objects.  This module owns the
single path that turns those objects into AstrBot message components.
"""

from __future__ import annotations

import asyncio
import hashlib
import mimetypes
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent

try:
    import astrbot.api.message_components as Comp
except Exception:  # pragma: no cover - AstrBot runtime provides this.
    Comp = None

from .common import ROutput, get_config_value


class OutputSender:
    """Prepare and send every resolver output through AstrBot's component API."""

    def __init__(self, *, config: Any, data_dir: Path):
        self.config = config
        self.data_dir = Path(data_dir)

    async def prepare(self, event: AstrMessageEvent, output: ROutput, rule_name: str = "") -> ROutput:
        if not self._source_link_enabled(rule_name) and output.text:
            output.text = self._strip_source_link_lines(output.text)
        await self._localize_remote_videos(output, rule_name or "media")
        return output

    async def send(self, event: AstrMessageEvent, output: ROutput) -> None:
        texts: list[str] = []
        if output.text:
            texts.append(output.text)
        if output.forward_texts:
            texts.append("\n\n".join(output.forward_texts))
        combined_text = "\n\n".join(t for t in texts if t)

        if Comp is not None and output.has_media():
            if self._prefer_segmented_media(event):
                await self._send_output_segmented_compat(event, output, combined_text)
                return
            try:
                chain = self._build_message_chain(output, combined_text)
                await event.send(event.chain_result(chain))
                return
            except Exception as exc:
                logger.warning(f"R插件统一发送模块：富媒体消息链发送失败，尝试逐段降级发送：{exc}")
                await self._send_output_segmented(event, output, combined_text)
                return

        await self._send_output_segmented(event, output, combined_text)

    def _source_link_enabled(self, rule_name: str) -> bool:
        path = self._source_link_config_path(rule_name)
        if path:
            value = get_config_value(self.config, path, None)
            if value is not None:
                return bool(value)
        legacy = get_config_value(self.config, f"source_link_display.{rule_name}", None)
        if legacy is not None:
            return bool(legacy)
        return False

    def _source_link_config_path(self, rule_name: str) -> str:
        return {
            "bili": "bilibili.display_source_link",
            "douyin": "douyin.display_source_link",
            "youtube": "youtube.display_source_link",
            "xhs": "cookies.xiaohongshu_display_source_link",
            "weibo": "cookies.weibo_display_source_link",
            "xiaoheihe": "cookies.xiaoheihe_display_source_link",
        }.get(rule_name, "")

    def _strip_source_link_lines(self, text: str) -> str:
        raw_lines = (text or "").splitlines()
        lines = []
        for index, line in enumerate(raw_lines):
            if re.match(r"^\s*(?:原)?链接\s*[:：]\s*https?://", line):
                context = "\n".join(raw_lines[max(0, index - 1) : min(len(raw_lines), index + 2)])
                if self._source_link_context_is_failure(context):
                    lines.append(line)
                continue
            lines.append(line)
        return "\n".join(lines).strip()

    def _source_link_context_is_failure(self, context: str) -> bool:
        marker = str(context or "").lower()
        return any(
            token in marker for token in ("解析失败", "读取失败", "展开失败", "缺少必要信息", "未找到", "无法", "失败")
        )

    async def _localize_remote_videos(self, output: ROutput, rule_name: str) -> None:
        if not output.videos:
            return
        localized_videos: list[str] = []
        for source in output.videos:
            if not self._is_remote_url(source):
                localized_videos.append(source)
                continue
            local = await self._download_remote_video_for_file(source, rule_name=rule_name)
            if local:
                logger.info(
                    "R插件统一发送模块：远程视频已本地化 rule=%s source_host=%s file=%s size=%d",
                    rule_name,
                    urllib.parse.urlparse(source).netloc,
                    Path(local).name,
                    Path(local).stat().st_size if Path(local).exists() else 0,
                )
                localized_videos.append(local)
            else:
                logger.warning("R插件统一发送模块：远程视频本地化失败 rule=%s，降级为直链文本", rule_name)
                output.text = self._append_text(output.text, f"[视频直链] {source}")
        output.videos = localized_videos

    async def _download_remote_video_for_file(self, url: str, *, rule_name: str = "media") -> str:
        return await asyncio.to_thread(self._download_remote_video_for_file_sync, url, rule_name=rule_name)

    def _download_remote_video_for_file_sync(self, url: str, *, rule_name: str = "media") -> str:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 AstrBot RConsole"}, method="GET")
        out_dir = self.data_dir / "temp" / "localized-video" / rule_name
        out_dir.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(req, timeout=60) as resp:
            content_type = (resp.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
            ext = self._safe_video_extension(url, content_type)
            path = out_dir / f"video_{self._stable_url_token(url)}{ext}"
            with path.open("wb") as fh:
                while True:
                    chunk = resp.read(1024 * 1024)
                    if not chunk:
                        break
                    fh.write(chunk)
        return str(path)

    def _safe_video_extension(self, url: str, content_type: str = "") -> str:
        allowed = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".flv"}
        guessed = mimetypes.guess_extension(content_type or "") or ""
        if guessed in {".mp4", ".m4v", ".mov", ".webm"}:
            return guessed
        suffix = Path(urllib.parse.urlparse(url).path).suffix.lower()
        if suffix in allowed:
            return suffix
        return ".mp4"

    def _stable_url_token(self, url: str) -> str:
        return hashlib.sha1(url.encode("utf-8", errors="ignore")).hexdigest()[:16]

    def _append_text(self, text: str, addition: str) -> str:
        return (text + "\n" + addition).strip() if text else addition

    def _platform_name(self, event: AstrMessageEvent) -> str:
        getter = getattr(event, "get_platform_name", None)
        if callable(getter):
            try:
                value = getter()
                if value:
                    return str(value)
            except Exception:
                pass
        message_obj = getattr(event, "message_obj", None)
        platform_name = getattr(message_obj, "platform_name", "") if message_obj is not None else ""
        if platform_name:
            return str(platform_name)
        origin = str(getattr(event, "unified_msg_origin", "") or "")
        return origin.split(":", 1)[0] if origin else ""

    def _prefer_segmented_media(self, event: AstrMessageEvent) -> bool:
        platform = self._platform_name(event).lower()
        origin = str(getattr(event, "unified_msg_origin", "") or "").lower()
        marker = f"{platform}:{origin}"
        conservative_tokens = ("aiocqhttp", "onebot", "onebot11", "cqhttp", "napcat", "lagrange", "llonebot")
        return any(token in marker for token in conservative_tokens)

    def _build_message_chain(self, output: ROutput, combined_text: str):
        chain = []
        if combined_text:
            chain.append(Comp.Plain(combined_text))
        for url in output.images:
            chain.append(Comp.Image.fromURL(url) if self._is_remote_url(url) else Comp.Image.fromFileSystem(url))
        for url in output.audios:
            if self._is_remote_url(url) and hasattr(Comp.Record, "fromURL"):
                chain.append(Comp.Record.fromURL(url))
            elif hasattr(Comp.Record, "fromFileSystem") and not self._is_remote_url(url):
                chain.append(Comp.Record.fromFileSystem(url))
            else:
                chain.append(Comp.Record(file=url, url=url))
        for url in output.videos:
            chain.append(Comp.Video.fromURL(url) if self._is_remote_url(url) else Comp.Video.fromFileSystem(path=url))
        for file_path in output.files:
            chain.append(Comp.File(file=file_path, name=Path(file_path).name))
        return chain

    async def _send_output_segmented_compat(self, event: AstrMessageEvent, output: ROutput, combined_text: str) -> None:
        text_image_output = ROutput(text=combined_text, images=list(output.images), stop=output.stop)
        if combined_text or output.images:
            try:
                chain = self._build_message_chain(text_image_output, combined_text)
                await event.send(event.chain_result(chain))
            except Exception as exc:
                logger.warning(f"R插件统一发送模块：图文合并发送失败，尝试逐段降级：{exc}")
                if combined_text:
                    await event.send(event.plain_result(combined_text))
                for url in output.images:
                    await self._send_image_segment(event, url)
        for url in output.audios:
            await self._send_component_segment(event, "音频", url, self._record_component)
        for url in output.videos:
            await self._send_video_segment(event, url)
        for file_path in output.files:
            await self._send_component_segment(event, "文件", file_path, self._file_component)
        if not combined_text and not output.has_media():
            await event.send(event.plain_result("操作完成"))

    async def _send_output_segmented(self, event: AstrMessageEvent, output: ROutput, combined_text: str) -> None:
        if combined_text:
            await event.send(event.plain_result(combined_text))
        for url in output.images:
            await self._send_image_segment(event, url)
        for url in output.audios:
            await self._send_component_segment(event, "音频", url, self._record_component)
        for url in output.videos:
            await self._send_video_segment(event, url)
        for file_path in output.files:
            await self._send_component_segment(event, "文件", file_path, self._file_component)
        if not combined_text and not output.has_media():
            await event.send(event.plain_result("操作完成"))

    async def _send_image_segment(self, event: AstrMessageEvent, url: str) -> None:
        image_result = getattr(event, "image_result", None)
        if callable(image_result):
            try:
                await event.send(image_result(url))
                return
            except Exception as exc:
                logger.warning(f"R插件统一发送模块：图片原生发送失败，尝试组件发送：{exc}")
        await self._send_component_segment(event, "图片", url, self._image_component)

    async def _send_video_segment(self, event: AstrMessageEvent, source: str) -> None:
        if not self._is_remote_url(source):
            path = Path(source.removeprefix("file://")).expanduser().resolve()
            if not path.exists() or not path.is_file():
                await event.send(event.plain_result(f"视频文件不存在，无法发送：{path}"))
                return
        try:
            await self._send_component_segment(event, "视频", source, self._video_component, text_fallback=False)
            return
        except Exception as exc:
            logger.warning(f"R插件统一发送模块：视频组件发送失败，降级为文本：{exc}")
        await event.send(event.plain_result(f"[视频] {source}"))

    async def _send_component_segment(
        self, event: AstrMessageEvent, label: str, source: str, factory, *, text_fallback: bool = True
    ) -> None:
        if Comp is not None:
            try:
                component = factory(source)
                await event.send(event.chain_result([component]))
                return
            except Exception as exc:
                logger.warning(f"R插件统一发送模块：{label}组件发送失败，降级为文本：{exc}")
                if not text_fallback:
                    raise
        if text_fallback:
            await event.send(event.plain_result(f"[{label}] {source}"))

    def _image_component(self, source: str):
        return Comp.Image.fromURL(source) if self._is_remote_url(source) else Comp.Image.fromFileSystem(source)

    def _record_component(self, source: str):
        if self._is_remote_url(source) and hasattr(Comp.Record, "fromURL"):
            return Comp.Record.fromURL(source)
        if not self._is_remote_url(source) and hasattr(Comp.Record, "fromFileSystem"):
            return Comp.Record.fromFileSystem(source)
        return Comp.Record(file=source, url=source if self._is_remote_url(source) else "")

    def _video_component(self, source: str):
        return Comp.Video.fromURL(source) if self._is_remote_url(source) else Comp.Video.fromFileSystem(path=source)

    def _file_component(self, source: str):
        return Comp.File(file=source, name=Path(source).name)

    def _is_remote_url(self, value: str) -> bool:
        return value.startswith("http://") or value.startswith("https://")
