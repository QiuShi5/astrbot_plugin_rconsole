"""AstrBot port for R-console / R-plugin."""

from __future__ import annotations

import asyncio
import fnmatch
import json
import re
from dataclasses import dataclass
from pathlib import Path
from re import Pattern

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

from .services.bilibili_auth import BilibiliAuthService
from .services.capabilities import CapabilityService
from .services.common import ROutput, get_config_value, read_json
from .services.help_version import HelpVersionService
from .services.netease import NeteaseService
from .services.output_sender import OutputSender
from .services.paths import astrbot_plugin_data_dir
from .services.query import QueryService
from .services.resolver import ResolverService
from .services.state import StateService
from .services.translate import TranslateService


@dataclass(frozen=True)
class RuleSpec:
    """Yunzai rule migration descriptor."""

    name: str
    pattern: Pattern[str]
    handler_name: str
    permission: str = "user"
    source_module: str = ""


class RConsolePlugin(Star):
    """R插件 AstrBot 高复刻移植版。"""

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.plugin_dir = Path(__file__).resolve().parent
        self.resources_dir = self.plugin_dir / "resources"
        self.data_dir = astrbot_plugin_data_dir(self.plugin_dir)
        self.state = StateService(self.data_dir)
        self.output_sender = OutputSender(config=config, data_dir=self.data_dir)
        self.query_service = QueryService()
        self.bilibili_auth_service = BilibiliAuthService(self.data_dir)
        self._bilibili_qr_poll_task: asyncio.Task | None = None
        self._bilibili_qr_poll_session = ""
        self._bilibili_qr_poll_token = 0
        self.capability_service = CapabilityService(config)
        self.translate_service = TranslateService()
        self.resolver_service = ResolverService(
            temp_dir=self.data_dir / "temp",
            ytdlp_mode=(
                get_config_value(config, "ytdlp.mode", "direct")
                if get_config_value(config, "ytdlp.enabled", True)
                else "off"
            )
            or "direct",
            max_filesize_mb=int(get_config_value(config, "video_size_limit", 70) or 70),
            proxy=self._proxy_url(),
            bilibili_sessdata=self._bilibili_sessdata(),
            douyin_cookie=self._douyin_cookie(),
            douyin_duration=int(get_config_value(config, "douyin.duration", 480) or 480),
            xiaohongshu_cookie=self._xiaohongshu_cookie(),
            download_timeout=int(get_config_value(config, "video_download_timeout", 60) or 60),
        )
        self.help_version_service = HelpVersionService(self.resources_dir, output_dir=self.data_dir / "rendered")
        self.netease_service = NeteaseService(
            self.state,
            api_base=get_config_value(config, "netease.cloud_api_server", "") or "",
            resources_dir=self.resources_dir,
            output_dir=self.data_dir / "rendered",
        )
        self.rules = self._build_rules()
        logger.info("R插件 AstrBot版已加载：核心逻辑、正则分发和安全降级已启用。")

    @filter.command("rhelp", alias={"R帮助", "r帮助", "R插件帮助", "R菜单", "r菜单"})
    async def r_help(self, event: AstrMessageEvent):
        """R插件帮助菜单。"""
        await self._send_output(event, self.help_version_service.help_text())

    @filter.command("rversion", alias={"R版本", "R插件版本", "r版本"})
    async def r_version(self, event: AstrMessageEvent):
        """R插件版本信息。"""
        await self._send_output(event, self.help_version_service.version_text())

    @filter.command("rcap", alias={"R能力诊断", "r能力诊断", "R运行诊断", "r运行诊断"})
    async def r_capability_probe(self, event: AstrMessageEvent):
        """诊断账号/适配器/外部工具能力。"""
        await self._send_output(event, self.capability_service.probe(event))

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def rconsole_dispatch(self, event: AstrMessageEvent):
        """兼容原 R 插件 #命令与链接正则的统一分发入口。"""
        msg = self._message_text(event)
        if not msg:
            return
        conversation_reason = self._conversation_block_reason(event)
        if conversation_reason:
            logger.info(f"R plugin[{self._event_tag(event)}] conversation access blocked: {conversation_reason}")
            event.stop_event()
            return
        whitelist_reason = self._astrbot_whitelist_block_reason(event)
        if whitelist_reason:
            logger.info(f"R插件[{self._event_tag(event)}] AstrBot白名单拦截：{whitelist_reason}")
            event.stop_event()
            return

        for rule in self.rules:
            if rule.pattern.search(msg):
                tag = self._event_tag(event)
                logger.info(
                    f"R插件[{tag}] 命中规则：name={rule.name} handler={rule.handler_name} source={rule.source_module}"
                )
                if rule.permission == "admin" and not self._is_admin(event):
                    logger.info(f"R插件[{tag}] 权限拦截：rule={rule.name} 需要管理员")
                    await event.send(event.plain_result("您无权操作"))
                    event.stop_event()
                    return
                disabled_reason = self._rule_disabled_reason(rule)
                if disabled_reason:
                    logger.info(f"R插件[{tag}] 规则已禁用，不处理：rule={rule.name} reason={disabled_reason}")
                    return
                handler = getattr(self, rule.handler_name, None)
                if handler is None:
                    logger.warning(f"R插件[{tag}] 未找到处理器：rule={rule.name} handler={rule.handler_name}")
                    continue
                output = await handler(event, msg, rule)
                if output:
                    output = await self._prepare_output_for_send(event, output, rule)
                    logger.info(
                        f"R插件[{tag}] 输出：rule={rule.name} text={bool(output.text)} "
                        f"images={len(output.images)} audios={len(output.audios)} "
                        f"videos={len(output.videos)} files={len(output.files)} stop={output.stop}"
                    )
                    await self._send_output(event, output)
                    if output.stop:
                        event.stop_event()
                return

    async def terminate(self):
        """插件卸载/停用时释放资源。"""
        self._cancel_bilibili_qr_poll_task("插件卸载")
        logger.info("R插件 AstrBot版已卸载。")

    def _rule_disabled(self, rule: RuleSpec) -> bool:
        return bool(self._rule_disabled_reason(rule))

    def _conversation_block_reason(self, event: AstrMessageEvent) -> str:
        identifiers = self._conversation_identifiers(event)
        blacklist = self._config_string_list("conversation_blacklist")
        matched_blacklist = self._match_configured_identifier(identifiers, blacklist)
        if matched_blacklist:
            return f"conversation_blacklist={matched_blacklist}"
        whitelist = self._config_string_list("conversation_whitelist")
        if whitelist and not self._match_configured_identifier(identifiers, whitelist):
            return "not in conversation_whitelist"
        return ""

    def _conversation_identifiers(self, event: AstrMessageEvent) -> set[str]:
        platform = self._platform_name(event).strip()
        group_id = self._group_id(event).strip()
        session_id = self._session_id(event).strip()
        message_obj = getattr(event, "message_obj", None)
        raw_session_id = str(getattr(message_obj, "session_id", "") or "").strip()
        identifiers = {
            str(getattr(event, "unified_msg_origin", "") or "").strip(),
            raw_session_id,
            session_id,
            group_id,
        }
        if platform and group_id:
            identifiers.add(f"{platform}:group:{group_id}")
        if platform and raw_session_id:
            identifiers.add(f"{platform}:session:{raw_session_id}")
        if platform and session_id:
            identifiers.add(f"{platform}:session:{session_id}")
        return {item for item in identifiers if item}

    def _config_string_list(self, key: str) -> list[str]:
        value = get_config_value(self.config, key, []) or []
        if isinstance(value, str):
            value = re.split(r"[,;\n]", value)
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()]

    def _match_configured_identifier(self, identifiers: set[str], configured: list[str]) -> str:
        normalized = {item.lower(): item for item in identifiers}
        for item in configured:
            expected = str(item).strip()
            if not expected:
                continue
            expected_lower = expected.lower()
            if expected_lower in normalized:
                return expected
            if any(fnmatch.fnmatchcase(identifier.lower(), expected_lower) for identifier in identifiers):
                return expected
        return ""

    def _rule_disabled_reason(self, rule: RuleSpec) -> str:
        link_rules = {
            "douyin",
            "tiktok",
            "bili",
            "twitter_x",
            "acfun",
            "xhs",
            "bodian",
            "general",
            "youtube",
            "miyoushe",
            "netease",
            "weibo",
            "weishi",
            "zuiyou",
            "freyr",
            "summary",
            "qq_music",
            "qishui",
            "aircraft",
            "tieba",
            "xiaoheihe",
        }
        if rule.name not in link_rules:
            return ""
        if not get_config_value(self.config, "enable_link_resolvers", True):
            return "enable_link_resolvers=false"
        blacklist = get_config_value(self.config, "global_black_list", []) or []
        if isinstance(blacklist, str):
            blacklist = [x.strip() for x in blacklist.split(",") if x.strip()]
        aliases = {
            "douyin": {"douyin", "抖音"},
            "tiktok": {"tiktok", "TikTok"},
            "bili": {"bili", "哔哩哔哩", "B站", "bilibili"},
            "twitter_x": {"twitter", "x", "Twitter", "Twitter/X"},
            "acfun": {"acfun", "Acfun", "AcFun"},
            "xhs": {"xhs", "小红书"},
            "youtube": {"youtube", "YouTube"},
            "netease": {"netease", "网易云", "网易云音乐"},
            "weibo": {"weibo", "微博"},
            "summary": {"summary", "AI总结", "总结"},
        }
        names = aliases.get(rule.name, {rule.name}) | {rule.name}
        for item in blacklist:
            value = str(item).strip()
            if value in names:
                return f"global_black_list命中：{value}"
        return ""

    def _proxy_url(self) -> str:
        if not get_config_value(self.config, "force_overseas_server", False):
            return ""
        host = str(get_config_value(self.config, "proxy_addr", "") or "").strip()
        port = str(get_config_value(self.config, "proxy_port", "") or "").strip()
        if host and port:
            return f"http://{host}:{port}"
        return ""

    def _bilibili_sessdata(self) -> str:
        return str(get_config_value(self.config, "bilibili.sessdata", "") or "").strip()

    def _douyin_cookie(self) -> str:
        return str(get_config_value(self.config, "douyin.cookie", "") or "").strip()

    def _xiaohongshu_cookie(self) -> str:
        return str(get_config_value(self.config, "cookies.xiaohongshu", "") or "").strip()

    def _auto_fill_bilibili_config_after_login(self, output: ROutput) -> ROutput:
        text = output.text or ""
        if "登录成功" not in text:
            return output
        record = read_json(self.bilibili_auth_service.auth_path, {})
        sessdata = str(record.get("sessdata", "") if isinstance(record, dict) else "").strip()
        if not sessdata:
            output.text = text + "\n未捕获到 SESSDATA，无法自动回填插件配置。"
            logger.warning("R插件B站扫码登录成功但未捕获到SESSDATA，跳过配置回填。")
            return output
        saved, detail = self._write_bilibili_sessdata_to_config(sessdata)
        self._sync_runtime_bilibili_sessdata(sessdata)
        if saved:
            output.text = text + "\n已自动写入插件配置：bilibili.sessdata。若设置页未立即刷新，请刷新页面或重载插件。"
            logger.info(f"R插件B站SESSDATA已自动回填并持久化：{detail}")
        else:
            output.text = (
                text
                + "\n已写入当前运行时配置：bilibili.sessdata；但未找到可用的持久化保存接口，请刷新/重载后如仍为空再手动填写。"
            )
            logger.warning(f"R插件B站SESSDATA已写入运行时配置但持久化失败：{detail}")
        return output

    def _write_bilibili_sessdata_to_config(self, sessdata: str) -> tuple[bool, str]:
        try:
            if isinstance(self.config, dict):
                bilibili = self.config.get("bilibili")
                if not isinstance(bilibili, dict):
                    bilibili = {}
                    self.config["bilibili"] = bilibili
                bilibili["sessdata"] = sessdata
            else:
                return False, "config object is not dict-like"
        except Exception as exc:
            return False, f"运行时配置写入失败：{exc}"
        return self._persist_current_plugin_config()

    def _persist_current_plugin_config(self) -> tuple[bool, str]:
        saver = getattr(self.config, "save_config", None)
        if callable(saver):
            try:
                saver()
                return True, "save_config()"
            except Exception as exc:
                logger.warning(f"R插件B站SESSDATA调用save_config持久化失败：{exc}")
        path = getattr(self.config, "config_path", "")
        if path:
            try:
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                Path(path).write_text(json.dumps(dict(self.config), ensure_ascii=False, indent=2), encoding="utf-8-sig")
                return True, f"config_path={path}"
            except Exception as exc:
                return False, f"config_path写入失败：{exc}"
        return False, "未发现save_config()或config_path"

    def _sync_runtime_bilibili_sessdata(self, sessdata: str) -> None:
        try:
            self.resolver_service.bili_video.sessdata = sessdata
        except Exception as exc:
            logger.warning(f"R插件B站SESSDATA运行时同步到解析服务失败：{exc}")

    def _bilibili_qr_auto_poll_enabled(self) -> bool:
        return bool(get_config_value(self.config, "bilibili.qr_auto_poll", True))

    def _bilibili_qr_poll_interval(self) -> int:
        try:
            return max(1, min(30, int(get_config_value(self.config, "bilibili.qr_poll_interval", 3))))
        except Exception:
            return 3

    def _bilibili_qr_poll_timeout(self) -> int:
        try:
            return max(30, min(600, int(get_config_value(self.config, "bilibili.qr_poll_timeout", 180))))
        except Exception:
            return 180

    def _cancel_bilibili_qr_poll_task(self, reason: str = "") -> None:
        task = self._bilibili_qr_poll_task
        if task is not None and not task.done():
            task.cancel()
            if reason:
                logger.info(f"R插件B站扫码自动轮询已取消：{reason}")
        self._bilibili_qr_poll_task = None
        self._bilibili_qr_poll_session = ""
        self._bilibili_qr_poll_token += 1

    def _start_bilibili_qr_poll_task(self, event: AstrMessageEvent) -> None:
        if not self._bilibili_qr_auto_poll_enabled():
            logger.info(f"R插件[{self._event_tag(event)}] B站扫码自动轮询未启用")
            return
        self._cancel_bilibili_qr_poll_task("新的#rbq请求")
        session = self._session_id(event)
        interval = self._bilibili_qr_poll_interval()
        timeout = self._bilibili_qr_poll_timeout()
        self._bilibili_qr_poll_session = session
        token = self._bilibili_qr_poll_token
        self._bilibili_qr_poll_task = asyncio.create_task(
            self._bilibili_qr_poll_loop(event, session, token, interval, timeout)
        )
        logger.info(f"R插件[{self._event_tag(event)}] B站扫码自动轮询已启动：interval={interval}s timeout={timeout}s")

    async def _bilibili_qr_poll_loop(
        self, event: AstrMessageEvent, session: str, token: int, interval: int, timeout: int
    ) -> None:
        deadline = asyncio.get_running_loop().time() + timeout
        last_text = ""
        try:
            while asyncio.get_running_loop().time() < deadline:
                await asyncio.sleep(interval)
                if session != self._bilibili_qr_poll_session or token != self._bilibili_qr_poll_token:
                    return
                output = await self.bilibili_auth_service.poll_status()
                output = self._auto_fill_bilibili_config_after_login(output)
                text = output.text or ""
                terminal = self._bilibili_qr_poll_terminal(text)
                if text and text != last_text and (terminal or "等待在手机端确认" in text):
                    logger.info(f"R插件[{self._event_tag(event)}] B站扫码状态变化：{self._redact_cookie_text(text)}")
                last_text = text
                if terminal:
                    await self._send_output(event, output)
                    event.stop_event()
                    logger.info(
                        f"R插件[{self._event_tag(event)}] B站扫码自动轮询结束：{self._redact_cookie_text(text)}"
                    )
                    return
            await event.send(event.plain_result("B站扫码登录超时：未在有效时间内完成扫码确认，请重新发送 #rbq。"))
            event.stop_event()
            logger.info(f"R插件[{self._event_tag(event)}] B站扫码自动轮询超时：timeout={timeout}s")
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning(f"R插件[{self._event_tag(event)}] B站扫码自动轮询异常：{exc}")
            try:
                await event.send(event.plain_result(f"B站扫码登录自动查询失败：{exc}\n可手动发送 #rbs 查询当前状态。"))
                event.stop_event()
            except Exception as send_exc:
                logger.warning(f"R插件[{self._event_tag(event)}] B站扫码自动轮询异常提示发送失败：{send_exc}")
        finally:
            if session == self._bilibili_qr_poll_session and token == self._bilibili_qr_poll_token:
                self._bilibili_qr_poll_task = None
                self._bilibili_qr_poll_session = ""

    def _bilibili_qr_poll_terminal(self, text: str) -> bool:
        return any(marker in text for marker in ("登录成功", "二维码已失效", "状态查询失败", "尚未生成"))

    def _redact_cookie_text(self, text: str) -> str:
        return re.sub(r"(SESSDATA|bili_jct|DedeUserID|sid)=([^;\s,，]+)", r"\1=<redacted>", text)

    def _message_text(self, event: AstrMessageEvent) -> str:
        message_obj = getattr(event, "message_obj", None)
        if message_obj is not None:
            text = getattr(message_obj, "message_str", "") or ""
            if text:
                return text.strip()
        return ""

    def _astrbot_whitelist_block_reason(self, event: AstrMessageEvent) -> str:
        config = self._astrbot_runtime_config()
        if not config:
            return ""
        enabled = get_config_value(config, "platform_settings.enable_id_white_list", False)
        if not enabled:
            return ""
        whitelist = get_config_value(config, "platform_settings.id_whitelist", []) or []
        if isinstance(whitelist, str):
            whitelist = [x.strip() for x in whitelist.split(",") if x.strip()]
        whitelist = [str(x).strip() for x in whitelist if str(x).strip()]
        if not whitelist:
            return ""
        if self._platform_name(event).lower() == "webchat":
            return ""
        role = str(
            getattr(event, "role", "")
            or getattr(getattr(getattr(event, "message_obj", None), "sender", None), "role", "")
        ).lower()
        message_type = str(self._message_type_name(event)).lower()
        if (
            role == "admin"
            and "group" in message_type
            and get_config_value(config, "platform_settings.wl_ignore_admin_on_group", False)
        ):
            return ""
        if (
            role == "admin"
            and ("friend" in message_type or "private" in message_type)
            and get_config_value(config, "platform_settings.wl_ignore_admin_on_friend", False)
        ):
            return ""
        origin = str(getattr(event, "unified_msg_origin", "") or "").strip()
        group_id = str(self._group_id(event) or "").strip()
        if origin in whitelist or (group_id and group_id in whitelist):
            return ""
        return f"会话不在AstrBot全局白名单：origin={origin or '-'} group={group_id or '-'}"

    def _astrbot_runtime_config(self):
        candidates = [
            getattr(self.context, "astrbot_config", None),
            getattr(self.context, "config", None),
            getattr(self.context, "_config", None),
            getattr(self, "astrbot_config", None),
            self.config,
        ]
        for cfg in candidates:
            if cfg is not None and get_config_value(cfg, "platform_settings.enable_id_white_list", None) is not None:
                return cfg
        return None

    def _message_type_name(self, event: AstrMessageEvent) -> str:
        getter = getattr(event, "get_message_type", None)
        if callable(getter):
            try:
                value = getter()
                return str(getattr(value, "name", value))
            except Exception:
                pass
        return str(getattr(getattr(event, "message_obj", None), "type", ""))

    def _group_id(self, event: AstrMessageEvent) -> str:
        getter = getattr(event, "get_group_id", None)
        if callable(getter):
            try:
                return str(getter() or "")
            except Exception:
                pass
        message_obj = getattr(event, "message_obj", None)
        return str(getattr(message_obj, "group_id", "") or getattr(message_obj, "group", ""))

    def _event_tag(self, event: AstrMessageEvent) -> str:
        platform = self._platform_name(event) or "unknown"
        session = self._session_id(event)
        sender = self._sender_id(event) or "unknown"
        return f"{platform}:{session}:{sender}"

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

    def _sender_id(self, event: AstrMessageEvent) -> str:
        getter = getattr(event, "get_sender_id", None)
        if callable(getter):
            try:
                return str(getter())
            except Exception:
                pass
        sender = getattr(getattr(event, "message_obj", None), "sender", None)
        return str(getattr(sender, "user_id", "") or getattr(sender, "id", ""))

    def _session_id(self, event: AstrMessageEvent) -> str:
        return str(
            getattr(event, "unified_msg_origin", "")
            or getattr(getattr(event, "message_obj", None), "session_id", "")
            or "default"
        )

    def _is_admin(self, event: AstrMessageEvent) -> bool:
        for attr in ("is_admin", "isMaster", "is_master"):
            value = getattr(event, attr, None)
            if callable(value):
                try:
                    if value():
                        return True
                except Exception:
                    pass
            elif value:
                return True
        role = getattr(getattr(getattr(event, "message_obj", None), "sender", None), "role", "")
        return str(role).lower() in {"admin", "owner", "master"}

    async def _prepare_output_for_send(self, event: AstrMessageEvent, output: ROutput, rule: RuleSpec) -> ROutput:
        return await self.output_sender.prepare(event, output, rule.name)

    async def _send_output(self, event: AstrMessageEvent, output: ROutput) -> None:
        await self.output_sender.send(event, output)

    def _build_rules(self) -> list[RuleSpec]:
        """Build regex mapping from the original Yunzai rules."""
        specs = [
            (
                "help",
                r"^#*(R|r)(插件)?(命令|帮助|菜单|help|说明|功能|指令|使用说明)$",
                "handle_help",
                "user",
                "apps/help.js",
            ),
            ("doctor", r"^#医药查询(.*)$", "handle_query", "user", "apps/query.js"),
            ("cat", r"^#cat$", "handle_query", "user", "apps/query.js"),
            ("software", r"^#推荐软件$", "handle_query", "user", "apps/query.js"),
            ("buyer_show", r"^#买家秀$", "handle_query", "user", "apps/query.js"),
            ("cospro", r"^#累了$", "handle_query", "user", "apps/query.js"),
            (
                "pick_song",
                r"^#点歌\s*(.+?)(?:\s+([12]))?$|#听[1-9][0-9]*|#听[1-9]*$",
                "handle_song",
                "user",
                "apps/songRequest.js",
            ),
            ("play_song", r"^#播放\s*(.+?)(?:\s+([12]))?$", "handle_song", "user", "apps/songRequest.js"),
            ("upload", r"^#?上传$", "handle_song", "user", "apps/songRequest.js"),
            ("cloud", r"^#?我的云盘$|^#rnc$|^#RNC$", "handle_song", "admin", "apps/songRequest.js"),
            ("cloud_update", r"^#?云盘更新$|#?更新云盘$", "handle_song", "admin", "apps/songRequest.js"),
            ("cloud_upload", r"^#?上传云盘|#?上传网盘$|#rnu|#RNU", "handle_song", "admin", "apps/songRequest.js"),
            ("cloud_clean", r"^#?清除云盘缓存$", "handle_song", "admin", "apps/songRequest.js"),
            ("set_oversea", r"^#设置海外解析$", "handle_switcher", "admin", "apps/switchers.js"),
            ("clear_trash", r"^清理垃圾$", "handle_switcher", "admin", "apps/switchers.js"),
            ("set_whitelist", r"^#设置R信任用户(.*)", "handle_switcher", "admin", "apps/switchers.js"),
            ("get_whitelist", r"^#R信任用户$", "handle_switcher", "admin", "apps/switchers.js"),
            ("search_whitelist", r"^#查询R信任用户(.*)", "handle_switcher", "admin", "apps/switchers.js"),
            ("delete_whitelist", r"^#删除R信任用户(.*)", "handle_switcher", "admin", "apps/switchers.js"),
            ("trans", r"^(翻|trans)[中日文英俄韩]", "handle_tool", "user", "apps/tools.js"),
            (
                "douyin",
                r"((v|live)\.douyin\.com|webcast\.amemv\.com|iesdouyin\.com|"
                r"www\.douyin\.com/(video|note|live|share|jingxuan|discover))",
                "handle_tool",
                "user",
                "apps/tools.js",
            ),
            (
                "tiktok",
                r"(www\.tiktok\.com)|(vt\.tiktok\.com)|(vm\.tiktok\.com)",
                "handle_tool",
                "user",
                "apps/tools.js",
            ),
            ("bili_scan", r"^#(RBQ|rbq)$", "handle_tool", "admin", "apps/tools.js"),
            ("bili_state", r"^#(RBS|rbs)$", "handle_tool", "admin", "apps/tools.js"),
            (
                "bili",
                r"(bilibili\.com|b23\.tv|bili2233\.cn|m\.bilibili\.com|t\.bilibili\.com|^BV[1-9a-zA-Z]{10}$)",
                "handle_tool",
                "user",
                "apps/tools.js",
            ),
            (
                "twitter_x",
                r"https?:\/\/x\.com\/[0-9-a-zA-Z_]{1,20}\/status\/([0-9]*)",
                "handle_tool",
                "user",
                "apps/tools.js",
            ),
            ("acfun", r"(acfun\.cn|^ac[0-9]{8}$)", "handle_tool", "user", "apps/tools.js"),
            ("xhs", r"(xhslink\.com|xiaohongshu\.com)", "handle_tool", "user", "apps/tools.js"),
            ("bodian", r"(h5app\.kuwo\.cn)", "handle_tool", "user", "apps/tools.js"),
            (
                "general",
                r"(chenzhongtech\.com|kuaishou\.com|ixigua\.com|h5\.pipix\.com|"
                r"h5\.pipigx\.com|s\.xsj\.qq\.com|m\.okjike\.com)",
                "handle_tool",
                "user",
                "apps/tools.js",
            ),
            ("youtube", r"(youtube\.com|youtu\.be|music\.youtube\.com)", "handle_tool", "user", "apps/tools.js"),
            ("miyoushe", r"(miyoushe\.com)", "handle_tool", "user", "apps/tools.js"),
            ("netease", r"(music\.163\.com|163cn\.tv)", "handle_tool", "user", "apps/tools.js"),
            ("weibo", r"(weibo\.com|m\.weibo\.cn)", "handle_tool", "user", "apps/tools.js"),
            ("weishi", r"(weishi\.qq\.com)", "handle_tool", "user", "apps/tools.js"),
            ("zuiyou", r"share\.xiaochuankeji\.cn", "handle_tool", "user", "apps/tools.js"),
            ("freyr", r"(music\.apple\.com|open\.spotify\.com)", "handle_tool", "user", "apps/tools.js"),
            (
                "summary",
                r"(^#总结一下\s*(http|https):\/\/.*|mp\.weixin\.qq\.com|arxiv\.org|sspai\.com|"
                r"chinadaily\.com\.cn|zhihu\.com|github\.com|v2ex\.com)",
                "handle_tool",
                "user",
                "apps/tools.js",
            ),
            ("qq_music", r"(y\.qq\.com)", "handle_tool", "user", "apps/tools.js"),
            ("qishui", r"(qishui\.douyin\.com)", "handle_tool", "user", "apps/tools.js"),
            (
                "aircraft",
                r"https:\/\/t\.me\/(?:c\/\d+\/\d+\/\d+|c\/\d+\/\d+|\w+\/\d+\/\d+|\w+\/\d+\?\w+=\d+|\w+\/\d+)",
                "handle_tool",
                "user",
                "apps/tools.js",
            ),
            ("tieba", r"tieba\.baidu\.com", "handle_tool", "user", "apps/tools.js"),
            ("xiaoheihe", r"xiaoheihe\.cn", "handle_tool", "user", "apps/tools.js"),
            (
                "netease_status",
                r"^#(网易云状态|rns|RNS|网易云云盘状态|rncs|RNCS)$",
                "handle_tool",
                "admin",
                "apps/tools.js",
            ),
            ("netease_scan", r"^#(rnq|RNQ|rncq|RNCQ)$", "handle_tool", "admin", "apps/tools.js"),
            ("version", r"^#*R(插件)?版本$", "handle_version", "user", "apps/update.js"),
        ]
        return [
            RuleSpec(name, re.compile(pattern), handler, permission, source)
            for name, pattern, handler, permission, source in specs
        ]

    async def handle_help(self, event: AstrMessageEvent, msg: str, rule: RuleSpec) -> ROutput:
        return self.help_version_service.help_text()

    async def handle_version(self, event: AstrMessageEvent, msg: str, rule: RuleSpec) -> ROutput:
        return self.help_version_service.version_text()

    async def handle_query(self, event: AstrMessageEvent, msg: str, rule: RuleSpec) -> ROutput:
        if rule.name == "doctor":
            return await self.query_service.doctor(msg.replace("#医药查询", "", 1))
        if rule.name == "cat":
            return await self.query_service.cat()
        if rule.name == "software":
            return await self.query_service.software_recommended()
        if rule.name == "buyer_show":
            return await self.query_service.buyer_show()
        if rule.name == "cospro":
            return await self.query_service.cospro()
        return ROutput(text="未知查询功能")

    async def handle_song(self, event: AstrMessageEvent, msg: str, rule: RuleSpec) -> ROutput:
        session_id = self._session_id(event)
        max_list = int(get_config_value(self.config, "netease.song_request_max_list", 10) or 10)
        if rule.name == "pick_song":
            return await self.netease_service.pick_song(msg, session_id, max_list=max_list)
        if rule.name == "play_song":
            return await self.netease_service.play_song(msg)
        if rule.name in {"cloud", "cloud_update", "cloud_upload", "cloud_clean", "upload"}:
            base = "网易云云盘/上传入口已迁移；真实执行需要账号 Cookie、平台文件上传能力和受控外部工具。\n\n"
            diag = self.capability_service.probe(event)
            return ROutput(text=base + diag.text)
        return ROutput(text="未知点歌功能")

    async def handle_switcher(self, event: AstrMessageEvent, msg: str, rule: RuleSpec) -> ROutput:
        if rule.name == "set_oversea":
            os = self.state.toggle_oversea()
            return ROutput(text=f"当前服务器：{'海外服务器' if os else '国内服务器'}")
        if rule.name == "clear_trash":
            ret = self.state.clean_temp()
            return ROutput(
                text=f"手动清理垃圾完成:\n- 清理了0个全局垃圾文件\n- 清理了{ret['folders']}个空文件夹\n- 清理了{ret['files']}个插件临时文件"
            )
        if rule.name == "get_whitelist":
            users = self.state.whitelist()
            return ROutput(text="R信任用户列表：\n" + (",\n".join(users) if users else "暂无"))
        user_id = ""
        if rule.name == "set_whitelist":
            user_id = msg.replace("#设置R信任用户", "", 1).strip() or self._sender_id(event)
            return ROutput(text=self.state.add_whitelist(user_id)[1])
        if rule.name == "search_whitelist":
            user_id = msg.replace("#查询R信任用户", "", 1).strip() or self._sender_id(event)
            return ROutput(
                text=(
                    f"{'✅' if self.state.is_whitelisted(user_id) else '⚠️'} {user_id}"
                    f"{'已经是' if self.state.is_whitelisted(user_id) else '不是'}R插件的信任用户哦~"
                )
            )
        if rule.name == "delete_whitelist":
            user_id = msg.replace("#删除R信任用户", "", 1).strip() or self._sender_id(event)
            return ROutput(text=self.state.remove_whitelist(user_id)[1])
        return ROutput(text="未知开关功能")

    async def handle_tool(self, event: AstrMessageEvent, msg: str, rule: RuleSpec) -> ROutput:
        if rule.name == "trans":
            return await self.translate_service.translate(msg)
        if rule.name in {"netease_status", "netease_scan"}:
            return self.capability_service.probe(event)
        if rule.name == "bili_scan":
            output = await self.bilibili_auth_service.start_qr_login()
            if "已生成" in (output.text or ""):
                self._start_bilibili_qr_poll_task(event)
            return output
        if rule.name == "bili_state":
            sessdata = self._bilibili_sessdata()
            if sessdata:
                return await self.bilibili_auth_service.configured_status(sessdata)
            output = await self.bilibili_auth_service.poll_status()
            return self._auto_fill_bilibili_config_after_login(output)
        return await self.resolver_service.resolve(rule.name, msg)
