"""Netease music features ported from apps/songRequest.js and related tools."""

from __future__ import annotations

import urllib.parse
from pathlib import Path
from typing import Any

from .common import ROutput, request_json, truncate
from .card_renderer import CardRenderer
from .state import StateService

DEFAULT_API = "https://neteasecloudmusicapi.vercel.app"


def fmt_duration(ms: int | float | None) -> str:
    try:
        seconds = int(float(ms) / 1000)
    except Exception:
        return "00:00"
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


class NeteaseService:
    def __init__(self, state: StateService, api_base: str = "", resources_dir: Path | None = None, output_dir: Path | None = None):
        self.state = state
        self.api_base = (api_base or DEFAULT_API).rstrip("/")
        self.renderer = CardRenderer(resources_dir, output_dir=output_dir) if resources_dir is not None else None

    async def pick_song(self, msg: str, session_id: str, max_list: int = 10) -> ROutput:
        if msg.replace(" ", "").startswith("#听"):
            return await self.pick_number(msg, session_id)
        keyword = msg.replace("#点歌", "", 1).strip()
        song_type = "1"
        if keyword.endswith(" 2"):
            keyword = keyword[:-2].strip()
            song_type = "2"
        elif keyword.endswith(" 1"):
            keyword = keyword[:-2].strip()
        if not keyword:
            return ROutput(text="请输入歌曲关键词，例如：#点歌 晴天")
        endpoint = "/search"
        params: dict[str, Any] = {"keywords": keyword, "limit": max_list}
        if song_type == "2":
            params["type"] = 2000
        url = self.api_base + endpoint + "?" + urllib.parse.urlencode(params)
        try:
            data = await request_json(url, timeout=20)
        except Exception as exc:
            return ROutput(text=f"网易云搜索失败：{exc}")
        songs = []
        if song_type == "2":
            resources = (((data or {}).get("data") or {}).get("resources") or []) if isinstance(data, dict) else []
            for item in resources[:max_list]:
                base = item.get("baseInfo", {})
                main = base.get("mainSong", {})
                songs.append({
                    "id": main.get("id"),
                    "songName": main.get("name", "未知声音"),
                    "singerName": (base.get("dj") or {}).get("nickname", "未知作者"),
                    "duration": fmt_duration(base.get("duration")),
                    "type": "podcast",
                    "cover": base.get("coverUrl", ""),
                })
        else:
            rows = (((data or {}).get("result") or {}).get("songs") or []) if isinstance(data, dict) else []
            for item in rows[:max_list]:
                artists = item.get("artists") or item.get("ar") or []
                songs.append({
                    "id": item.get("id"),
                    "songName": item.get("name", "未知歌曲"),
                    "singerName": artists[0].get("name", "未知歌手") if artists else "未知歌手",
                    "duration": fmt_duration(item.get("duration") or item.get("dt")),
                    "type": "song",
                    "cover": "",
                })
        if not songs:
            return ROutput(text="暂未找到你想听的歌哦~")
        self.state.save_song_cache(session_id, songs)
        lines = ["🎵 R插件点歌列表"]
        for idx, song in enumerate(songs, 1):
            lines.append(f"#{idx} {song['songName']} - {song['singerName']} [{song['duration']}]")
        lines.append("\n发送 #听序号 播放，例如：#听1")
        out = ROutput(text="\n".join(lines), forward_texts=[f"{i+1}. {s['songName']} - {s['singerName']}\nID：{s.get('id')}\n时长：{s.get('duration')}" for i, s in enumerate(songs)])
        if self.renderer is not None:
            try:
                out.images.append(self.renderer.render_pick_song(songs))
            except Exception:
                pass
        return out

    async def pick_number(self, msg: str, session_id: str) -> ROutput:
        digits = "".join(ch for ch in msg if ch.isdigit())
        if not digits:
            return ROutput(text="请输入要听的序号，例如：#听1")
        idx = int(digits) - 1
        songs = self.state.get_song_cache(session_id)
        if idx < 0 or idx >= len(songs):
            return ROutput(text="点歌序号不存在，请先 #点歌 搜索后再 #听序号")
        song = songs[idx]
        return await self.play_by_id(song)

    async def play_song(self, msg: str) -> ROutput:
        keyword = msg.replace("#播放", "", 1).strip()
        if keyword.endswith(" 2") or keyword.endswith(" 1"):
            keyword = keyword[:-2].strip()
        if not keyword:
            return ROutput(text="请输入歌曲关键词，例如：#播放 晴天")
        search = await self.pick_song("#点歌 " + keyword, "__direct__", max_list=1)
        songs = self.state.get_song_cache("__direct__")
        if not songs:
            return search
        return await self.play_by_id(songs[0])

    async def play_by_id(self, song: dict[str, Any]) -> ROutput:
        song_id = song.get("id")
        if not song_id:
            return ROutput(text="歌曲数据缺少 ID，无法播放")
        url = self.api_base + "/song/url/v1?" + urllib.parse.urlencode({"id": song_id, "level": "exhigh"})
        try:
            data = await request_json(url, timeout=20)
            rows = data.get("data", []) if isinstance(data, dict) else []
            play_url = rows[0].get("url") if rows else ""
        except Exception as exc:
            return ROutput(text=f"获取播放链接失败：{exc}")
        info = f"🎶 {song.get('songName')} - {song.get('singerName')}\nID：{song_id}\n时长：{song.get('duration')}"
        if not play_url:
            return ROutput(text=info + "\n暂未获取到可播放链接，可能需要 Cookie 或歌曲受版权限制。")
        return ROutput(text=info + f"\n播放链接：{truncate(play_url, 300)}", audios=[play_url])

    async def status(self) -> ROutput:
        return ROutput(text="网易云状态功能已迁移为配置驱动：请在 AstrBot 插件配置中填写 netease.cookie / cloud_cookie。扫码登录与云盘上传属于平台/账号强耦合能力，后续按平台支持程度启用。")
