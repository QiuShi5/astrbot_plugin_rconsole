"""AstrBot stub end-to-end tests for the R-console plugin.

These tests simulate the AstrBot API surface used by main.py so the plugin can be
imported and exercised without a full AstrBot runtime.
"""

from __future__ import annotations

import asyncio
import importlib
import json
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def install_astrbot_stubs(with_components: bool = True) -> None:
    for name in list(sys.modules):
        if name == "astrbot" or name.startswith("astrbot."):
            del sys.modules[name]

    astrbot = types.ModuleType("astrbot")
    api = types.ModuleType("astrbot.api")
    event = types.ModuleType("astrbot.api.event")
    star = types.ModuleType("astrbot.api.star")

    class Logger:
        def info(self, *args, **kwargs):
            pass

        def warning(self, *args, **kwargs):
            pass

    class AstrBotConfig(dict):
        pass

    class Star:
        def __init__(self, context):
            self.context = context

    class Context:
        pass

    class AstrMessageEvent:
        pass

    class EventMessageType:
        ALL = "all"

    class Filter:
        def command(self, *args, **kwargs):
            def deco(func):
                return func
            return deco

        def event_message_type(self, *args, **kwargs):
            def deco(func):
                return func
            return deco

    api.AstrBotConfig = AstrBotConfig
    api.logger = Logger()
    event.AstrMessageEvent = AstrMessageEvent
    event.filter = Filter()
    event.filter.EventMessageType = EventMessageType
    star.Context = Context
    star.Star = Star

    sys.modules["astrbot"] = astrbot
    sys.modules["astrbot.api"] = api
    sys.modules["astrbot.api.event"] = event
    sys.modules["astrbot.api.star"] = star

    if with_components:
        comp = types.ModuleType("astrbot.api.message_components")

        class Plain:
            def __init__(self, text):
                self.text = text

        class Image:
            @classmethod
            def fromURL(cls, url):
                return ("image_url", url)

            @classmethod
            def fromFileSystem(cls, path):
                return ("image_file", path)

        class Record:
            def __init__(self, file=None, url=None):
                self.file = file
                self.url = url

        class Video:
            @classmethod
            def fromURL(cls, url):
                return ("video_url", url)

            @classmethod
            def fromFileSystem(cls, path=None):
                return ("video_file", path)

        class File:
            def __init__(self, file=None, name=None):
                self.file = file
                self.name = name

        comp.Plain = Plain
        comp.Image = Image
        comp.Record = Record
        comp.Video = Video
        comp.File = File
        sys.modules["astrbot.api.message_components"] = comp


class MessageObj:
    def __init__(self, text: str, role: str = "member", platform_name: str = "stub-adapter"):
        self.message_str = text
        self.session_id = "session-1"
        self.sender = types.SimpleNamespace(user_id="10001", role=role)
        self.platform_name = platform_name


class FakeEvent:
    def __init__(self, text: str, *, admin: bool = False, role: str = "member", platform_name: str = "stub-adapter"):
        self.message_obj = MessageObj(text, role="admin" if admin else role, platform_name=platform_name)
        self.unified_msg_origin = f"{platform_name}:group:session-1"
        self.sent = []
        self.stopped = False
        self._admin = admin

    def is_admin(self):
        return self._admin

    def get_sender_id(self):
        return "10001"

    def get_platform_name(self):
        return self.message_obj.platform_name

    def plain_result(self, text):
        return {"type": "plain", "text": text}

    def chain_result(self, chain):
        return {"type": "chain", "chain": chain}

    def image_result(self, path):
        return {"type": "image", "path": path}

    async def send(self, payload):
        self.sent.append(payload)

    def stop_event(self):
        self.stopped = True


class FakePluginConfig(dict):
    def __init__(self, config_path: Path, initial: dict | None = None):
        data = {"bilibili": {"sessdata": "", "qr_auto_poll": False}}
        if initial:
            data.update(initial)
        super().__init__(data)
        self.config_path = str(config_path)
        self.saved_count = 0

    def save_config(self):
        self.saved_count += 1
        Path(self.config_path).write_text(json.dumps(self, ensure_ascii=False, indent=2), encoding="utf-8-sig")


