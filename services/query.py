"""Query functions ported from apps/query.js."""

from __future__ import annotations

import urllib.parse

from .common import ROutput, request_json, strip_html


class QueryService:
    async def doctor(self, keyword: str) -> ROutput:
        keyword = keyword.strip()
        if not keyword:
            return ROutput(text="请输入要查询的疾病/症状/医院/医生/药品，例如：#医药查询 感冒")
        url = "https://server.dayi.org.cn/api/search?" + urllib.parse.urlencode(
            {"keyword": keyword, "pageNo": 1, "pageSize": 10}
        )
        try:
            data = await request_json(url, timeout=18)
            rows = data.get("list", []) if isinstance(data, dict) else []
        except Exception as exc:
            return ROutput(text=f"医药查询失败，请稍后重试：{exc}")
        if not rows:
            return ROutput(text="未找到相关医药信息")
        forward = []
        for item in rows[:10]:
            title = strip_html(item.get("title"))
            second = strip_html(item.get("secondTitle"))
            intro = strip_html(item.get("introduction"))
            forward.append(f"📌 {title} - {second}\n\n📝 简介：{intro}")
        return ROutput(text="医药查询结果：", forward_texts=forward)

    async def cat(self) -> ROutput:
        images: list[str] = []
        errors: list[str] = []
        for url, parser in [
            ("https://shibe.online/api/cats?count=10", lambda data: data if isinstance(data, list) else []),
            ("https://api.thecatapi.com/v1/images/search?limit=10", lambda data: [x.get("url") for x in data if isinstance(x, dict) and x.get("url")]),
        ]:
            try:
                images.extend(parser(await request_json(url, timeout=18)))
            except Exception as exc:
                errors.append(str(exc))
        if not images:
            return ROutput(text="获取猫图失败，请稍后重试" + (f"：{errors[0]}" if errors else ""))
        return ROutput(text="涩图也不看了,就看猫是吧", images=images[:20])

    async def software_recommended(self) -> ROutput:
        urls = [
            "https://www.ghxi.com/ghapi?type=query&n=pc",
            "https://www.ghxi.com/ghapi?type=query&n=and",
        ]
        forward: list[str] = []
        for url in urls:
            try:
                data = await request_json(url, timeout=18)
                rows = (((data or {}).get("data") or {}).get("list") or []) if isinstance(data, dict) else []
                for item in rows[:20]:
                    title = item.get("title", "")
                    link = item.get("url", "")
                    forward.append(f"推荐软件：{title}\n地址：{link}\n")
            except Exception as exc:
                forward.append(f"推荐软件接口请求失败：{exc}")
        if not forward:
            return ROutput(text="暂无推荐软件数据")
        return ROutput(text="推荐软件：", forward_texts=forward[:40])

    async def buyer_show(self) -> ROutput:
        try:
            data = await request_json("https://api.suyanw.cn/api/tbmjx.php?return=json", timeout=18)
            img = data.get("imgurl") if isinstance(data, dict) else ""
        except Exception as exc:
            return ROutput(text=f"获取买家秀失败，请稍后重试：{exc}")
        if not img:
            return ROutput(text="获取买家秀失败")
        return ROutput(images=[img])

    async def cospro(self) -> ROutput:
        images: list[str] = []
        for url in ["https://imgapi.cn/cos2.php?return=jsonpro", "https://imgapi.cn/cos.php?return=jsonpro"]:
            try:
                data = await request_json(url, timeout=18)
                images.extend(data.get("imgurls", []) if isinstance(data, dict) else [])
            except Exception:
                continue
        if not images:
            return ROutput(text="获取图片失败，请稍后重试")
        return ROutput(text="哪天克火掉一定是在这个群里面...", images=images[:30])
