import asyncio
import socket
import sys
from pathlib import Path

# Bound every low-level socket in this test so a sandbox without outbound
# network cannot hang on urllib/DNS internals.
socket.setdefaulttimeout(5)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.media_downloader import YtDlpService
from services.resolver import ResolverService


def _network_available(timeout: float = 4.0) -> bool:
    # Pure TCP connect, fully governed by socket timeout: no DNS/HTTP internals
    # that could bypass the budget in a no-route sandbox.
    socket.setdefaulttimeout(timeout)
    try:
        with socket.create_connection(("1.1.1.1", 443), timeout=timeout):
            pass
        return True
    except Exception:
        return False
    finally:
        socket.setdefaulttimeout(5)


NETWORK = _network_available()


async def main():
    temp = ROOT / "data" / "test_media"
    ytdlp = YtDlpService(temp, mode="metadata")
    ok, backend = ytdlp.available()
    assert ok, "yt-dlp backend not available after installing requirements"
    assert backend in {"python-package"} or backend

    if not NETWORK:
        # No outbound network: skip ffixture-requiring API/social assertions; the
        # offline-safe local formatting branches below still run.
        print("NETWORK_UNAVAILABLE: skipping network-backed resolver assertions")
    else:
        # OpenGraph extraction should work without a social-account cookie.
        resolver = ResolverService(temp_dir=temp, ytdlp_mode="metadata")
        og = await resolver.resolve_opengraph("general", "https://example.com")
        assert "Example Domain" in og.text or "example.com" in og.text

        # Public YouTube test video metadata path; tolerate network/extractor
        # failure but wrap in a hard timeout so a degraded/no-route sandbox cannot
        # hang the whole test in yt-dlp's internal retry loop.
        async def _youtube_probe():
            r = ResolverService(temp_dir=temp, ytdlp_mode="metadata")
            return await r.resolve("youtube", "https://www.youtube.com/watch?v=BaW_jenozKc")

        try:
            out = await asyncio.wait_for(_youtube_probe(), timeout=40)
            assert out.text and ("YouTube" in out.text or "yt-dlp" in out.text)
        except asyncio.TimeoutError:
            print("TIMEOUT: youtube yt-dlp probe skipped (no stable outbound network)")

    direct_ytdlp = YtDlpService(temp, mode="direct")
    direct = await direct_ytdlp._output_from_info(
        {
            "title": "Local direct media fixture",
            "uploader": "fixture",
            "duration": 10,
            "webpage_url": "https://example.com/video",
            "url": "https://example.com/video.mp4",
            "filesize": 1024 * 1024,
        },
        platform="通用直链视频",
        original_url="https://example.com/video",
    )
    assert direct.videos == ["https://example.com/video.mp4"], direct.text

    off = await YtDlpService(temp, mode="off").extract("https://example.com/video.mp4", platform="通用直链视频")
    assert "已在配置中关闭" in off.text and not off.videos

    douyin = ResolverService(temp_dir=temp, ytdlp_mode="metadata", douyin_cookie="a=b")
    douyin_url = "https://www.douyin.com/jingxuan?modal_id=7651544681980906803"
    assert douyin._extract_douyin_id(douyin_url) == "7651544681980906803"
    douyin_item = {
        "desc": "抖音测试简介",
        "aweme_type": 4,
        "author": {"nickname": "抖音作者"},
        "video": {
            "duration": 12000,
            "cover": {"url_list": ["https://img.example/cover.jpg"]},
            "play_addr": {"uri": "video-uri-123", "url_list": ["https://video.example/fallback.mp4"]},
        },
        "music": {"play_url": {"url_list": ["https://audio.example/bgm.mp3"]}},
    }
    douyin_out = douyin._format_douyin_item(douyin_item, douyin_url)
    assert "抖音作者" in douyin_out.text
    assert douyin_out.images == ["https://img.example/cover.jpg"]
    assert douyin_out.videos == ["https://aweme.snssdk.com/aweme/v1/play/?video_id=video-uri-123&ratio=1080p&line=0"]
    assert douyin_out.audios == []

    async def fake_douyin_extract(url, platform=""):
        return type(douyin_out)(text="✅ 识别：抖音\n只有封面", images=["https://img.example/cover.jpg"])

    async def fake_douyin_json(url, headers=None, timeout=15):
        return {"aweme_detail": douyin_item}

    douyin.media.extract = fake_douyin_extract
    import services.resolver as resolver_module

    original_request_json = resolver_module.request_json
    resolver_module.request_json = fake_douyin_json
    try:
        resolved_douyin = await douyin.resolve_douyin(douyin_url)
    finally:
        resolver_module.request_json = original_request_json
    assert resolved_douyin.videos == [
        "https://aweme.snssdk.com/aweme/v1/play/?video_id=video-uri-123&ratio=1080p&line=0"
    ]

    short_douyin = ResolverService(temp_dir=temp, ytdlp_mode="metadata", douyin_cookie="sessionid=x")
    short_douyin._expand_douyin_url = lambda url: asyncio.sleep(
        0, result=("https://www.douyin.com/video/7651544681980906803", "short-ttwid")
    )
    extracted_candidates = []

    async def fake_short_extract(url, platform=""):
        extracted_candidates.append(url)
        return type(douyin_out)(text="✅ 识别：抖音\n只有封面", images=["https://img.example/cover.jpg"])

    seen_headers = []

    async def fake_short_json(url, headers=None, timeout=15):
        seen_headers.append(headers or {})
        assert "aweme_id=7651544681980906803" in url
        return {"aweme_detail": douyin_item}

    short_douyin.media.extract = fake_short_extract
    resolver_module.request_json = fake_short_json
    try:
        short_result = await short_douyin.resolve_douyin("https://v.douyin.com/maji1B2XpUM/")
    finally:
        resolver_module.request_json = original_request_json
    assert "https://www.douyin.com/video/7651544681980906803" in extracted_candidates
    assert short_result.videos == ["https://aweme.snssdk.com/aweme/v1/play/?video_id=video-uri-123&ratio=1080p&line=0"]
    assert any("ttwid=short-ttwid" in item.get("Cookie", "") for item in seen_headers)

    xhs_without_cookie = ResolverService(temp_dir=temp, ytdlp_mode="metadata")
    missing = await xhs_without_cookie.resolve_xhs(
        "https://www.xiaohongshu.com/explore/abc123?xsec_token=token123&xsec_source=pc_feed"
    )
    assert "Cookie" in missing.text and "xsec_token" not in missing.text.split("解析缺少必要信息：")[-1].split("\n")[0]

    xhs = ResolverService(temp_dir=temp, ytdlp_mode="metadata", xiaohongshu_cookie="a=b")
    note = {
        "title": "小红书测试标题",
        "desc": "小红书测试简介",
        "type": "normal",
        "imageList": [
            {"urlDefault": "//sns-img.example.com/1.jpg"},
            {"urlDefault": "https://sns-img.example.com/2.jpg"},
        ],
    }
    formatted = xhs._format_xhs_note(note, "https://www.xiaohongshu.com/explore/abc123")
    assert "小红书测试标题" in formatted.text
    assert formatted.images == ["https://sns-img.example.com/1.jpg", "https://sns-img.example.com/2.jpg"]

    html_state = '<script>window.__INITIAL_STATE__={"note":{"noteDetailMap":{"abc123":{"note":{"title":"T","desc":"D","type":"video","imageList":[{"urlDefault":"https://i.example/cover.jpg"}],"video":{"media":{"stream":{"h264":[{"masterUrl":"https://v.example/a.mp4"}]}}}}}}}}</script>'
    state = xhs._extract_xhs_initial_state(html_state)
    video_note = state["note"]["noteDetailMap"]["abc123"]["note"]
    video = xhs._format_xhs_note(video_note, "https://www.xiaohongshu.com/explore/abc123")
    assert video.images == ["https://i.example/cover.jpg"]
    assert video.videos == ["https://v.example/a.mp4"]

    nested_state = {
        "loaderData": {
            "note": {
                "noteId": "abc123",
                "title": "Nested T",
                "desc": "Nested D",
                "type": "video",
                "imageList": [{"url": "//sns-img.example.com/nested.jpg"}],
                "video": {"media": {"stream": {"h264": [{"backupUrls": ["https://v.example/backup.mp4"]}]}}},
            }
        }
    }
    nested_note = xhs._find_xhs_note_in_state(nested_state, "abc123")
    nested_video = xhs._format_xhs_note(nested_note, "https://www.xiaohongshu.com/explore/abc123")
    assert nested_video.images == ["https://sns-img.example.com/nested.jpg"]
    assert nested_video.videos == ["https://v.example/backup.mp4"]

    xhs_card_msg = """<?xml version="1.0"?>
<msg><appmsg>
<title>我听见你心中那动人的天籁搜</title>
<des>我听见你心中那动人的天籁搜</des>
<url>https://www.xiaohongshu.com/discovery/item/6a2981430000000008024a58?app_platform=harmony&amp;app_version=9.33.4&amp;share_from_user_hidden=true&amp;xsec_source=app_share&amp;type=normal&amp;xsec_token=CBx8SBh30U51DJphYbz5dzefmcjw6Mr-Yc1BLSfUZpAOw=&amp;author_share=1&amp;&amp;apptime=1781399319&amp;share_id=e5f9419d99b443828cdc66870f2f3cf7&amp;xhsshare=WeixinSession</url>
</appmsg></msg>"""
    card_url = xhs._extract_xhs_url(xhs_card_msg)
    assert card_url.startswith("https://www.xiaohongshu.com/discovery/item/6a2981430000000008024a58?")
    assert "&amp;" not in card_url and "</url" not in card_url
    note_id, token, source, final_url = await xhs._parse_xhs_note_params(card_url)
    assert note_id == "6a2981430000000008024a58"
    assert token == "CBx8SBh30U51DJphYbz5dzefmcjw6Mr-Yc1BLSfUZpAOw="
    assert source == "app_share"

    fallback_html = """<html><head>
<title>小红书卡片标题</title>
<meta property="og:title" content="小红书页面标题">
<meta property="og:description" content="小红书页面简介">
<meta property="og:image" content="//sns-img.example.com/card.jpg">
</head><body>no initial state</body></html>"""
    fallback = xhs._format_xhs_fallback(fallback_html, final_url, xhs_card_msg)
    assert fallback is not None
    assert "小红书页面标题" in fallback.text
    assert fallback.images == ["https://sns-img.example.com/card.jpg"]
    xml_fallback = xhs._format_xhs_fallback("", final_url, xhs_card_msg)
    assert xml_fallback is not None
    assert "我听见你心中那动人的天籁搜" in xml_fallback.text

    print("media resolver tests ok")
    print("backend=", backend)
    if NETWORK and "out" in locals():
        youtube_head = out.text.split("\n")[0].encode("gbk", errors="replace").decode("gbk")
        print("youtube_result_head=", youtube_head)


if __name__ == "__main__":
    asyncio.run(main())
