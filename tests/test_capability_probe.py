import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.capabilities import CapabilityService


class Msg:
    platform_name = "aiocqhttp-probe"


class Event:
    message_obj = Msg()


def main():
    cfg = {
        "bilibili": {"sessdata": "dummy"},
        "netease": {"cookie": "", "cloud_cookie": "", "cloud_api_server": ""},
    }
    out = CapabilityService(cfg).probe(Event())
    text = out.text
    assert "R插件 AstrBot版能力诊断" in text
    assert "AstrBot 富媒体组件" in text
    assert "B站 SESSDATA" in text
    assert "网易云云盘 Cookie" in text
    assert "当前适配器" in text
    print("capability probe tests ok")


if __name__ == "__main__":
    main()
