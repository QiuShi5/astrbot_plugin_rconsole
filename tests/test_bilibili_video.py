import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services import resolver as resolver_module
from services.bilibili_video import BilibiliVideoService
from services.resolver import ResolverService
from services.common import ROutput


async def main():
    temp = ROOT / 'data' / 'test_bili_video'
    svc = BilibiliVideoService(temp, max_filesize_mb=5)

    def fake_request(*, bvid, cid, page_url, qn='64'):
        assert bvid == 'BV1xx411c7mD'
        assert str(cid) == '123'
        return {'code': 0, 'data': {'durl': [{'url': 'https://example.com/video.mp4', 'size': 1024}]}}

    def fake_download(url, *, page_url, stem, limit_mb):
        p = temp / 'mock.mp4'
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b'mp4')
        return str(p)

    svc._request_playurl = fake_request
    svc._download_video = fake_download
    out = await svc.extract_video(bvid='BV1xx411c7mD', cid='123', title='demo')
    assert out.videos and out.videos[0].endswith('.mp4')
    assert '已获取并下载' in out.text

    resolver = ResolverService(temp_dir=temp, ytdlp_mode='off')
    resolver.media.extract = lambda url, platform='': asyncio.sleep(0, result=ROutput(text='yt-dlp 解析链已在配置中关闭。'))
    resolver.bili_video.extract_video = lambda **kwargs: asyncio.sleep(0, result=ROutput(text='native ok', videos=[str(temp / 'native.mp4')]))

    async def fake_json(url, timeout=15, headers=None):
        return {'code': 0, 'data': {'title': 'demo title', 'owner': {'name': 'up'}, 'desc': 'desc', 'pic': 'https://example.com/p.jpg', 'cid': 123, 'stat': {'view': 10000, 'like': 2, 'coin': 3, 'favorite': 4, 'share': 5, 'danmaku': 6, 'reply': 7}}}

    original_request_json = resolver_module.request_json
    resolver_module.request_json = fake_json
    try:
        out = await resolver.resolve_bili('https://www.bilibili.com/video/BV1xx411c7mD')
    finally:
        resolver_module.request_json = original_request_json
    assert out.videos and out.videos[0].endswith('native.mp4')
    assert 'native ok' not in out.text
    assert '已获取并下载 B站视频' not in out.text
    assert out.text.startswith('✅ 识别：哔哩哔哩，demo title')
    assert '点赞：2 | 硬币：3 | 收藏：4 | 分享：5 | 总播放量：1.0万 | 弹幕数量：6 | 评论：7' in out.text
    assert '📝 简介：desc' in out.text
    assert '短链已展开' not in out.text
    assert 'BVID：' not in out.text
    assert 'UP：' not in out.text
    assert '链接：' not in out.text

    resolver = ResolverService(temp_dir=temp, ytdlp_mode='direct')
    expanded = 'https://www.bilibili.com/video/BV1HsovBGETx?p=1'
    resolver._expand_bili_url = lambda url: asyncio.sleep(0, result=expanded)
    seen = {}

    async def fake_media_extract(url, platform=''):
        seen['media_url'] = url
        return ROutput(text='✅ 识别：哔哩哔哩\n链接：https://b23.tv/vQMt0c5\nyt-dlp 解析失败：HTTP Error 412')

    async def fake_native(**kwargs):
        seen['native_kwargs'] = kwargs
        return ROutput(text='native fallback ok', videos=[str(temp / 'short_native.mp4')])

    resolver.media.extract = fake_media_extract
    resolver.bili_video.extract_video = fake_native

    async def fake_short_json(url, timeout=15, headers=None):
        assert 'BV1HsovBGETx' in url
        assert headers and 'Referer' in headers
        return {'code': 0, 'data': {'title': 'short title', 'owner': {'name': 'short up'}, 'desc': 'short desc', 'pic': '', 'cid': 456, 'stat': {'view': 3, 'like': 4, 'coin': 5, 'favorite': 6, 'share': 7, 'danmaku': 8, 'reply': 9}}}

    resolver_module.request_json = fake_short_json
    try:
        out = await resolver.resolve_bili('【安保系统瘫痪啦-哔哩哔哩】 https://b23.tv/vQMt0c5')
    finally:
        resolver_module.request_json = original_request_json
    assert out.videos and out.videos[0].endswith('short_native.mp4')
    assert 'native fallback ok' not in out.text
    assert '已获取并下载 B站视频' not in out.text
    assert '短链已展开' not in out.text
    assert expanded not in out.text
    assert 'https://b23.tv/vQMt0c5' not in out.text
    assert out.text.startswith('✅ 识别：哔哩哔哩，short title')
    assert '点赞：4 | 硬币：5 | 收藏：6 | 分享：7 | 总播放量：3 | 弹幕数量：8 | 评论：9' in out.text
    assert '📝 简介：short desc' in out.text
    assert 'BVID：' not in out.text
    assert 'UP：' not in out.text
    assert 'yt-dlp 解析失败' not in out.text
    assert seen['media_url'] == expanded
    assert seen['native_kwargs']['bvid'] == 'BV1HsovBGETx'
    assert seen['native_kwargs']['cid'] == 456
    print('bilibili video tests ok')


if __name__ == '__main__':
    asyncio.run(main())
