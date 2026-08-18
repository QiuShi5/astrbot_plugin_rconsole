"""Link resolver service for R-console AstrBot port.

This module ports the original R-plugin resolver surface. It now provides:
- first-class Bilibili/Netease metadata APIs;
- OpenGraph extraction for article/social pages;
- optional yt-dlp backed extraction/download for many video platforms;
- explicit capability reporting when an account/cookie-only feature cannot be
  completed in the current environment.
"""

from __future__ import annotations

import asyncio
import html
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from .bilibili_video import BilibiliVideoService
from .common import USER_AGENT, ROutput, first_url, request_json, request_text, strip_html, truncate
from .media_downloader import YtDlpService

try:
    from astrbot.api import logger as LOGGER
except Exception:  # pragma: no cover - plain unit tests outside AstrBot.

    class _FallbackLogger:
        """Minimal no-op logger for tests running without AstrBot."""

        def debug(self, *args, **kwargs):
            pass

        def info(self, *args, **kwargs):
            pass

        def warning(self, *args, **kwargs):
            pass

        def error(self, *args, **kwargs):
            pass

    LOGGER = _FallbackLogger()


class ResolverService:
    def __init__(
        self,
        *,
        temp_dir: Path | None = None,
        ytdlp_mode: str = "direct",
        max_filesize_mb: int = 70,
        proxy: str = "",
        bilibili_sessdata: str = "",
        douyin_cookie: str = "",
        douyin_duration: int = 480,
        xiaohongshu_cookie: str = "",
        download_timeout: int = 60,
        bili_comments: bool = False,
        bili_comment_count: int = 5,
        douyin_comments: bool = False,
        douyin_comment_count: int = 5,
        weibo_comments: bool = False,
        weibo_comment_count: int = 5,
    ):
        temp = temp_dir or Path("data/temp")
        self.media = YtDlpService(temp, mode=ytdlp_mode, max_filesize_mb=max_filesize_mb, proxy=proxy)
        self.bili_video = BilibiliVideoService(
            temp, max_filesize_mb=max_filesize_mb, sessdata=bilibili_sessdata, download_timeout=download_timeout
        )
        self.douyin_cookie = douyin_cookie.strip()
        self.douyin_duration = int(douyin_duration or 480)
        self.xiaohongshu_cookie = xiaohongshu_cookie.strip()
        self.bili_comments = bool(bili_comments)
        self.bili_comment_count = int(bili_comment_count or 5)
        self.douyin_comments = bool(douyin_comments)
        self.douyin_comment_count = int(douyin_comment_count or 5)
        self.weibo_comments = bool(weibo_comments)
        self.weibo_comment_count = int(weibo_comment_count or 5)

    async def resolve(self, rule_name: str, msg: str) -> ROutput:
        method = getattr(self, f"resolve_{rule_name}", None)
        if method:
            return await method(msg)
        return await self.resolve_generic(rule_name, msg)

    async def resolve_generic(self, rule_name: str, msg: str) -> ROutput:
        url = first_url(msg)
        if not url:
            return ROutput(text=f"✅ 识别：{self.display_name(rule_name)}\n未找到可解析链接。")
        # Prefer yt-dlp for media-like platforms; fall back to OpenGraph.
        if rule_name in {
            "douyin",
            "tiktok",
            "twitter_x",
            "acfun",
            "youtube",
            "general",
            "weishi",
            "zuiyou",
            "tieba",
            "xiaoheihe",
            "qishui",
        }:
            out = await self.media.extract(url, platform=self.display_name(rule_name))
            if "未检测到 yt-dlp" not in out.text and "yt-dlp 解析失败" not in out.text:
                return out
        return await self.resolve_opengraph(rule_name, msg)

    def display_name(self, name: str) -> str:
        return {
            "douyin": "抖音",
            "tiktok": "TikTok",
            "bili": "哔哩哔哩",
            "twitter_x": "Twitter/X",
            "acfun": "AcFun",
            "xhs": "小红书",
            "bodian": "波点音乐",
            "general": "通用解析",
            "youtube": "YouTube",
            "miyoushe": "米游社",
            "netease": "网易云音乐",
            "weibo": "微博",
            "instagram": "Instagram",
            "kugou": "酷狗音乐",
            "weixin_channel": "微信视频号",
            "weishi": "微视",
            "zuiyou": "最右",
            "freyr": "Apple Music / Spotify",
            "summary": "AI总结",
            "qq_music": "QQ音乐",
            "qishui": "汽水音乐",
            "aircraft": "小飞机",
            "tieba": "贴吧",
            "xiaoheihe": "小黑盒",
        }.get(name, name)

    async def resolve_opengraph(self, rule_name: str, msg: str) -> ROutput:
        url = first_url(msg)
        if not url:
            return ROutput(text=f"✅ 识别：{self.display_name(rule_name)}\n未找到链接。")
        try:
            html_text = await request_text(url, timeout=20)
        except Exception as exc:
            return ROutput(text=f"✅ 识别：{self.display_name(rule_name)}\n链接：{url}\n网页读取失败：{exc}")
        meta = self._extract_meta(html_text)
        title = meta.get("og:title") or meta.get("twitter:title") or meta.get("title") or url
        desc = meta.get("og:description") or meta.get("description") or meta.get("twitter:description") or ""
        image = meta.get("og:image") or meta.get("twitter:image") or ""
        video = meta.get("og:video") or meta.get("og:video:url") or meta.get("twitter:player:stream") or ""
        if image.startswith("//"):
            image = "https:" + image
        if video.startswith("//"):
            video = "https:" + video
        text = f"✅ 识别：{self.display_name(rule_name)}\n标题：{truncate(title, 120)}\n链接：{url}"
        if desc:
            text += f"\n简介：{truncate(desc, 240)}"
        if video:
            text += "\n已提取页面视频字段。"
        return ROutput(
            text=text,
            images=[image] if image.startswith("http") else [],
            videos=[video] if video.startswith("http") else [],
        )

    def _extract_meta(self, html_text: str) -> dict[str, str]:
        result: dict[str, str] = {}
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.I | re.S)
        if title_match:
            result["title"] = html.unescape(strip_html(title_match.group(1)))
        for match in re.finditer(r"<meta\s+([^>]+)>", html_text, re.I | re.S):
            attrs = dict(
                (k.lower(), html.unescape(v)) for k, v in re.findall(r"([a-zA-Z_:.-]+)=[\"'](.*?)[\"']", match.group(1))
            )
            key = attrs.get("property") or attrs.get("name")
            content = attrs.get("content")
            if key and content:
                result[key.lower()] = strip_html(content)
        return result

    async def resolve_douyin(self, msg: str) -> ROutput:
        url = first_url(msg)
        if not url:
            return ROutput(text="✅ 识别：抖音\n未找到可解析链接。")
        final_url, ttwid = await self._expand_douyin_url(url)
        detail_id = self._extract_douyin_id(final_url) or self._extract_douyin_id(url)
        LOGGER.info(
            "R插件抖音解析开始：url=%s final_url=%s detail_id=%s ytdlp_mode=%s cookie=%s",
            url,
            final_url or url,
            detail_id or "",
            self.media.mode,
            "已配置" if self.douyin_cookie else "未配置",
        )
        media_candidates = [url]
        if final_url and final_url != url:
            media_candidates.append(final_url)
        if detail_id:
            media_candidates.append(f"https://www.douyin.com/video/{detail_id}")
        seen: set[str] = set()
        last_media_text = ""
        for candidate in media_candidates:
            if candidate in seen:
                continue
            seen.add(candidate)
            media_out = await self.media.extract(candidate, platform="抖音")
            last_media_text = media_out.text
            if media_out.videos or media_out.files:
                LOGGER.info(
                    "R插件抖音yt-dlp解析成功：candidate=%s images=%d videos=%d files=%d",
                    candidate,
                    len(media_out.images),
                    len(media_out.videos),
                    len(media_out.files),
                )
                return media_out
            LOGGER.info(
                "R插件抖音yt-dlp未产出视频，准备尝试下一路径/官方接口：candidate=%s images=%d videos=%d files=%d",
                candidate,
                len(media_out.images),
                len(media_out.videos),
                len(media_out.files),
            )

        if not detail_id:
            return ROutput(text=f"✅ 识别：抖音\n链接：{url}\n未提取到作品 ID，无法继续解析。")
        if not self.douyin_cookie:
            return ROutput(
                text=(
                    "✅ 识别：抖音\n"
                    f"作品 ID：{detail_id}\n"
                    "yt-dlp 未提取到媒体直链，当前抖音官方接口解析需要在配置 douyin.cookie 中填写有效 Cookie。"
                )
            )
        try:
            data = await request_json(
                self._douyin_detail_api(detail_id), headers=self._douyin_headers(ttwid=ttwid), timeout=20
            )
            item = data.get("aweme_detail") if isinstance(data, dict) else None
            if not item:
                raise ValueError(f"接口未返回 aweme_detail：{truncate(str(data), 240)}")
            output = self._format_douyin_item(item, final_url or url)
            if self.douyin_comments and detail_id:
                comments = await self.fetch_douyin_comments(detail_id, self.douyin_comment_count)
                if comments:
                    output.text += "\n💬 评论：\n" + "\n".join(comments)
            LOGGER.info(
                "R插件抖音官方接口解析成功：detail_id=%s images=%d videos=%d audios=%d",
                detail_id,
                len(output.images),
                len(output.videos),
                len(output.audios),
            )
            return output
        except Exception as exc:
            LOGGER.warning("R插件抖音官方接口解析失败 id=%s url=%s: %s", detail_id, url, exc)
            extra = f"\nyt-dlp 返回：{truncate(last_media_text, 240)}" if last_media_text else ""
            return ROutput(text=f"✅ 识别：抖音\n作品 ID：{detail_id}\n链接：{url}\n官方接口解析失败：{exc}{extra}")

    async def _expand_douyin_url(self, url: str) -> tuple[str, str]:
        if "v.douyin.com" not in urllib.parse.urlparse(url).netloc.lower():
            return url, ""
        return await asyncio.to_thread(self._expand_douyin_url_sync, url)

    def _expand_douyin_url_sync(self, url: str) -> tuple[str, str]:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                final_url = resp.geturl() or url
                ttwid = self._extract_cookie_value(resp.headers.get_all("Set-Cookie") or [], "ttwid")
                return final_url, ttwid
        except urllib.error.HTTPError as exc:
            final_url = exc.geturl() or exc.headers.get("Location") or url
            ttwid = self._extract_cookie_value(exc.headers.get_all("Set-Cookie") or [], "ttwid")
            return final_url, ttwid
        except Exception as exc:
            LOGGER.warning("R插件抖音短链展开失败 url=%s: %s", url, exc)
            return url, ""

    def _extract_cookie_value(self, cookies: list[str], name: str) -> str:
        for cookie in cookies or []:
            match = re.search(rf"(?:^|;\s*){re.escape(name)}=([^;]+)", cookie)
            if match:
                return match.group(1)
        return ""

    def _extract_douyin_id(self, url: str) -> str:
        decoded = urllib.parse.unquote(url or "")
        for pattern in (r"/(?:video|note)/(\d+)", r"/share/slides/(\d+)", r"modal_id=(\d+)", r"aweme_id=(\d+)"):
            match = re.search(pattern, decoded)
            if match:
                return match.group(1)
        return ""

    def _douyin_detail_api(self, aweme_id: str) -> str:
        query = {
            "device_platform": "webapp",
            "aid": "6383",
            "channel": "channel_pc_web",
            "aweme_id": aweme_id,
            "pc_client_type": "1",
            "version_code": "190500",
            "version_name": "19.5.0",
            "cookie_enabled": "true",
            "screen_width": "1344",
            "screen_height": "756",
            "browser_language": "zh-CN",
            "browser_platform": "Win32",
            "browser_name": "Firefox",
            "browser_version": "118.0",
            "browser_online": "true",
            "engine_name": "Gecko",
            "engine_version": "109.0",
            "os_name": "Windows",
            "os_version": "10",
            "cpu_core_num": "16",
            "device_memory": "",
            "platform": "PC",
        }
        return "https://www.douyin.com/aweme/v1/web/aweme/detail/?" + urllib.parse.urlencode(query)

    def _douyin_headers(self, *, ttwid: str = "") -> dict[str, str]:
        cookie = self.douyin_cookie
        if ttwid and "ttwid=" not in cookie:
            cookie = (cookie.rstrip("; ") + f"; ttwid={ttwid}").lstrip("; ")
        return {
            "Accept": "application/json,text/plain,*/*",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
            "Cookie": cookie,
            "Referer": "https://www.douyin.com/",
            "User-Agent": USER_AGENT,
        }

    def _format_douyin_item(self, item: dict[str, Any], source_url: str) -> ROutput:
        desc = str(item.get("desc") or "无简介")
        author = (item.get("author") or {}).get("nickname") or "未知作者"
        aweme_type = item.get("aweme_type")
        cover = self._last_url(((item.get("video") or {}).get("cover") or {}).get("url_list") or [])
        text = f"✅ 识别：抖音，{author}\n📝 简介：{truncate(desc, 300)}\n链接：{source_url}"

        images = [cover] if cover else []
        videos: list[str] = []
        audios: list[str] = []

        video = item.get("video") or {}
        if aweme_type in {0, 4, 51, 55, 58, 61, 109} or video:
            duration = int(float(video.get("duration") or 0) / 1000)
            if duration and self.douyin_duration > 0 and duration >= self.douyin_duration:
                text += f"\n当前视频时长约 {duration // 60}:{duration % 60:02d}，超过配置上限 {self.douyin_duration} 秒，未发送视频。"
            else:
                video_url = self._douyin_video_url(video)
                if video_url:
                    videos.append(video_url)
                    text += "\n已提取视频直链。"

        if not videos and item.get("images"):
            images = [
                self._last_url(img.get("url_list") or []) for img in item.get("images") or [] if isinstance(img, dict)
            ]
            images = [img for img in images if img]
            if images:
                text += f"\n已提取 {len(images)} 张图片。"

        return ROutput(text=text, images=images, videos=videos, audios=audios)

    def _douyin_video_url(self, video: dict[str, Any]) -> str:
        uri = (video.get("play_addr") or {}).get("uri") or ""
        if uri:
            return "https://aweme.snssdk.com/aweme/v1/play/?" + urllib.parse.urlencode(
                {
                    "video_id": uri,
                    "ratio": "1080p",
                    "line": "0",
                }
            )
        for key in ("play_addr", "play_addr_h264", "play_addr_265"):
            url = self._last_url((video.get(key) or {}).get("url_list") or [])
            if url:
                return url
        return ""

    def _last_url(self, values: list[Any]) -> str:
        for value in reversed(values or []):
            value = html.unescape(str(value or ""))
            if value.startswith("http"):
                return value
        return ""

    async def resolve_bili(self, msg: str) -> ROutput:
        url = first_url(msg)
        final_url = url
        bvid = self._extract_bvid(msg.strip())
        if not bvid and url:
            final_url = await self._expand_bili_url(url)
            bvid = self._extract_bvid(final_url)
            if final_url != url:
                LOGGER.info("R插件B站短链展开：%s -> %s", url, final_url)
        if not bvid and url:
            LOGGER.info("R插件B站链接未提取到BVID，退回yt-dlp：%s", url)
            return await self.media.extract(url, platform="哔哩哔哩")
        if not bvid:
            return await self.resolve_generic("bili", msg)
        page_url = (
            final_url if final_url and self._extract_bvid(final_url) else f"https://www.bilibili.com/video/{bvid}"
        )
        api = "https://api.bilibili.com/x/web-interface/view?" + urllib.parse.urlencode({"bvid": bvid})
        try:
            data = await request_json(api, headers=self._bili_headers(page_url), timeout=15)
            item = data.get("data", {}) if isinstance(data, dict) else {}
            if not item:
                raise RuntimeError(f"B站API未返回data：{data}")
        except Exception as exc:
            LOGGER.warning("R插件B站view API失败 bvid=%s url=%s: %s", bvid, page_url, exc)
            return ROutput(text=f"✅ 识别：哔哩哔哩\nBVID：{bvid}\n获取视频信息失败：{exc}")
        title = item.get("title", "未知标题")
        desc = str(item.get("desc") or "")
        pic = item.get("pic", "")
        stat = item.get("stat", {}) or {}
        cid = item.get("cid") or ""
        text = self._format_bili_native_text(title=title, desc=desc, stat=stat)
        LOGGER.info("R插件B站解析：bvid=%s cid=%s title=%s", bvid, cid, truncate(title, 60))
        media_out = await self.media.extract(page_url, platform="哔哩哔哩")
        videos = media_out.videos if "已提取" in media_out.text else []
        extra = ""
        if videos:
            LOGGER.info("R插件B站yt-dlp解析成功：bvid=%s videos=%d", bvid, len(videos))
        else:
            if "yt-dlp 解析失败" in media_out.text:
                LOGGER.warning("R插件B站yt-dlp失败，将使用官方playurl fallback：bvid=%s error=%s", bvid, media_out.text)
            elif "已在配置中关闭" in media_out.text or "未检测到 yt-dlp" in media_out.text:
                LOGGER.info("R插件B站yt-dlp不可用/关闭，将使用官方playurl fallback：bvid=%s", bvid)
            native = await self.bili_video.extract_video(bvid=bvid, cid=cid, title=title)
            if native.videos:
                videos = native.videos
                LOGGER.info("R插件B站官方playurl fallback成功：bvid=%s videos=%d", bvid, len(videos))
            elif native.text:
                extra = "\n" + native.text
                LOGGER.warning("R插件B站官方playurl fallback未产出视频：bvid=%s text=%s", bvid, native.text)
        comments_extra = ""
        if self.bili_comments and cid:
            comments = await self.fetch_bili_comments(cid, self.bili_comment_count)
            if comments:
                comments_extra = "\n💬 评论：\n" + "\n".join(comments)
        return ROutput(text=text + extra + comments_extra, images=[pic] if pic else [], videos=videos)

    async def fetch_bili_comments(self, oid: str | int, limit: int = 5) -> list[str]:
        """Fetch Bilibili comments as plain text (public reply API, no login needed)."""
        try:
            url = "https://api.bilibili.com/x/v2/reply?" + urllib.parse.urlencode(
                {"type": 1, "oid": oid, "pn": 1, "ps": int(limit or 5), "sort": 2}
            )
            data = await request_json(url, headers=self._bili_headers("https://www.bilibili.com/"), timeout=15)
            replies = (data.get("data") or {}).get("replies") or []
            result = []
            for r in replies[:limit]:
                member = (r.get("member") or {}).get("uname") or "未知用户"
                content = r.get("content") or {}
                msg = content.get("message") if isinstance(content, dict) else ""
                if msg:
                    result.append(f"{member}：{strip_html(str(msg))}")
            return result
        except Exception as exc:
            LOGGER.warning("R插件B站评论拉取失败 oid=%s: %s", oid, exc)
            return []

    async def fetch_douyin_comments(self, aweme_id: str | int, limit: int = 5) -> list[str]:
        """Fetch Douyin comments as plain text. Requires a valid douyin.cookie; otherwise returns []."""
        if not self.douyin_cookie:
            return []
        try:
            url = "https://www.douyin.com/aweme/v1/web/comment/list/?" + urllib.parse.urlencode(
                {
                    "aweme_id": aweme_id,
                    "cursor": 0,
                    "count": int(limit or 5),
                    "device_platform": "webapp",
                    "aid": "6383",
                }
            )
            data = await request_json(url, headers=self._douyin_headers(), timeout=20)
            comments = (data.get("comments") or []) if isinstance(data, dict) else []
            result = []
            for c in comments[:limit]:
                user = (c.get("user") or {}).get("nickname") or "未知用户"
                text = str(c.get("text") or "")
                if text:
                    result.append(f"{user}：{strip_html(text)}")
            return result
        except Exception as exc:
            LOGGER.warning("R插件抖音评论拉取失败 aweme_id=%s: %s", aweme_id, exc)
            return []

    async def fetch_weibo_comments(self, id_or_url: str, limit: int = 5) -> list[str]:
        """Fetch Weibo comments as plain text via the public comment API (best effort)."""
        try:
            # mid extraction: numeric or from a weibo.com URL
            mid = re.sub(r"^.*?\D(\d{10,})$", r"\1", str(id_or_url))
            if not mid or not mid.isdigit():
                return []
            url = "https://weibo.com/ajax/statuses/buildComments?" + urllib.parse.urlencode(
                {"flow": 0, "is_reload": 1, "id": mid, "is_show_bulletin": 2, "max_id": 0, "count": int(limit or 5)}
            )
            data = await request_json(url, timeout=20)
            comments = data.get("data") or []
            result = []
            for c in comments[:limit]:
                user = (c.get("user") or {}).get("screen_name") or "未知用户"
                text = str(c.get("text") or "")
                if text:
                    result.append(f"{user}：{strip_html(text)}")
            return result
        except Exception as exc:
            LOGGER.warning("R插件微博评论拉取失败 id=%s: %s", id_or_url, exc)
            return []

    def _format_bili_native_text(self, *, title: str, desc: str, stat: dict[str, Any]) -> str:
        """Format ordinary Bilibili video text like the original R plugin."""
        data = {
            "点赞": stat.get("like", 0),
            "硬币": stat.get("coin", 0),
            "收藏": stat.get("favorite", 0),
            "分享": stat.get("share", 0),
            "总播放量": stat.get("view", 0),
            "弹幕数量": stat.get("danmaku", 0),
            "评论": stat.get("reply", 0),
        }
        info = " | ".join(f"{key}：{self._format_bili_number(value)}" for key, value in data.items())
        filtered_desc = self._filter_bili_desc_link(desc)
        return f"✅ 识别：哔哩哔哩，{title}\n{info}\n📝 简介：{self._truncate_bili_intro(filtered_desc, 50)}"

    def _truncate_bili_intro(self, value: str, limit: int = 50) -> str:
        value = value or ""
        if limit in (0, -1) or len(value) <= limit:
            return value
        return value[:limit] + "..."

    def _format_bili_number(self, value: Any) -> str:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value)
        if number >= 10000:
            return f"{number / 10000:.1f}万"
        if number.is_integer():
            return str(int(number))
        return str(value)

    def _filter_bili_desc_link(self, desc: str) -> str:
        return (
            re.sub(r"(?:https?://)?(?:www\.|music\.)?youtube\.com/[A-Za-z\d._?%&+\-=/#]*", "", desc or "")
            .replace("\n", "")
            .strip()
        )

    def _extract_bvid(self, text: str) -> str:
        match = re.search(r"BV[1-9a-zA-Z]{10}", text or "")
        return match.group(0) if match else ""

    async def _expand_bili_url(self, url: str) -> str:
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc.lower()
        if self._extract_bvid(url) or not any(token in host for token in ("b23.tv", "bili2233.cn", "bilibili.com")):
            return url
        return await asyncio.to_thread(self._expand_bili_url_sync, url)

    def _expand_bili_url_sync(self, url: str) -> str:
        req = urllib.request.Request(url, headers=self._bili_headers("https://www.bilibili.com/"), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.geturl() or url
        except urllib.error.HTTPError as exc:
            # Bilibili pages may return 412 after redirect; HTTPError still keeps the final URL.
            return exc.geturl() or exc.headers.get("Location") or url
        except Exception as exc:
            LOGGER.warning("R插件B站短链展开失败：%s: %s", url, exc)
            return url

    def _bili_headers(self, referer: str) -> dict[str, str]:
        return {
            "User-Agent": USER_AGENT,
            "Referer": referer or "https://www.bilibili.com/",
            "Accept": "application/json,text/plain,*/*",
        }

    async def resolve_netease(self, msg: str) -> ROutput:
        url = first_url(msg)
        match = re.search(r"(?:id=|song/)(\d+)", url or msg)
        if not match:
            return await self.resolve_generic("netease", msg)
        song_id = match.group(1)
        api = "https://neteasecloudmusicapi.vercel.app/song/detail?" + urllib.parse.urlencode({"ids": song_id})
        try:
            data = await request_json(api, timeout=15)
            song = (data.get("songs") or [{}])[0]
        except Exception as exc:
            return ROutput(text=f"✅ 识别：网易云音乐\n歌曲 ID：{song_id}\n获取详情失败：{exc}")
        artists = song.get("ar") or []
        album = song.get("al") or {}
        play = await self._netease_play_url(song_id)
        artists_text = artists[0].get("name", "未知歌手") if artists else "未知歌手"
        text = (
            f"✅ 识别：网易云音乐\n歌曲：{song.get('name', '未知歌曲')}\n歌手：{artists_text}\n"
            f"专辑：{album.get('name', '未知专辑')}\nID：{song_id}"
        )
        if play:
            text += "\n已获取播放链接。"
        pic = album.get("picUrl", "")
        return ROutput(text=text, images=[pic] if pic else [], audios=[play] if play else [])

    async def _netease_play_url(self, song_id: str) -> str:
        api = "https://neteasecloudmusicapi.vercel.app/song/url/v1?" + urllib.parse.urlencode(
            {"id": song_id, "level": "exhigh"}
        )
        try:
            data = await request_json(api, timeout=15)
            rows = data.get("data", []) if isinstance(data, dict) else []
            return rows[0].get("url") if rows else ""
        except Exception:
            return ""

    async def resolve_weibo(self, msg: str) -> ROutput:
        output = await self.resolve_opengraph("weibo", msg)
        if self.weibo_comments:
            comments = await self.fetch_weibo_comments(msg, self.weibo_comment_count)
            if comments:
                output.text += "\n💬 评论：\n" + "\n".join(comments)
        return output

    async def resolve_instagram(self, msg: str) -> ROutput:
        return await self.resolve_opengraph("instagram", msg)

    async def resolve_kugou(self, msg: str) -> ROutput:
        return await self.resolve_opengraph("kugou", msg)

    async def resolve_weixin_channel(self, msg: str) -> ROutput:
        return await self.resolve_opengraph("weixin_channel", msg)

    async def resolve_xhs(self, msg: str) -> ROutput:
        url = self._extract_xhs_url(msg)
        if not url:
            return ROutput(text="✅ 识别：小红书\n未找到可解析链接。")
        LOGGER.info("R插件小红书解析开始：url=%s cookie=%s", url, "已配置" if self.xiaohongshu_cookie else "未配置")
        try:
            note_id, xsec_token, xsec_source, final_url = await self._parse_xhs_note_params(url)
        except Exception as exc:
            LOGGER.warning("R插件小红书链接展开失败 url=%s: %s", url, exc)
            return ROutput(text=f"✅ 识别：小红书\n链接：{url}\n短链展开失败：{exc}")

        missing = []
        if not self.xiaohongshu_cookie:
            missing.append("Cookie")
        if not note_id:
            missing.append("笔记 id")
        if not xsec_token:
            missing.append("xsec_token")
        if not xsec_source:
            missing.append("xsec_source")
        if missing:
            return ROutput(
                text=(
                    "✅ 识别：小红书\n"
                    f"链接：{final_url or url}\n"
                    "解析缺少必要信息：" + "、".join(missing) + "\n"
                    "请确认已在配置 cookies.xiaohongshu 填写有效 Cookie，并发送带 xsec_token/xsec_source 的完整分享链接。"
                )
            )

        req_url = (
            "https://www.xiaohongshu.com/explore/"
            + note_id
            + "?"
            + urllib.parse.urlencode(
                {
                    "xsec_token": xsec_token,
                    "xsec_source": xsec_source,
                }
            )
        )
        try:
            html_text = await request_text(req_url, headers=self._xhs_headers(), timeout=20)
            note = self._extract_xhs_note_from_html(html_text, note_id)
            if not note:
                fallback = self._format_xhs_fallback(html_text, final_url or req_url, msg)
                if fallback:
                    LOGGER.info(
                        "R插件小红书使用页面元信息兜底：note_id=%s images=%d videos=%d",
                        note_id,
                        len(fallback.images),
                        len(fallback.videos),
                    )
                    return fallback
                return ROutput(text="✅ 识别：小红书\n检测到无效的小红书 Cookie，或该笔记需要重新登录后获取 Cookie。")
            output = self._format_xhs_note(note, final_url or req_url)
            LOGGER.info(
                "R插件小红书解析成功：note_id=%s type=%s images=%d videos=%d",
                note_id,
                note.get("type") or "",
                len(output.images),
                len(output.videos),
            )
            return output
        except Exception as exc:
            try:
                fallback = self._format_xhs_fallback(
                    html_text if "html_text" in locals() else "", final_url or req_url, msg
                )
            except Exception:
                fallback = None
            if fallback:
                LOGGER.info(
                    "R插件小红书INITIAL_STATE失败后使用兜底：note_id=%s err=%s images=%d videos=%d",
                    note_id,
                    exc,
                    len(fallback.images),
                    len(fallback.videos),
                )
                return fallback
            LOGGER.warning("R插件小红书解析失败 note_id=%s url=%s: %s", note_id, req_url, exc)
            return ROutput(text=f"✅ 识别：小红书\n链接：{final_url or req_url}\n解析失败：{exc}")

    def _extract_xhs_url(self, msg: str) -> str:
        normalized = html.unescape(msg or "").strip().replace("amp;", "")
        xml_match = re.search(
            r"<url>\s*(https?://(?:www\.)?(?:xhslink|xiaohongshu)\.com/.*?)\s*</url>", normalized, re.I | re.S
        )
        if xml_match:
            return self._clean_xhs_url(xml_match.group(1))
        match = re.search(r"https?://(?:www\.)?(?:xhslink|xiaohongshu)\.com/[^\s\]）)>\"']+", normalized)
        return self._clean_xhs_url(match.group(0)) if match else ""

    def _clean_xhs_url(self, url: str) -> str:
        value = html.unescape(str(url or "")).strip().replace("amp;", "")
        value = re.split(r"<\/?url\b|<\/?msg\b|<\/?appmsg\b", value, maxsplit=1, flags=re.I)[0]
        value = value.rstrip(".,;，。；\r\n\t ")
        return value

    async def _parse_xhs_note_params(self, url: str) -> tuple[str, str, str, str]:
        parsed = urllib.parse.urlparse(url)
        final_url = url
        if "xhslink.com" in parsed.netloc.lower():
            final_url = await asyncio.to_thread(self._expand_xhs_url_sync, url)
            parsed = urllib.parse.urlparse(final_url)
        decoded = urllib.parse.unquote(final_url)
        note_id = self._extract_xhs_note_id(decoded)
        query = urllib.parse.parse_qs(parsed.query)
        xsec_source = self._first_query_value(query, "xsec_source") or "pc_feed"
        xsec_token = self._first_query_value(query, "xsec_token")
        if not xsec_token:
            redirect_path = self._first_query_value(query, "redirectPath")
            if redirect_path:
                redirect_query = urllib.parse.parse_qs(urllib.parse.urlparse(redirect_path).query)
                xsec_token = self._first_query_value(redirect_query, "xsec_token")
                xsec_source = self._first_query_value(redirect_query, "xsec_source") or xsec_source
        return note_id, xsec_token, xsec_source, final_url

    def _expand_xhs_url_sync(self, url: str) -> str:
        req = urllib.request.Request(url, headers=self._xhs_headers(), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.geturl() or url
        except urllib.error.HTTPError as exc:
            return exc.geturl() or exc.headers.get("Location") or url

    def _extract_xhs_note_id(self, value: str) -> str:
        for pattern in (
            r"noteId=([0-9a-zA-Z]+)",
            r"/(?:explore|discovery/item)/([0-9a-zA-Z]+)",
            r"/item/([0-9a-zA-Z]+)",
        ):
            match = re.search(pattern, value or "")
            if match:
                return match.group(1)
        return ""

    def _first_query_value(self, query: dict[str, list[str]], key: str) -> str:
        values = query.get(key) or []
        return values[0] if values else ""

    def _xhs_headers(self) -> dict[str, str]:
        accept = (
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,"
            "image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        )
        ua = (
            "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/55.0.2883.87 UBrowser/6.2.4098.3 Safari/537.36"
        )
        return {
            "Accept": accept,
            "Cookie": self.xiaohongshu_cookie,
            "User-Agent": ua,
            "Referer": "https://www.xiaohongshu.com/",
        }

    def _extract_xhs_initial_state(self, html_text: str) -> dict[str, Any]:
        match = re.search(r"window\.__INITIAL_STATE__\s*=\s*(.*?)</script>", html_text, re.I | re.S)
        if not match:
            match = re.search(r"__INITIAL_STATE__\s*[=:]\s*({.*?})\s*(?:;|</script>)", html_text, re.I | re.S)
        if not match:
            raise ValueError("未找到 window.__INITIAL_STATE__")
        raw = html.unescape(match.group(1)).strip().rstrip(";").replace("undefined", "null")
        return json.loads(raw)

    def _extract_xhs_note_from_html(self, html_text: str, note_id: str) -> dict[str, Any]:
        state = self._extract_xhs_initial_state(html_text)
        note_map = (state.get("note") or {}).get("noteDetailMap") or {}
        note = ((note_map.get(note_id) or {}).get("note") or {}) if isinstance(note_map, dict) else {}
        if note:
            return note
        for value in note_map.values() if isinstance(note_map, dict) else []:
            if isinstance(value, dict) and isinstance(value.get("note"), dict):
                return value.get("note") or {}
        note = self._find_xhs_note_in_state(state, note_id)
        if note:
            return note
        return {}

    def _find_xhs_note_in_state(self, value: Any, note_id: str) -> dict[str, Any]:
        stack = [value]
        seen: set[int] = set()
        while stack:
            current = stack.pop()
            if id(current) in seen:
                continue
            seen.add(id(current))
            if isinstance(current, dict):
                nested_note = current.get("note")
                if isinstance(nested_note, dict) and self._looks_like_xhs_note(nested_note, note_id):
                    return nested_note
                if self._looks_like_xhs_note(current, note_id):
                    return current
                stack.extend(current.values())
            elif isinstance(current, list):
                stack.extend(current)
        return {}

    def _looks_like_xhs_note(self, value: dict[str, Any], note_id: str) -> bool:
        if not isinstance(value, dict):
            return False
        ids = {str(value.get(key) or "") for key in ("id", "noteId", "note_id")}
        if note_id and note_id in ids:
            return True
        return bool(
            (value.get("imageList") or value.get("images"))
            and (value.get("title") is not None or value.get("desc") is not None or value.get("video"))
        )

    def _format_xhs_fallback(self, html_text: str, source_url: str, original_msg: str = "") -> ROutput | None:
        meta = self._extract_meta(html_text or "") if html_text else {}
        title = (
            meta.get("og:title")
            or meta.get("twitter:title")
            or meta.get("title")
            or self._extract_xml_text(original_msg, "title")
            or "未命名笔记"
        )
        desc = (
            meta.get("og:description")
            or meta.get("description")
            or meta.get("twitter:description")
            or self._extract_xml_text(original_msg, "des")
            or ""
        )
        image = meta.get("og:image") or meta.get("twitter:image") or ""
        video = meta.get("og:video") or meta.get("og:video:url") or meta.get("twitter:player:stream") or ""
        image = self._normalize_xhs_media_url(image)
        video = self._normalize_xhs_media_url(video)
        if not any([title and title != "未命名笔记", desc, image.startswith("http"), video.startswith("http")]):
            return None
        text = f"✅ 识别：小红书，{truncate(strip_html(title), 120)}"
        if desc:
            text += f"\n{truncate(strip_html(desc), 300)}"
        text += f"\n链接：{source_url}"
        if not video.startswith("http"):
            text += "\n未在页面中找到无水印视频直链，已使用卡片/页面信息兜底。"
        else:
            text += "\n已提取页面视频字段。"
        return ROutput(
            text=text,
            images=[image] if image.startswith("http") else [],
            videos=[video] if video.startswith("http") else [],
        )

    def _extract_xml_text(self, text: str, tag: str) -> str:
        match = re.search(rf"<{re.escape(tag)}>\s*(.*?)\s*</{re.escape(tag)}>", text or "", re.I | re.S)
        return html.unescape(strip_html(match.group(1))).strip() if match else ""

    def _format_xhs_note(self, note: dict[str, Any], source_url: str) -> ROutput:
        title = str(note.get("title") or "未命名笔记")
        desc = str(note.get("desc") or "")
        note_type = str(note.get("type") or "")
        images = [
            self._normalize_xhs_media_url(self._xhs_image_url(item))
            for item in note.get("imageList") or note.get("images") or []
            if isinstance(item, dict)
        ]
        images = [item for item in images if item.startswith("http")]
        text = f"✅ 识别：小红书，{truncate(title, 120)}"
        if desc:
            text += f"\n{truncate(desc, 300)}"
        text += f"\n链接：{source_url}"
        video_url = self._xhs_video_url(note)
        if note_type == "video" or video_url:
            cover = images[:1]
            if video_url:
                text += "\n已提取视频直链。"
            return ROutput(text=text, images=cover, videos=[video_url] if video_url.startswith("http") else [])
        return ROutput(text=text, images=images)

    def _xhs_image_url(self, item: dict[str, Any]) -> str:
        return str(
            item.get("urlDefault")
            or item.get("url_default")
            or item.get("urlPre")
            or item.get("url")
            or item.get("src")
            or ""
        )

    def _xhs_video_url(self, note: dict[str, Any]) -> str:
        stream = ((note.get("video") or {}).get("media") or {}).get("stream") or {}
        candidates: list[str] = []
        for key in ("h264", "h265", "av1"):
            for item in stream.get(key) or []:
                if not isinstance(item, dict):
                    continue
                candidates.extend(
                    [
                        item.get("masterUrl") or "",
                        item.get("master_url") or "",
                        item.get("url") or "",
                    ]
                )
                candidates.extend(item.get("backupUrls") or item.get("backup_urls") or [])
        origin_key = ((note.get("video") or {}).get("consumer") or {}).get("originVideoKey") or ""
        if origin_key:
            candidates.append("http://sns-video-bd.xhscdn.com/" + str(origin_key).lstrip("/"))
        for candidate in candidates:
            url = self._normalize_xhs_media_url(str(candidate or ""))
            if url.startswith("http"):
                return url
        return ""

    def _normalize_xhs_media_url(self, value: str) -> str:
        value = html.unescape(str(value or ""))
        if value.startswith("//"):
            return "https:" + value
        return value

    async def resolve_miyoushe(self, msg: str) -> ROutput:
        return await self.resolve_opengraph("miyoushe", msg)

    async def resolve_aircraft(self, msg: str) -> ROutput:
        return await self.resolve_opengraph("aircraft", msg)

    async def resolve_bodian(self, msg: str) -> ROutput:
        return await self.resolve_opengraph("bodian", msg)

    async def resolve_freyr(self, msg: str) -> ROutput:
        return await self.resolve_opengraph("freyr", msg)

    async def resolve_qq_music(self, msg: str) -> ROutput:
        return await self.resolve_opengraph("qq_music", msg)

    async def resolve_qishui(self, msg: str) -> ROutput:
        return await self.resolve_generic("qishui", msg)

    async def resolve_summary(self, msg: str) -> ROutput:
        url = first_url(msg)
        if not url:
            return ROutput(text="请提供要总结的网页 URL，例如：#总结一下 https://example.com")
        try:
            html_text = await request_text(url, timeout=20)
        except Exception as exc:
            return ROutput(text=f"网页读取失败：{exc}")
        meta = self._extract_meta(html_text)
        title = meta.get("og:title") or meta.get("title") or url
        text = strip_html(re.sub(r"<script.*?</script>|<style.*?</style>", "", html_text, flags=re.I | re.S))
        compact = re.sub(r"\s+", " ", text).strip()
        return ROutput(text=f"标题: {title}\n\n摘要: {truncate(compact, 1200)}")
