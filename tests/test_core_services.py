import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.help_version import HelpVersionService
from services.netease import NeteaseService
from services.resolver import ResolverService
from services.state import StateService
from services.translate import TranslateService


def _network_available(timeout: float = 4.0) -> bool:
    """True when outbound TCP is reachable from this environment."""
    import socket

    socket.setdefaulttimeout(timeout)
    try:
        with socket.create_connection(("1.1.1.1", 443), timeout=timeout):
            return True
    except Exception:
        return False


NETWORK = _network_available()


def test_help_version():
    svc = HelpVersionService(ROOT / "resources")
    help_out = svc.help_text()
    ver_out = svc.version_text()
    assert "R-Plugin" in help_out.text
    assert "#医药查询" in help_out.text
    assert "R插件版本" in ver_out.text


def test_state(tmp_dir=ROOT / "data" / "test_state"):
    svc = StateService(tmp_dir)
    os_value = svc.toggle_oversea()
    assert isinstance(os_value, bool)
    ok, msg = svc.add_whitelist("10001")
    assert "成功添加" in msg or "已存在" in msg
    assert svc.is_whitelisted("10001")
    ok, msg = svc.remove_whitelist("10001")
    assert "成功删除" in msg


async def test_services():
    resolver = ResolverService()
    state = StateService(ROOT / "data" / "test_song")
    netease = NeteaseService(state)

    if not NETWORK:
        # No outbound network in this sandbox: run offline-safe logic only and
        # leave the external-API assertions for a networked/real AstrBot env.
        out = await netease.pick_song("#听1", "empty")
        assert "序号不存在" in out.text or "请先" in out.text
        print("NETWORK_UNAVAILABLE: skipped external API assertions (resolver/translate)")
        return

    out = await resolver.resolve("bili", "BV1xx411c7mD")
    assert "哔哩哔哩" in out.text
    out = await resolver.resolve("summary", "#总结一下 https://example.com")
    assert "标题:" in out.text or "网页读取失败" in out.text
    trans = TranslateService()
    out = await trans.translate("翻英 你好")
    assert out.text
    out = await netease.pick_song("#听1", "empty")
    assert "序号不存在" in out.text or "请先" in out.text


if __name__ == "__main__":
    test_help_version()
    test_state()
    asyncio.run(test_services())
    print("task5 service tests ok")
