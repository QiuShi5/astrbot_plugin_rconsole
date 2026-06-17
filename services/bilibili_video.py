"""Native Bilibili playurl extraction and local video download."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from .common import ROutput, read_json, safe_filename, truncate

PLAYURL_API = "https://api.bilibili.com/x/player/playurl"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125 Safari/537.36"


class BilibiliVideoService:
    def __init__(self, temp_dir: Path, *, max_filesize_mb: int = 70, sessdata: str = "",
                 download_timeout: int = 60):
        self.temp_dir = temp_dir
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.max_filesize_mb = int(max_filesize_mb or 70)
        self.sessdata = sessdata or ""
        self.download_timeout = max(10, int(download_timeout or 60))
        self.auth_path = self.temp_dir.parent / "bilibili_auth.json"

    async def extract_video(self, *, bvid: str, cid: str | int, title: str = "") -> ROutput:
        if not bvid or not cid:
            return ROutput(text="未找到 B站视频 cid，无法获取播放地址。")
        page_url = f"https://www.bilibili.com/video/{bvid}"
        try:
            data, selected_qn = self._request_best_playurl(bvid=bvid, cid=str(cid), page_url=page_url)
        except Exception as exc:
            return ROutput(text=f"B站 playurl 获取失败：{exc}")
        payload = data.get("data") or data.get("result") or {}
        durl = payload.get("durl") or []
        if not durl:
            return ROutput(text="B站 playurl 未返回可直接发送的 mp4/flv 地址；可能需要 SESSDATA 或更低清晰度。")
        item = durl[0]
        media_url = item.get("url") or ""
        size = int(item.get("size") or 0)
        size_mb = size / 1024 / 1024 if size else 0
        if not media_url:
            return ROutput(text="B站 playurl 返回为空。")
        if size_mb and size_mb > self.max_filesize_mb:
            return ROutput(text=f"B站视频大小约 {size_mb:.1f} MB，超过配置上限 {self.max_filesize_mb} MB，未下载发送视频。")
        try:
            local = self._download_video(media_url, page_url=page_url, stem=f"{bvid}_{title or 'video'}", limit_mb=self.max_filesize_mb)
        except Exception as exc:
            return ROutput(text=f"B站视频直链已获取，但下载成本地文件失败（超时=下载失败，可在配置中调高 video_download_timeout）：{exc}\n直链可能需要 Referer/Cookie，已避免直接远程发送导致适配器失败。")
        return ROutput(text=f"已获取并下载 B站视频：{Path(local).name}（清晰度 qn={selected_qn}）", videos=[local])

    def _request_best_playurl(self, *, bvid: str, cid: str, page_url: str) -> tuple[dict[str, Any], str]:
        best_data: dict[str, Any] | None = None
        best_qn = "64"
        for qn in ["64", "32", "16"]:
            data = self._request_playurl(bvid=bvid, cid=cid, page_url=page_url, qn=qn)
            payload = data.get("data") or data.get("result") or {}
            durl = payload.get("durl") or []
            if not durl:
                continue
            size = int((durl[0] or {}).get("size") or 0)
            best_data, best_qn = data, qn
            if not size or size / 1024 / 1024 <= self.max_filesize_mb:
                return data, qn
        if best_data is None:
            return self._request_playurl(bvid=bvid, cid=cid, page_url=page_url, qn="16"), "16"
        return best_data, best_qn

    def _request_playurl(self, *, bvid: str, cid: str, page_url: str, qn: str = "64") -> dict[str, Any]:
        params = {
            "bvid": bvid,
            "cid": cid,
            "qn": qn,
            "fnval": "0",
            "otype": "json",
            "platform": "html5",
            "high_quality": "1",
        }
        url = PLAYURL_API + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers=self._headers(page_url))
        with urllib.request.urlopen(req, timeout=18) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))

    def _download_video(self, url: str, *, page_url: str, stem: str, limit_mb: int) -> str:
        suffix = ".mp4"
        parsed_ext = Path(urllib.parse.urlparse(url).path).suffix.lower()
        if parsed_ext in {".mp4", ".flv", ".m4s"}:
            suffix = parsed_ext
        path = self.temp_dir / f"{safe_filename(truncate(stem, 80))}{suffix}"
        req = urllib.request.Request(url, headers=self._headers(page_url))
        limit = int(limit_mb * 1024 * 1024)
        total = 0
        with urllib.request.urlopen(req, timeout=self.download_timeout) as resp, path.open("wb") as f:
            while True:
                chunk = resp.read(1024 * 256)
                if not chunk:
                    break
                total += len(chunk)
                if total > limit:
                    f.close()
                    path.unlink(missing_ok=True)
                    raise RuntimeError(f"下载超过大小限制 {limit_mb} MB")
                f.write(chunk)
        if path.stat().st_size == 0:
            path.unlink(missing_ok=True)
            raise RuntimeError("下载文件为空")
        return str(path)

    def _headers(self, page_url: str) -> dict[str, str]:
        headers = {
            "User-Agent": UA,
            "Referer": page_url,
            "Accept": "application/json,text/plain,*/*",
        }
        sessdata = self.sessdata or self._saved_sessdata()
        if sessdata:
            headers["Cookie"] = f"SESSDATA={sessdata}"
        return headers

    def _saved_sessdata(self) -> str:
        data = read_json(self.auth_path, {})
        if isinstance(data, dict):
            return str(data.get("sessdata") or "")
        return ""
