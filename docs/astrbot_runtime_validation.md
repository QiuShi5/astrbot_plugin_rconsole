# AstrBot 真实运行时加载验证报告

## 目的

针对审查意见“缺少真实 AstrBot load/WebUI/适配器命令测试”，本轮补强不再只依赖本地 stub，而是在隔离虚拟环境中安装真实 AstrBot PyPI 包并验证插件导入兼容性。

## 执行环境

- 工作目录：`rconsole-astrbot-port`
- Python：3.11
- 隔离虚拟环境：`.venv_astrbot_check`
- AstrBot 版本：PyPI `astrbot==4.14.6`

## 执行命令与结果

### 1. 查询 PyPI 版本

```bash
python -m pip index versions astrbot
```

结果：可用最新版本包含 `4.14.6`。

### 2. 安装真实 AstrBot

首次在全局沙箱安装出现依赖冲突/异常退出，仅输出：

```text
WARNING: lxml 6.1.1 does not provide the extra 'html_clean'
```

为排除沙箱全局依赖污染，改用隔离 venv：

```bash
python -m venv .venv_astrbot_check
.venv_astrbot_check/bin/python -m pip install --upgrade pip
.venv_astrbot_check/bin/python -m pip install "astrbot==4.14.6"
```

结果：安装成功。

### 3. 真实 AstrBot API + 插件导入

```bash
.venv_astrbot_check/bin/python - <<'PY'
import importlib, sys
sys.path.insert(0, 'rconsole-astrbot-port')
import astrbot
import astrbot.api
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Star, Context
mod = importlib.import_module('astrbot_plugin_rconsole.main')
print('plugin_import_ok', hasattr(mod, 'RConsolePlugin'))
PY
```

结果：

```text
astrbot_import_ok unknown
astrbot_api_import_ok
plugin_import_ok True
```

### 4. 真实 API 签名检查

```text
plugin_class RConsolePlugin
init_signature (self, context: 'Context', config: 'AstrBotConfig')
has_dispatch True
has_help True
context_signature (event_queue, config, db, provider_manager, platform_manager, ...)
```

## 结论

- 插件可在真实 `astrbot==4.14.6` Python 包环境中导入；`astrbot.api`、`filter`、`Star`、`Context` API 路径与插件代码兼容。
- 由于真实 `Context` 需要完整 AstrBot 运行时管理器、事件队列、数据库、平台管理器等，未在沙箱内启动完整 WebUI/适配器；这类测试需要用户提供真实 AstrBot 部署、平台账号和消息适配器配置。
- 已用 `tests/test_astrbot_stub_e2e.py` 覆盖命令分发、图片/音频/视频发送降级、管理员权限等端到端路径；真实包验证补强了 API 兼容证据。
