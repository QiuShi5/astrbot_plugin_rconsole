"""Persistent state service for R-console AstrBot port."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from .common import read_json, write_json


class StateService:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        (self.base_dir / "temp").mkdir(parents=True, exist_ok=True)
        self.state_path = self.base_dir / "state.json"
        self.whitelist_path = self.base_dir / "whitelist.json"
        self.song_cache_path = self.base_dir / "song_search_cache.json"
        self.cloud_cache_path = self.base_dir / "cloud_song_cache.json"

    def get_state(self) -> dict[str, Any]:
        return read_json(self.state_path, {"oversea": False, "resolve_disabled": []})

    def save_state(self, data: dict[str, Any]) -> None:
        write_json(self.state_path, data)

    def toggle_oversea(self) -> bool:
        data = self.get_state()
        data["oversea"] = not bool(data.get("oversea", False))
        self.save_state(data)
        return bool(data["oversea"])

    def get_value(self, key: str, default: Any = "") -> Any:
        return self.get_state().get(key, default)

    def set_value(self, key: str, value: Any) -> None:
        data = self.get_state()
        data[key] = value
        self.save_state(data)

    def whitelist(self) -> list[str]:
        data = read_json(self.whitelist_path, [])
        return [str(x) for x in data] if isinstance(data, list) else []

    def add_whitelist(self, user_id: str) -> tuple[bool, str]:
        user_id = str(user_id).strip()
        if not user_id:
            return False, "无效的R信任用户"
        data = self.whitelist()
        if user_id in data:
            return False, "R信任用户已存在，无须添加!"
        data.append(user_id)
        write_json(self.whitelist_path, data)
        return True, f"成功添加R信任用户：{user_id}"

    def remove_whitelist(self, user_id: str) -> tuple[bool, str]:
        user_id = str(user_id).strip()
        data = self.whitelist()
        if user_id not in data:
            return False, "R信任用户不存在，无须删除！"
        data = [x for x in data if x != user_id]
        write_json(self.whitelist_path, data)
        return True, f"成功删除R信任用户：{user_id}"

    def is_whitelisted(self, user_id: str) -> bool:
        return str(user_id).strip() in self.whitelist()

    def clean_temp(self, max_age_seconds: int = 24 * 3600) -> dict[str, int]:
        temp_dir = self.base_dir / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        now = time.time()
        files = 0
        folders = 0
        for path in sorted(temp_dir.rglob("*"), reverse=True):
            try:
                if path.is_file() and now - path.stat().st_mtime >= max_age_seconds:
                    path.unlink()
                    files += 1
                elif path.is_dir() and not any(path.iterdir()):
                    path.rmdir()
                    folders += 1
            except OSError:
                continue
        return {"files": files, "folders": folders}

    def save_song_cache(self, session_id: str, songs: list[dict[str, Any]]) -> None:
        data = read_json(self.song_cache_path, {})
        if not isinstance(data, dict):
            data = {}
        data[str(session_id)] = {"time": int(time.time()), "songs": songs}
        write_json(self.song_cache_path, data)

    def get_song_cache(self, session_id: str) -> list[dict[str, Any]]:
        data = read_json(self.song_cache_path, {})
        item = data.get(str(session_id), {}) if isinstance(data, dict) else {}
        songs = item.get("songs", []) if isinstance(item, dict) else []
        return songs if isinstance(songs, list) else []
