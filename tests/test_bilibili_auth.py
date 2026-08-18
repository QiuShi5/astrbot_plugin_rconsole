import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.bilibili_auth import BilibiliAuthService


async def main():
    data_dir = ROOT / "data" / "test_bili_auth"
    svc = BilibiliAuthService(data_dir)

    def fake_generate(url):
        assert "qrcode/generate" in url
        return {
            "code": 0,
            "data": {
                "url": "https://passport.bilibili.com/h5-app/passport/login/scan?navhide=1&qrcode_key=test-key",
                "qrcode_key": "test-key",
            },
        }

    svc._request_json = fake_generate
    out = await svc.start_qr_login()
    assert "B站扫码登录已生成" in out.text
    assert out.images and Path(out.images[0]).exists()

    def fake_poll(key):
        assert key == "test-key"
        return {"code": 0, "data": {"code": 86101, "message": "未扫码"}}, {}

    svc._poll_with_cookies = fake_poll
    out = await svc.poll_status()
    assert "未扫码" in out.text

    def fake_success(key):
        return {"code": 0, "data": {"code": 0, "message": "OK"}}, {"SESSDATA": "abc", "bili_jct": "csrf"}

    svc._poll_with_cookies = fake_success
    out = await svc.poll_status()
    assert "登录成功" in out.text and "SESSDATA" in out.text

    out = await svc.configured_status("configured")
    assert "已在插件配置中检测到" in out.text
    print("bilibili auth tests ok")


if __name__ == "__main__":
    asyncio.run(main())
