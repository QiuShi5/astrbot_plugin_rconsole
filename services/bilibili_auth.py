"""Bilibili QR login helpers for #rbq/#rbs."""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any

from .common import ROutput, read_json, safe_filename, write_json

GENERATE_API = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
POLL_API = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"


class BilibiliAuthService:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.auth_path = self.data_dir / "bilibili_auth.json"
        self.qr_dir = self.data_dir / "rendered"
        self.qr_dir.mkdir(parents=True, exist_ok=True)

    async def start_qr_login(self) -> ROutput:
        try:
            data = self._request_json(GENERATE_API)
            payload = data.get("data") or {}
            login_url = payload.get("url") or ""
            key = payload.get("qrcode_key") or ""
            if not login_url or not key:
                return ROutput(text=f"B站扫码登录二维码获取失败：{data}")
        except Exception as exc:
            return ROutput(text=f"B站扫码登录二维码获取失败：{exc}")

        record = read_json(self.auth_path, {})
        if not isinstance(record, dict):
            record = {}
        record.update({"qrcode_key": key, "login_url": login_url, "created_at": int(time.time())})
        write_json(self.auth_path, record)

        image = self._make_qr(login_url, key)
        text = (
            "B站扫码登录已生成。\n"
            "请用哔哩哔哩 App 扫描二维码并确认登录；插件会自动查询并回调成功/失败/超时结果。\n"
            "也可以随时发送 #rbs 手动查看状态。\n"
            "二维码有效期较短；过期后请重新发送 #rbq。"
        )
        if image:
            return ROutput(text=text, images=[image])
        return ROutput(text=text + f"\n扫码链接：{login_url}")

    async def poll_status(self) -> ROutput:
        record = read_json(self.auth_path, {})
        key = record.get("qrcode_key") if isinstance(record, dict) else ""
        if not key:
            return ROutput(text="尚未生成 B站扫码登录二维码，请先发送 #rbq。")
        try:
            data, cookies = self._poll_with_cookies(str(key))
        except Exception as exc:
            return ROutput(text=f"B站扫码状态查询失败：{exc}")
        payload = data.get("data") or {}
        code = payload.get("code")
        message = payload.get("message") or data.get("message") or ""
        if code == 0:
            sessdata = cookies.get("SESSDATA", "")
            saved = read_json(self.auth_path, {})
            if not isinstance(saved, dict):
                saved = {}
            saved.update({"cookies": cookies, "sessdata": sessdata, "login_at": int(time.time()), "last_poll": payload})
            write_json(self.auth_path, saved)
            hint = "已保存到插件 data/bilibili_auth.json。"
            return ROutput(text=f"B站扫码登录成功。{hint}\nCookie 字段：{', '.join(cookies.keys()) or '未捕获到 Cookie'}")
        status_map = {
            86038: "二维码已失效，请重新发送 #rbq。",
            86090: "已扫码，等待在手机端确认。",
            86101: "未扫码，请继续扫码。",
        }
        return ROutput(text=f"B站扫码状态：{status_map.get(code, message or code)}")

    async def configured_status(self, configured_sessdata: str = "") -> ROutput:
        record = read_json(self.auth_path, {})
        saved = record.get("sessdata", "") if isinstance(record, dict) else ""
        if configured_sessdata:
            return ROutput(text="B站登录状态：已在插件配置中检测到 bilibili.sessdata。")
        if saved:
            return ROutput(text="B站登录状态：已通过 #rbq/#rbs 保存过 SESSDATA 到插件 data/bilibili_auth.json；建议同步到插件配置 bilibili.sessdata。")
        return ROutput(text="B站登录状态：未检测到 SESSDATA。发送 #rbq 生成二维码，扫码确认后发送 #rbs 查询状态。")

    def _request_json(self, url: str) -> dict[str, Any]:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 AstrBot-RConsole", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))

    def _poll_with_cookies(self, key: str) -> tuple[dict[str, Any], dict[str, str]]:
        jar = CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        url = POLL_API + "?" + urllib.parse.urlencode({"qrcode_key": key})
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 AstrBot-RConsole", "Accept": "application/json"})
        with opener.open(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        cookies = {cookie.name: cookie.value for cookie in jar}
        return data, cookies

    def _make_qr(self, login_url: str, key: str) -> str:
        try:
            import qrcode
        except Exception:
            return ""
        path = self.qr_dir / f"bili_qr_{safe_filename(key)}.png"
        qr = qrcode.QRCode(border=2, box_size=8)
        qr.add_data(login_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(path)
        return str(path)

