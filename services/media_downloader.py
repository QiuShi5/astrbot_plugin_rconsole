"""Optional yt-dlp backed media resolver/downloader.

This is the closest platform-neutral replacement for the original R-plugin's
BBDown/yt-dlp/ffmpeg/download pipeline. It works inside AstrBot without shelling
out when the Python package `yt-dlp` is installed, and can fall back to the
`yt-dlp` executable if present.
"""

from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .common import ROutput, safe_filename, truncate


class YtDlpService:
    def __init__(self, temp_dir: Path, *, mode: str = "direct", max_filesize_mb: int = 70, proxy: str = ""):
        self.temp_dir = temp_dir
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.mode = mode if mode in {"off", "metadata", "direct", "download"} else "direct"
        self.max_filesize_mb = int(max_filesize_mb or 70)
        self.proxy = proxy or ""

    def available(self) -> tuple[bool, str]:
        try:
            import yt_dlp  # noqa: F401

            return True, "python-package"
        except Exception:
            pass
        exe = shutil.which("yt-dlp")
        if exe:
            return True, exe
        return False, ""

    async def extract(self, url: str, *, platform: str = "") -> ROutput:
        if self.mode == "off":
            return ROutput(text=f"✅ 识别：{platform or '通用媒体'}\n链接：{url}\nyt-dlp 解析链已在配置中关闭。")
        ok, backend = self.available()
        if not ok:
            return ROutput(
                text=(
                    f"✅ 识别：{platform or '通用媒体'}\n链接：{url}\n"
                    "未检测到 yt-dlp。已保留完整媒体解析/下载链入口；安装依赖 `pip install yt-dlp` 后可自动提取标题、封面、直链并按配置下载。"
                )
            )
        try:
            if backend == "python-package":
                info = await asyncio.to_thread(self._extract_python, url)
            else:
                info = await asyncio.to_thread(self._extract_cli, url, backend)
        except Exception as exc:
            return ROutput(text=f"✅ 识别：{platform or '通用媒体'}\n链接：{url}\nyt-dlp 解析失败：{exc}")

        return await self._output_from_info(info, platform=platform, original_url=url)

    def _ydl_opts(self, *, download: bool = False, outtmpl: str | None = None) -> dict[str, Any]:
        opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": not download,
            "noplaylist": True,
            "format": "bv*+ba/best/bestvideo+bestaudio",
            "socket_timeout": 25,
            "retries": 2,
            "ignoreerrors": False,
        }
        if self.proxy:
            opts["proxy"] = self.proxy
        if download and outtmpl:
            opts.update(
                {
                    "skip_download": False,
                    "outtmpl": outtmpl,
                    "merge_output_format": "mp4",
                    "overwrites": True,
                }
            )
        return opts

    def _extract_python(self, url: str) -> dict[str, Any]:
        import yt_dlp

        with yt_dlp.YoutubeDL(self._ydl_opts(download=False)) as ydl:
            return ydl.extract_info(url, download=False)

    def _extract_cli(self, url: str, exe: str) -> dict[str, Any]:
        cmd = [exe, "--dump-single-json", "--no-playlist", "--no-warnings", url]
        if self.proxy:
            cmd.extend(["--proxy", self.proxy])
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=True)
        return json.loads(proc.stdout)

    async def _download_python(self, url: str, stem: str) -> list[str]:
        import yt_dlp

        outtmpl = str(self.temp_dir / f"{safe_filename(stem)}.%(ext)s")
        before = set(self.temp_dir.glob(f"{safe_filename(stem)}*"))
        with yt_dlp.YoutubeDL(self._ydl_opts(download=True, outtmpl=outtmpl)) as ydl:
            ydl.extract_info(url, download=True)
        after = set(self.temp_dir.glob(f"{safe_filename(stem)}*"))
        return [str(p) for p in sorted(after - before) if p.is_file()]

    async def _output_from_info(self, info: dict[str, Any], *, platform: str, original_url: str) -> ROutput:
        if info.get("_type") == "playlist" and info.get("entries"):
            info = next((x for x in info.get("entries") or [] if x), info)
        title = info.get("title") or "未知标题"
        uploader = info.get("uploader") or info.get("channel") or info.get("creator") or "未知作者"
        duration = self._fmt_duration(info.get("duration"))
        webpage_url = info.get("webpage_url") or original_url
        desc = truncate(info.get("description") or "", 220)
        thumbnail = info.get("thumbnail") or ""
        filesize = self._filesize_mb(info)
        media_url = self._best_media_url(info)

        lines = [
            f"✅ 识别：{platform or info.get('extractor_key') or '通用媒体'}",
            f"标题：{title}",
            f"作者：{uploader}",
            f"时长：{duration}",
            f"链接：{webpage_url}",
        ]
        if filesize:
            lines.append(f"估计大小：{filesize:.1f} MB")
        if desc:
            lines.append(f"简介：{desc}")

        images = [thumbnail] if thumbnail else []
        videos: list[str] = []
        files: list[str] = []

        if self.mode in {"direct", "download"} and media_url:
            if filesize and filesize > self.max_filesize_mb:
                lines.append(f"媒体大小超过配置上限 {self.max_filesize_mb} MB，已返回信息与封面，未发送直链。")
            else:
                videos.append(media_url)
                lines.append("已提取可播放直链。")

        if self.mode == "download":
            if filesize and filesize > self.max_filesize_mb:
                lines.append("跳过下载：超过大小限制。")
            else:
                ok, backend = self.available()
                if backend == "python-package":
                    try:
                        downloaded = await self._download_python(webpage_url, title)
                        files.extend(downloaded)
                        if downloaded:
                            lines.append(f"已下载媒体文件：{Path(downloaded[0]).name}")
                    except Exception as exc:
                        lines.append(f"下载失败：{exc}")
                else:
                    lines.append(
                        "当前仅检测到 yt-dlp CLI，AstrBot 版默认不在后台 shell 下载；请安装 Python 包 `yt-dlp` 启用内置下载。"
                    )

        return ROutput(text="\n".join(lines), images=images, videos=videos, files=files)

    def _fmt_duration(self, value: Any) -> str:
        try:
            seconds = int(float(value or 0))
        except Exception:
            return "未知"
        if seconds <= 0:
            return "未知"
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    def _filesize_mb(self, info: dict[str, Any]) -> float:
        size = info.get("filesize") or info.get("filesize_approx")
        if not size:
            formats = info.get("formats") or []
            candidates = [
                f.get("filesize") or f.get("filesize_approx")
                for f in formats
                if f.get("filesize") or f.get("filesize_approx")
            ]
            size = max(candidates) if candidates else 0
        try:
            return float(size or 0) / 1024 / 1024
        except Exception:
            return 0.0

    def _best_media_url(self, info: dict[str, Any]) -> str:
        if info.get("url") and str(info.get("url", "")).startswith("http"):
            return str(info["url"])
        formats = info.get("formats") or []
        ranked = []
        for fmt in formats:
            url = fmt.get("url")
            if not url or not str(url).startswith("http"):
                continue
            vcodec = fmt.get("vcodec")
            acodec = fmt.get("acodec")
            height = fmt.get("height") or 0
            ext = fmt.get("ext") or ""
            score = int(height or 0)
            if vcodec and vcodec != "none":
                score += 10000
            if acodec and acodec != "none":
                score += 1000
            if ext in {"mp4", "m4a"}:
                score += 100
            ranked.append((score, str(url)))
        if not ranked:
            return ""
        ranked.sort(reverse=True)
        return ranked[0][1]
