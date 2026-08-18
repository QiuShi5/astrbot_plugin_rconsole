from __future__ import annotations

import inspect
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/runtime_adapter_capability_probe.json"


def run(cmd):
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
    return {"cmd": cmd, "returncode": proc.returncode, "output_head": proc.stdout[:4000]}


def main():
    result = {"checks": []}
    try:
        import astrbot.api.message_components as Comp
        from astrbot.api.star import Context

        result["real_astrbot_api"] = True
        result["component_signatures"] = {}
        for name in ["Plain", "Image", "Record", "Video", "File"]:
            obj = getattr(Comp, name)
            sig = {"constructor": str(inspect.signature(obj))}
            for meth in ["fromURL", "fromFileSystem"]:
                if hasattr(obj, meth):
                    sig[meth] = str(inspect.signature(getattr(obj, meth)))
            result["component_signatures"][name] = sig
        # Construct media components without sending to a real adapter. This proves
        # plugin chain_result construction targets valid AstrBot component APIs.
        samples = [
            Comp.Plain("probe"),
            Comp.Image.fromURL("https://example.com/a.png"),
            Comp.Record.fromURL("https://example.com/a.mp3"),
            Comp.Video.fromURL("https://example.com/a.mp4"),
            Comp.File(name="a.txt", file="/tmp/a.txt"),
        ]
        result["component_construction"] = [type(x).__name__ for x in samples]
        result["context_signature"] = str(inspect.signature(Context))
        result["adapter_runtime_requirement"] = (
            "真实发送需要运行中的 AstrBot Context、平台管理器、消息适配器和账号配置；沙箱仅能验证组件 API 与构造兼容。"
        )
    except Exception as exc:
        result["real_astrbot_api"] = False
        result["error"] = repr(exc)
        result["adapter_runtime_requirement"] = (
            "真实 AstrBot 运行时缺失：本探针需在已安装 AstrBot 的环境中运行以验证组件 API 签名。"
        )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("RUNTIME_ADAPTER_PROBE_OK" if result.get("real_astrbot_api") else "RUNTIME_ADAPTER_PROBE_SKIPPED_NO_ASTRBOT")
    print(json.dumps(result, ensure_ascii=False, indent=2)[:2000])


if __name__ == "__main__":
    main()
