from __future__ import annotations

import shutil
from pathlib import Path

PLUGIN_NAME = "astrbot_plugin_rconsole"
PERSISTENT_FILES = (
    "state.json",
    "whitelist.json",
    "song_search_cache.json",
    "cloud_song_cache.json",
    "bilibili_auth.json",
)


def astrbot_plugin_data_dir(plugin_dir: Path, plugin_name: str = PLUGIN_NAME) -> Path:
    try:
        from astrbot.core.utils.astrbot_path import get_astrbot_data_path

        base = Path(get_astrbot_data_path()) / "plugin_data" / plugin_name
    except Exception:
        base = plugin_dir / "data"
    base.mkdir(parents=True, exist_ok=True)
    (base / "temp").mkdir(parents=True, exist_ok=True)
    (base / "rendered").mkdir(parents=True, exist_ok=True)
    migrate_legacy_data(plugin_dir / "data", base)
    return base


def migrate_legacy_data(legacy_dir: Path, data_dir: Path) -> None:
    if not legacy_dir.exists():
        return
    if legacy_dir.resolve() == data_dir.resolve():
        return
    for filename in PERSISTENT_FILES:
        src = legacy_dir / filename
        dst = data_dir / filename
        if src.exists() and src.is_file() and not dst.exists():
            try:
                shutil.copy2(src, dst)
            except OSError:
                continue
