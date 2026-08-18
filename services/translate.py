"""Translation service compatible with R-plugin's 翻中/英/日/文/俄/韩 commands."""

from __future__ import annotations

import urllib.parse

from .common import ROutput, request_json

LANG_MAP = {"中": "zh-CN", "英": "en", "日": "ja", "韩": "ko", "俄": "ru", "文": "zh-CN"}


class TranslateService:
    async def translate(self, msg: str) -> ROutput:
        msg = msg.strip()
        if msg.startswith("trans"):
            lang_key = msg[5:6]
            text = msg[6:].strip()
        else:
            lang_key = msg[1:2]
            text = msg[2:].strip()
        if lang_key not in LANG_MAP:
            return ROutput(text="输入格式有误或暂不支持该语言！\n例子：翻中 China's policy has been consistent")
        if not text:
            return ROutput(text="请输入要翻译的文本，或回复一条消息后使用翻中/英/日/韩/俄。")
        target = LANG_MAP[lang_key]
        # Public fallback endpoint. R-plugin used a custom Translate strategy; this
        # port keeps the same user-facing command.
        url = "https://api.mymemory.translated.net/get?" + urllib.parse.urlencode(
            {"q": text, "langpair": f"auto|{target}"}
        )
        try:
            data = await request_json(url, timeout=20)
            translated = ((data or {}).get("responseData") or {}).get("translatedText")
            if not translated:
                matches = data.get("matches", []) if isinstance(data, dict) else []
                translated = matches[0].get("translation") if matches else ""
        except Exception as exc:
            return ROutput(text=f"翻译失败：{exc}")
        return ROutput(text=(translated or "翻译失败：未返回结果").strip())