class FakeOneBot:
    def __init__(self, fail_files: set[str] | None = None, timeout_files: set[str] | None = None):
        self.sent = []
        self.fail_files = fail_files or set()
        self.timeout_files = timeout_files or set()

    async def send_private_msg(self, user_id, message):
        file_value = message[0].get("data", {}).get("file", "") if message else ""
        if file_value in self.timeout_files:
            raise RuntimeError("ActionFailed retcode=1200 status=failed message=Timeout: NTEvent ...")
        if file_value in self.fail_files:
            raise RuntimeError(f"reject video source: {file_value}")
        self.sent.append(("private", user_id, message))

    async def send_group_msg(self, group_id, message):
        file_value = message[0].get("data", {}).get("file", "") if message else ""
        if file_value in self.timeout_files:
            raise RuntimeError("ActionFailed retcode=1200 status=failed message=Timeout: NTEvent ...")
        if file_value in self.fail_files:
            raise RuntimeError(f"reject video source: {file_value}")
        self.sent.append(("group", group_id, message))


class RejectVideoEvent(FakeEvent):
    def __init__(self, *args, with_bot: bool = False, fail_files: set[str] | None = None, timeout_files: set[str] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        if with_bot:
            self.bot = FakeOneBot(fail_files=fail_files, timeout_files=timeout_files)

    async def send(self, payload):
        if payload.get("type") == "chain" and any(isinstance(x, tuple) and x[0] == "video_file" for x in payload.get("chain", [])):
            raise RuntimeError("onebot video rejected")
        self.sent.append(payload)


async def main():
    install_astrbot_stubs(with_components=True)
    module = importlib.import_module("astrbot_plugin_rconsole.main")
    plugin = module.RConsolePlugin(module.Context(), {"netease": {"song_request_max_list": 3}})

    assert len(plugin.rules) == 46

    ev = FakeEvent("#R帮助")
    await plugin.rconsole_dispatch(ev)
    assert ev.stopped
    assert ev.sent and ev.sent[0]["type"] == "chain"
    assert any(getattr(x, "text", "").startswith("R-Plugin") for x in ev.sent[0]["chain"])
    assert any(isinstance(x, tuple) and x[0] == "image_file" for x in ev.sent[0]["chain"])

    ev = FakeEvent("media matrix", platform_name="matrix")
    await plugin._send_output(ev, module.ROutput(text="media", images=[str(Path(__file__).resolve())], videos=[str(Path(__file__).resolve())]))
    assert len(ev.sent) == 1 and ev.sent[0]["type"] == "chain"
    assert any(isinstance(x, tuple) and x[0] == "image_file" for x in ev.sent[0]["chain"])
    assert any(isinstance(x, tuple) and x[0] == "video_file" for x in ev.sent[0]["chain"])

    ev = FakeEvent("media onebot", platform_name="aiocqhttp")
    await plugin._send_output(ev, module.ROutput(text="media", images=[str(Path(__file__).resolve())], videos=[str(Path(__file__).resolve())]))
    assert [x["type"] for x in ev.sent] == ["chain", "chain"]
    assert any(getattr(x, "text", "") == "media" for x in ev.sent[0]["chain"])
    assert any(isinstance(x, tuple) and x[0] == "image_file" for x in ev.sent[0]["chain"])
    assert ev.sent[1]["chain"] == [("video_file", str(Path(__file__).resolve()))]

    ev = FakeEvent("media generic", platform_name="generic")
    await plugin._send_output(ev, module.ROutput(text="media", images=[str(Path(__file__).resolve())], videos=[str(Path(__file__).resolve())]))
    assert [x["type"] for x in ev.sent] == ["chain"]
    assert any(getattr(x, "text", "") == "media" for x in ev.sent[0]["chain"])
    assert any(isinstance(x, tuple) and x[0] == "image_file" for x in ev.sent[0]["chain"])
    assert any(isinstance(x, tuple) and x[0] == "video_file" for x in ev.sent[0]["chain"])

    existing_video = plugin.data_dir / "temp" / "reject.mp4"
    existing_video.parent.mkdir(parents=True, exist_ok=True)
    existing_video.write_bytes(b"fake mp4")
    ev = FakeEvent("media onebot unified sender", platform_name="aiocqhttp")
    ev.bot = FakeOneBot()
    await plugin._send_output(ev, module.ROutput(text="media", videos=[str(existing_video)]))
    assert [x["type"] for x in ev.sent] == ["chain", "chain"]
    assert any(getattr(x, "text", "") == "media" for x in ev.sent[0]["chain"])
    assert ev.sent[1]["chain"] == [("video_file", str(existing_video))]
    assert ev.bot.sent == []

    # OneBot-like adapters are still sent through AstrBot components from the unified sender.
    ev = FakeEvent("media onebot unified repeat", platform_name="aiocqhttp")
    ev.bot = FakeOneBot()
    await plugin._send_output(ev, module.ROutput(text="media", videos=[str(existing_video)]))
    assert [x["type"] for x in ev.sent] == ["chain", "chain"]
    assert any(getattr(x, "text", "") == "media" for x in ev.sent[0]["chain"])
    assert ev.sent[1]["chain"] == [("video_file", str(existing_video))]
    assert ev.bot.sent == []

    # Component failures degrade to a text pointer; adapter-native bot APIs are not called.
    ev = RejectVideoEvent("media onebot component rejected", platform_name="aiocqhttp", with_bot=True)
    await plugin._send_output(ev, module.ROutput(text="media", videos=[str(existing_video)]))
    assert ev.bot.sent == []
    assert [x["type"] for x in ev.sent] == ["chain", "plain"]
    assert "[视频]" in ev.sent[1]["text"]

    ev = RejectVideoEvent("media onebot missing video", platform_name="aiocqhttp", with_bot=True)
    await plugin._send_output(ev, module.ROutput(text="media", videos=["/tmp/missing-rconsole-video.mp4"]))
    assert [x["type"] for x in ev.sent] == ["chain", "plain"]
    assert "视频文件不存在，无法发送" in ev.sent[1]["text"]

    ev = RejectVideoEvent("media onebot reject", platform_name="aiocqhttp")
    await plugin._send_output(ev, module.ROutput(text="media", videos=["/tmp/reject.mp4"]))
    assert [x["type"] for x in ev.sent] == ["chain", "plain"]
    assert any(getattr(x, "text", "") == "media" for x in ev.sent[0]["chain"])
    assert "视频文件不存在，无法发送" in ev.sent[1]["text"]

    ev = FakeEvent("#R版本")
    await plugin.rconsole_dispatch(ev)
    assert ev.sent and ev.sent[0]["type"] == "chain"

    ev = FakeEvent("#R插件更新", admin=True)
    await plugin.rconsole_dispatch(ev)
    assert ev.sent == [] and not ev.stopped

    assert plugin.output_sender._safe_video_extension('https://example.com/a.mp4?sign=21b3c1fb', '') == '.mp4'
    assert plugin.output_sender._safe_video_extension('https://example.com/a.mp4sign21b3c1fb', '') == '.mp4'
    assert plugin.output_sender._stable_url_token('https://example.com/a.mp4?sign=21b3c1fb')

    local_xhs_video = plugin.data_dir / "temp" / "xhs-preview.mp4"
    local_xhs_video.parent.mkdir(parents=True, exist_ok=True)
    local_xhs_video.write_bytes(b"fake mp4")
    ev = FakeEvent("matrix xhs preview", platform_name="matrix")
    output = module.ROutput(text="xhs", videos=[str(local_xhs_video)])
    prepared = await plugin._prepare_output_for_send(ev, output, module.RuleSpec("xhs", __import__('re').compile("x"), "handle_tool"))
    assert prepared.videos == [str(local_xhs_video)]
    assert prepared.files == []

    plugin = module.RConsolePlugin(module.Context(), {})
    called_downloads = []
    async def fake_download(source, rule_name=""):
        called_downloads.append((source, rule_name))
        return "/tmp/localized.mp4"
    plugin.output_sender._download_remote_video_for_file = fake_download
    ev = FakeEvent("douyin unified localize", platform_name="matrix")
    remote_video = "https://aweme.snssdk.com/aweme/v1/play/?video_id=abc"
    output = module.ROutput(text="douyin", videos=[remote_video])
    prepared = await plugin._prepare_output_for_send(ev, output, module.RuleSpec("douyin", __import__('re').compile("x"), "handle_tool"))
    assert called_downloads == [(remote_video, "douyin")]
    assert prepared.videos == ["/tmp/localized.mp4"]
    assert prepared.files == []

    plugin = module.RConsolePlugin(module.Context(), {"douyin": {"display_source_link": False}})
    output = module.ROutput(text="ok\n\u94fe\u63a5\uff1ahttps://example.com/a\nkeep")
    ev = FakeEvent("source link hidden", platform_name="matrix")
    prepared = await plugin._prepare_output_for_send(ev, output, module.RuleSpec("douyin", __import__('re').compile("x"), "handle_tool"))
    assert prepared.text == "ok\nkeep"

    plugin = module.RConsolePlugin(module.Context(), {})
    output = module.ROutput(text="ok\n\u94fe\u63a5\uff1ahttps://example.com/a\nkeep")
    prepared = await plugin._prepare_output_for_send(ev, output, module.RuleSpec("general", __import__('re').compile("x"), "handle_tool"))
    assert prepared.text == "ok\nkeep"

    output = module.ROutput(text="ok\n\u94fe\u63a5\uff1ahttps://example.com/a\n\u89e3\u6790\u5931\u8d25\uff1abad")
    prepared = await plugin._prepare_output_for_send(ev, output, module.RuleSpec("general", __import__('re').compile("x"), "handle_tool"))
    assert "\u94fe\u63a5\uff1ahttps://example.com/a" in prepared.text

    plugin = module.RConsolePlugin(module.Context(), {"source_link_display": {"douyin": True}})
    output = module.ROutput(text="ok\n\u94fe\u63a5\uff1ahttps://example.com/a\nkeep")
    prepared = await plugin._prepare_output_for_send(ev, output, module.RuleSpec("douyin", __import__('re').compile("x"), "handle_tool"))
    assert prepared.text == "ok\n\u94fe\u63a5\uff1ahttps://example.com/a\nkeep"

    ev = FakeEvent("#设置海外解析", admin=False)
    await plugin.rconsole_dispatch(ev)
    assert ev.sent[0]["type"] == "plain" and "无权" in ev.sent[0]["text"]

    ev = FakeEvent("#设置海外解析", admin=True)
    await plugin.rconsole_dispatch(ev)
    assert ev.sent and "当前服务器" in ev.sent[0]["text"]

    ev = FakeEvent("https://www.bilibili.com/video/BV1xx411c7mD")
    await plugin.rconsole_dispatch(ev)
    assert ev.sent and ("哔哩哔哩" in ev.sent[0].get("text", "") or ev.sent[0]["type"] == "chain")

    plugin = module.RConsolePlugin(module.Context(), {"conversation_blacklist": ["stub-adapter:group:session-1"]})
    ev = FakeEvent("https://www.bilibili.com/video/BV1xx411c7mD")
    await plugin.rconsole_dispatch(ev)
    assert ev.sent == [] and ev.stopped

    plugin = module.RConsolePlugin(module.Context(), {"conversation_whitelist": ["other-session"]})
    ev = FakeEvent("https://www.bilibili.com/video/BV1xx411c7mD")
    await plugin.rconsole_dispatch(ev)
    assert ev.sent == [] and ev.stopped

    plugin = module.RConsolePlugin(module.Context(), {"conversation_whitelist": ["session-1"]})
    plugin.resolver_service.resolve = lambda rule_name, msg: asyncio.sleep(0, result=module.ROutput(text="conversation whitelist allowed"))
    ev = FakeEvent("https://www.bilibili.com/video/BV1xx411c7mD")
    await plugin.rconsole_dispatch(ev)
    assert ev.sent and ev.sent[0]["text"] == "conversation whitelist allowed"

    plugin = module.RConsolePlugin(module.Context(), {"conversation_whitelist": ["session-*"], "conversation_blacklist": ["stub-adapter:group:session-1"]})
    ev = FakeEvent("https://www.bilibili.com/video/BV1xx411c7mD")
    await plugin.rconsole_dispatch(ev)
    assert ev.sent == [] and ev.stopped

    ctx = module.Context()
    ctx.astrbot_config = {"platform_settings": {"enable_id_white_list": True, "id_whitelist": ["other-session"], "wl_ignore_admin_on_group": False, "wl_ignore_admin_on_friend": False}}
    plugin = module.RConsolePlugin(ctx, {})
    ev = FakeEvent("https://www.bilibili.com/video/BV1xx411c7mD", platform_name="aiocqhttp")
    await plugin.rconsole_dispatch(ev)
    assert ev.sent == [] and ev.stopped

    ctx = module.Context()
    ctx.astrbot_config = {"platform_settings": {"enable_id_white_list": True, "id_whitelist": ["aiocqhttp:group:session-1"], "wl_ignore_admin_on_group": False, "wl_ignore_admin_on_friend": False}}
    plugin = module.RConsolePlugin(ctx, {})
    plugin.resolver_service.resolve = lambda rule_name, msg: asyncio.sleep(0, result=module.ROutput(text="白名单允许"))
    ev = FakeEvent("https://www.bilibili.com/video/BV1xx411c7mD", platform_name="aiocqhttp")
    await plugin.rconsole_dispatch(ev)
    assert ev.sent and ev.sent[0]["text"] == "白名单允许"

    ev = FakeEvent("#R能力诊断")
    await plugin.r_capability_probe(ev)
    assert ev.sent and "能力诊断" in ev.sent[0]["text"]

    ev = FakeEvent("https://www.bilibili.com/video/BV1xx411c7mD")
    plugin = module.RConsolePlugin(module.Context(), {"enable_link_resolvers": False})
    await plugin.rconsole_dispatch(ev)
    assert ev.sent == []

    ev = FakeEvent("https://www.bilibili.com/video/BV1xx411c7mD")
    plugin = module.RConsolePlugin(module.Context(), {"global_black_list": ["B站"]})
    await plugin.rconsole_dispatch(ev)
    assert ev.sent == []

    schema = json.loads((ROOT / "astrbot_plugin_rconsole" / "_conf_schema.json").read_text(encoding="utf-8"))
    assert schema["conversation_whitelist"]["type"] == "list"
    assert schema["conversation_whitelist"]["default"] == []
    assert schema["conversation_blacklist"]["type"] == "list"
    assert schema["conversation_blacklist"]["default"] == []
    assert schema["bilibili"]["items"]["sessdata"]["description"].startswith("哔哩哔哩 SESSDATA")
    assert schema["bilibili"]["items"]["sessdata"]["type"] == "string"
    assert schema["bilibili"]["items"]["qr_auto_poll"]["default"] is True

    plugin = module.RConsolePlugin(module.Context(), {"bilibili": {"sessdata": "configured", "qr_auto_poll": False}})
    ev = FakeEvent("#rbs", admin=True)
    await plugin.rconsole_dispatch(ev)
    assert ev.sent and "已在插件配置中检测到" in ev.sent[0]["text"]

    ev = FakeEvent("#R能力诊断")
    await plugin.r_capability_probe(ev)
    assert ev.sent and "B站 SESSDATA: 已配置" in ev.sent[0]["text"]

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        cfg = FakePluginConfig(td_path / "astrbot_plugin_rconsole_config.json")
        plugin = module.RConsolePlugin(module.Context(), cfg)
        plugin.bilibili_auth_service.auth_path = td_path / "bilibili_auth.json"
        plugin.bilibili_auth_service.auth_path.write_text(json.dumps({"qrcode_key": "manual-key", "sessdata": "manual-autofill-sess"}, ensure_ascii=False), encoding="utf-8")
        plugin.bilibili_auth_service.poll_status = lambda: asyncio.sleep(0, result=module.ROutput(text="B站扫码登录成功。已保存到插件 data/bilibili_auth.json。\nCookie 字段：SESSDATA, bili_jct"))
        ev = FakeEvent("#rbs", admin=True)
        await plugin.rconsole_dispatch(ev)
        persisted = json.loads((td_path / "astrbot_plugin_rconsole_config.json").read_text(encoding="utf-8-sig"))
        assert cfg["bilibili"]["sessdata"] == "manual-autofill-sess"
        assert persisted["bilibili"]["sessdata"] == "manual-autofill-sess"
        assert cfg.saved_count == 1
        assert plugin._bilibili_sessdata() == "manual-autofill-sess"
        assert plugin.resolver_service.bili_video.sessdata == "manual-autofill-sess"
        assert ev.sent and "已自动写入插件配置" in ev.sent[0]["text"]
        assert "manual-autofill-sess" not in ev.sent[0]["text"]

    ev = FakeEvent("#rbq", admin=True)
    plugin.bilibili_auth_service.start_qr_login = lambda: asyncio.sleep(0, result=module.ROutput(text="B站扫码登录已生成。", images=[str(Path(__file__).resolve())]))
    await plugin.rconsole_dispatch(ev)
    assert ev.sent and ev.sent[0]["type"] == "chain" and "B站扫码登录" in getattr(ev.sent[0]["chain"][0], "text", "")
    assert plugin._bilibili_qr_poll_task is None

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        cfg = FakePluginConfig(td_path / "astrbot_plugin_rconsole_config.json", {"bilibili": {"qr_auto_poll": True}})
        plugin = module.RConsolePlugin(module.Context(), cfg)
        plugin._bilibili_qr_poll_interval = lambda: 0
        plugin._bilibili_qr_poll_timeout = lambda: 2
        plugin.bilibili_auth_service.auth_path = td_path / "bilibili_auth.json"
        plugin.bilibili_auth_service.auth_path.write_text(json.dumps({"qrcode_key": "auto-key", "sessdata": "auto-autofill-sess"}, ensure_ascii=False), encoding="utf-8")
        plugin.bilibili_auth_service.start_qr_login = lambda: asyncio.sleep(0, result=module.ROutput(text="B站扫码登录已生成。", images=[str(Path(__file__).resolve())]))
        plugin.bilibili_auth_service.poll_status = lambda: asyncio.sleep(0, result=module.ROutput(text="B站扫码登录成功。已保存到插件 data/bilibili_auth.json。\nCookie 字段：SESSDATA, bili_jct"))
        ev = FakeEvent("#rbq", admin=True)
        await plugin.rconsole_dispatch(ev)
        await asyncio.sleep(0.05)
        persisted = json.loads((td_path / "astrbot_plugin_rconsole_config.json").read_text(encoding="utf-8-sig"))
        assert len(ev.sent) >= 2 and "B站扫码登录成功" in ev.sent[-1]["text"]
        assert "已自动写入插件配置" in ev.sent[-1]["text"]
        assert "auto-autofill-sess" not in ev.sent[-1]["text"]
        assert cfg["bilibili"]["sessdata"] == "auto-autofill-sess"
        assert persisted["bilibili"]["sessdata"] == "auto-autofill-sess"
        assert cfg.saved_count == 1
        assert plugin.resolver_service.bili_video.sessdata == "auto-autofill-sess"
        assert plugin._bilibili_qr_poll_task is None

    plugin = module.RConsolePlugin(module.Context(), {"bilibili": {"qr_auto_poll": True}})
    plugin._bilibili_qr_poll_interval = lambda: 0
    plugin._bilibili_qr_poll_timeout = lambda: 0
    plugin.bilibili_auth_service.start_qr_login = lambda: asyncio.sleep(0, result=module.ROutput(text="B站扫码登录已生成。"))
    plugin.bilibili_auth_service.poll_status = lambda: asyncio.sleep(0, result=module.ROutput(text="B站扫码状态：未扫码，请继续扫码。"))
    ev = FakeEvent("#rbq", admin=True)
    await plugin.rconsole_dispatch(ev)
    await asyncio.sleep(0.05)
    assert any("B站扫码登录超时" in item.get("text", "") for item in ev.sent)

    plugin = module.RConsolePlugin(module.Context(), {"bilibili": {"qr_auto_poll": True}})
    plugin._bilibili_qr_poll_interval = lambda: 5
    plugin._bilibili_qr_poll_timeout = lambda: 30
    plugin.bilibili_auth_service.start_qr_login = lambda: asyncio.sleep(0, result=module.ROutput(text="B站扫码登录已生成。"))
    first = FakeEvent("#rbq", admin=True)
    await plugin.rconsole_dispatch(first)
    first_task = plugin._bilibili_qr_poll_task
    assert first_task is not None and not first_task.done()
    second = FakeEvent("#rbq", admin=True)
    await plugin.rconsole_dispatch(second)
    await asyncio.sleep(0)
    assert first_task.cancelled()
    assert plugin._bilibili_qr_poll_task is not None and plugin._bilibili_qr_poll_task is not first_task
    plugin._cancel_bilibili_qr_poll_task("test cleanup")

    install_astrbot_stubs(with_components=False)
    # Force reload without message component module to verify text fallback path.
    for name in ["astrbot_plugin_rconsole.main", "astrbot_plugin_rconsole.services.output_sender"]:
        sys.modules.pop(name, None)
    module = importlib.import_module("astrbot_plugin_rconsole.main")
    plugin = module.RConsolePlugin(module.Context(), {})
    ev = FakeEvent("#R帮助")
    await plugin.rconsole_dispatch(ev)
    assert ev.sent and ev.sent[0]["type"] == "plain" and ev.sent[1]["type"] == "image"

    print("astrbot stub e2e tests ok")


if __name__ == "__main__":
    asyncio.run(main())
