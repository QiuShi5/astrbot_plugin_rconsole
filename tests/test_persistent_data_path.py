from __future__ import annotations

import json
import shutil
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.paths import PLUGIN_NAME, astrbot_plugin_data_dir
from services.state import StateService


def install_astrbot_path_stub(root: Path) -> None:
    for name in list(sys.modules):
        if name == "astrbot" or name.startswith("astrbot."):
            del sys.modules[name]
    astrbot = types.ModuleType("astrbot")
    core = types.ModuleType("astrbot.core")
    utils = types.ModuleType("astrbot.core.utils")
    path_mod = types.ModuleType("astrbot.core.utils.astrbot_path")
    path_mod.get_astrbot_data_path = lambda: str(root / "data")
    sys.modules["astrbot"] = astrbot
    sys.modules["astrbot.core"] = core
    sys.modules["astrbot.core.utils"] = utils
    sys.modules["astrbot.core.utils.astrbot_path"] = path_mod


def test_plugin_data_survives_reinstall():
    base = ROOT / "data" / "test_persistent_path"
    shutil.rmtree(base, ignore_errors=True)
    install_root = base / "install_v1" / PLUGIN_NAME
    reinstall_root = base / "install_v2" / PLUGIN_NAME
    astrbot_root = base / "astrbot_root"
    legacy_dir = install_root / "data"
    legacy_dir.mkdir(parents=True, exist_ok=True)
    (legacy_dir / "state.json").write_text(json.dumps({"oversea": True, "resolve_disabled": ["bili"]}), encoding="utf-8")
    (legacy_dir / "bilibili_auth.json").write_text(json.dumps({"sessdata": "legacy-sess"}), encoding="utf-8")

    install_astrbot_path_stub(astrbot_root)
    data_dir = astrbot_plugin_data_dir(install_root)
    assert data_dir == astrbot_root / "data" / "plugin_data" / PLUGIN_NAME
    assert json.loads((data_dir / "state.json").read_text(encoding="utf-8"))["oversea"] is True
    assert json.loads((data_dir / "bilibili_auth.json").read_text(encoding="utf-8"))["sessdata"] == "legacy-sess"

    state = StateService(data_dir)
    state.add_whitelist("10001")

    reinstall_data_dir = astrbot_plugin_data_dir(reinstall_root)
    assert reinstall_data_dir == data_dir
    assert StateService(reinstall_data_dir).is_whitelisted("10001")
    assert json.loads((reinstall_data_dir / "bilibili_auth.json").read_text(encoding="utf-8"))["sessdata"] == "legacy-sess"


def main():
    test_plugin_data_survives_reinstall()
    print("persistent data path tests ok")


if __name__ == "__main__":
    main()
