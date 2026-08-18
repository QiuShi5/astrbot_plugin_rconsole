"""Shared helpers for the AstrBot R-console port."""

from __future__ import annotations

import asyncio
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 5.0; AstrBot RConsole Port) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36"
)


@dataclass
class ROutput:
    """Platform-neutral service output."""

    text: str = ""
    images: list[str] = field(default_factory=list)
    audios: list[str] = field(default_factory=list)
    videos: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    forward_texts: list[str] = field(default_factory=list)
    stop: bool = True

    def has_media(self) -> bool:
        return bool(self.images or self.audios or self.videos or self.files)


def strip_html(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"<[^>]+>", "", value).strip()


def first_url(text: str) -> str:
    match = re.search(r"https?://[^\s\]）)>\"']+", text)
    return match.group(0) if match else ""


def truncate(value: str, limit: int = 500) -> str:
    value = value or ""
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"


def _request_json_sync(url: str, *, headers: dict[str, str] | None = None, timeout: int = 15) -> Any:
    req_headers = {"User-Agent": USER_AGENT, "Accept": "application/json,text/plain,*/*"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    return json.loads(raw.decode("utf-8", errors="replace"))


async def request_json(url: str, *, headers: dict[str, str] | None = None, timeout: int = 15) -> Any:
    return await asyncio.to_thread(_request_json_sync, url, headers=headers, timeout=timeout)


def _request_text_sync(url: str, *, headers: dict[str, str] | None = None, timeout: int = 15) -> str:
    req_headers = {"User-Agent": USER_AGENT, "Accept": "text/html,text/plain,*/*"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    return raw.decode("utf-8", errors="replace")


async def request_text(url: str, *, headers: dict[str, str] | None = None, timeout: int = 15) -> str:
    return await asyncio.to_thread(_request_text_sync, url, headers=headers, timeout=timeout)


def safe_filename(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._\-\u4e00-\u9fa5]+", "_", name).strip("._") or "file"


def read_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default
    return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_config_value(config: Any, key: str, default: Any = None) -> Any:
    """Read AstrBotConfig/dict-like values without depending on its concrete type."""
    if config is None:
        return default
    cur: Any = config
    for part in key.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part, default)
        else:
            getter = getattr(cur, "get", None)
            if callable(getter):
                try:
                    cur = getter(part, default)
                except TypeError:
                    cur = getter(part)
            else:
                cur = getattr(cur, part, default)
        if cur is default:
            return default
    return cur
