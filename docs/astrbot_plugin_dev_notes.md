# AstrBot 插件开发文档整理

> 整理时间基准：2026-06-09 09:24:30 +08:00 Asia/Shanghai  
> 目标：为将 `rconsole-plugin` 移植为 AstrBot 插件提供开发规范依据。  
> 注意：以下内容来自 AstrBot 官方开发文档及相关页面，网页内容仅作为外部资料摘要使用，具体 API 仍应以目标 AstrBot 版本实际源码/运行环境为准。

## 1. 插件项目结构

AstrBot 插件通常是一个独立目录，建议目录名：

- 以 `astrbot_plugin_` 开头；
- 全小写；
- 不含空格；
- 尽量简短且能表达用途。

开发/部署时常放在 AstrBot 本体目录：

```text
AstrBot/
  data/
    plugins/
      astrbot_plugin_xxx/
```

典型结构：

```text
astrbot_plugin_xxx/
  main.py                    # 必需：插件入口
  metadata.yaml              # 必需：插件元数据
  requirements.txt           # 可选：Python 依赖
  _conf_schema.json          # 可选：插件配置 schema
  logo.png                   # 可选：插件 Logo，建议 1:1，256x256
  skills/                    # 可选：随插件提供 Skills
  pages/                     # 可选：WebUI Dashboard 页面
  .astrbot-plugin/
    i18n/
      zh-CN.json             # 可选：国际化资源
      en-US.json
```

关键约束：

- 入口文件必须是 `main.py`。
- 插件类应继承 `Star`。
- Handler 应注册在插件类内部。
- 复杂业务可以拆到外部模块，但由插件类内 Handler 调用。
- 持久化数据不建议写入插件目录，应写到 AstrBot 数据目录，以免插件更新/重装覆盖。

## 2. `metadata.yaml` 元数据

AstrBot 通过 `metadata.yaml` 识别插件信息。常见字段：

```yaml
name: astrbot_plugin_xxx
version: v1.0.0
desc: 插件描述
author: 作者
repo: 仓库地址
```

推荐补充字段：

```yaml
display_name: 插件展示名
short_desc: 插件短描述
support_platforms:
  - aiocqhttp
  - telegram
astrbot_version: ">=4.16,<5"
```

说明：

- `display_name`：在插件市场/WebUI 展示。
- `short_desc`：插件市场卡片短描述，缺失时回退到 `desc`。
- `support_platforms`：声明支持的平台适配器。
- `astrbot_version`：声明兼容 AstrBot 版本范围，遵循 PEP 440，不加 `v` 前缀，例如 `>=4.17.0`、`>=4.16,<5`。

常见平台 key 包括：

```text
aiocqhttp, qq_official, qq_official_webhook, telegram, wecom,
wecom_ai_bot, lark, dingtalk, discord, slack, kook, vocechat,
weixin_official_account, weixin_oc, satori, misskey, line,
matrix, mattermost
```

移植 R 插件时，应根据原插件实际平台能力优先适配 `aiocqhttp` / OneBot 类平台，再为其他平台提供降级输出。

## 3. 插件类与生命周期

最小插件示例：

```python
from astrbot.api import logger
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star

class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.command("helloworld")
    async def helloworld(self, event: AstrMessageEvent):
        """hello world 指令"""
        user_name = event.get_sender_name()
        logger.info("触发 helloworld 指令")
        yield event.plain_result(f"Hello, {user_name}!")

    async def terminate(self):
        """插件卸载/停用时调用，可选。"""
```

有配置时可接收 `AstrBotConfig`：

```python
from astrbot.api import AstrBotConfig
from astrbot.api.star import Context, Star

class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
```

生命周期与实现要点：

- `__init__()` 中必须调用 `super().__init__(context)`。
- `terminate()` 可用于关闭资源、停止后台任务、保存状态。
- Handler 的前两个参数通常是 `self`、`event`。
- 日志建议使用 `from astrbot.api import logger`。

## 4. 命令、事件与过滤器

核心导入：

```python
from astrbot.api.event import filter, AstrMessageEvent
```

### 4.1 普通命令

```python
@filter.command("help")
async def help_cmd(self, event: AstrMessageEvent):
    yield event.plain_result("帮助内容")
```

用户发送：

```text
/help
```

### 4.2 参数解析

AstrBot 可按函数签名解析参数并进行类型转换：

```python
@filter.command("add")
async def add(self, event: AstrMessageEvent, a: int, b: int):
    yield event.plain_result(f"结果是: {a + b}")
```

调用：

```text
/add 1 2
```

### 4.3 指令组

```python
@filter.command_group("math")
def math():
    pass

@math.command("add")
async def add(self, event: AstrMessageEvent, a: int, b: int):
    yield event.plain_result(f"结果是: {a + b}")
```

调用：

```text
/math add 1 2
```

### 4.4 别名

```python
@filter.command("help", alias={"帮助", "菜单"})
async def help_cmd(self, event: AstrMessageEvent):
    yield event.plain_result("帮助内容")
```

### 4.5 消息类型过滤

```python
@filter.event_message_type(filter.EventMessageType.ALL)
async def on_all_message(self, event: AstrMessageEvent):
    pass

@filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
async def on_private(self, event: AstrMessageEvent):
    pass

@filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
async def on_group(self, event: AstrMessageEvent):
    pass
```

### 4.6 平台过滤

```python
@filter.platform_adapter_type(
    filter.PlatformAdapterType.AIOCQHTTP | filter.PlatformAdapterType.QQOFFICIAL
)
async def on_specific_platform(self, event: AstrMessageEvent):
    pass
```

### 4.7 权限过滤

```python
@filter.permission_type(filter.PermissionType.ADMIN)
@filter.command("admin")
async def admin_cmd(self, event: AstrMessageEvent):
    yield event.plain_result("管理员命令")
```

### 4.8 优先级与停止传播

```python
@filter.command("check", priority=1)
async def check(self, event: AstrMessageEvent):
    if not self.check_ok():
        yield event.plain_result("检查失败")
        event.stop_event()
```

多个过滤器通常是 AND 逻辑。调用 `event.stop_event()` 后会阻止后续插件 Handler、LLM 请求等流程。

## 5. 事件钩子

事件钩子不建议与 `@filter.command`、`@filter.command_group`、`@filter.event_message_type`、`@filter.platform_adapter_type`、`@filter.permission_type` 混用。

常见钩子：

```python
@filter.on_astrbot_loaded()
async def on_loaded(self):
    pass

@filter.on_waiting_llm_request()
async def on_waiting_llm(self, event: AstrMessageEvent):
    await event.send(event.plain_result("正在等待请求..."))

@filter.on_llm_request()
async def on_llm_request(self, event: AstrMessageEvent, req):
    pass

@filter.on_llm_response()
async def on_llm_response(self, event: AstrMessageEvent, resp):
    pass

@filter.on_decorating_result()
async def on_decorating_result(self, event: AstrMessageEvent):
    pass

@filter.after_message_sent()
async def after_message_sent(self, event: AstrMessageEvent):
    pass
```

注意：部分钩子中不能通过 `yield` 发送消息，应使用 `event.send()` 或只修改请求/响应对象。

## 6. 消息对象与消息链

`AstrMessageEvent` 是消息事件对象，常见能力：

- 获取发送者名称：`event.get_sender_name()`
- 获取发送者 ID：`event.get_sender_id()`
- 获取平台 ID：`event.get_platform_id()`
- 获取平台名称：`event.get_platform_name()`
- 获取会话唯一标识：`event.unified_msg_origin`
- 获取底层消息：`event.message_obj`

`event.message_obj` 常见字段：

```text
type, self_id, session_id, message_id, group_id, sender,
message, message_str, raw_message, timestamp
```

消息链常见组件：

- `Plain`：文本
- `At`：提及
- `Image`：图片
- `Record`：语音
- `Video`：视频
- `File`：文件
- OneBot/QQ 相关平台可能支持 `Face`、`Node`、`Nodes`、`Poke` 等扩展段。

## 7. 消息发送 API

### 7.1 被动回复

```python
yield event.plain_result("文本")
yield event.image_result("path/to/image.jpg")
yield event.image_result("https://example.com/image.jpg")
```

图片 URL 必须以 `http` 或 `https` 开头。

### 7.2 消息链回复

```python
import astrbot.api.message_components as Comp

chain = [
    Comp.At(qq=event.get_sender_id()),
    Comp.Plain("来看这个图："),
    Comp.Image.fromFileSystem("path/to/image.jpg"),
]
yield event.chain_result(chain)
```

### 7.3 主动发送

```python
from astrbot.api.event import MessageChain

umo = event.unified_msg_origin
message_chain = MessageChain().message("Hello").file_image("path/to/image.jpg")
await self.context.send_message(umo, message_chain)
```

主动消息依赖平台能力，并非所有平台都支持。

### 7.4 富媒体组件

```python
Comp.Image.fromURL("https://example.com/image.jpg")
Comp.Image.fromFileSystem("path/to/image.jpg")
Comp.File(file="path/to/file.txt", name="file.txt")
Comp.Record(file="path/to/record.wav", url="path/to/record.wav")
Comp.Video.fromFileSystem(path="test.mp4")
Comp.Video.fromURL(url="https://example.com/video.mp4")
```

平台差异风险：文件、视频、语音、合并转发、OneBot 专属消息段不一定跨平台可用。移植时需要能力判断或降级方案。

## 8. 插件配置 `_conf_schema.json`

AstrBot 通过插件根目录 `_conf_schema.json` 生成 WebUI 配置和运行时配置实体。加载流程大致为：

1. 检查插件目录是否存在 `_conf_schema.json`；
2. 解析配置 schema；
3. 在 AstrBot 数据目录生成插件配置实体；
4. 实例化插件类时传入 `AstrBotConfig`。

示例：

```json
{
  "token": {
    "description": "Bot Token",
    "type": "string",
    "default": ""
  },
  "enable_feature": {
    "description": "启用功能",
    "type": "bool",
    "default": true
  },
  "nested": {
    "description": "嵌套配置",
    "type": "object",
    "items": {
      "name": {
        "description": "名称",
        "type": "string",
        "default": ""
      }
    }
  }
}
```

支持类型包括：

```text
string, text, int, float, bool, object, list, dict, template_list, file
```

常见字段：

- `type`：配置类型；
- `description`：配置说明；
- `hint`：提示；
- `obvious_hint`：醒目提示；
- `default`：默认值；
- `items`：嵌套结构；
- `invisible`：隐藏配置；
- `options` / `labels`：下拉选项及展示文本；
- `editor_mode` / `editor_language` / `editor_theme`：编辑器配置；
- `_special`：调用 WebUI 特殊选择组件，例如供应商、人设、知识库等。

移植注意：配置字段命名应稳定，避免后续版本重命名导致用户配置丢失。

## 9. 依赖管理

Python 依赖写入插件根目录：

```text
requirements.txt
```

示例：

```text
aiohttp>=3.9
pydantic>=2
```

建议：

- 避免同步 `requests` 阻塞事件循环；
- 网络请求优先使用 `aiohttp`、`httpx` 等异步库；
- 做好异常处理，避免单个功能错误导致插件整体崩溃；
- 提交前可用 `ruff` / `python -m py_compile` / 单元测试进行验证。

## 10. 资源、静态资产、Skills 与 Pages

### 10.1 Logo

插件根目录可放 `logo.png`：

- 建议 1:1；
- 推荐尺寸 256x256；
- 控制体积。

### 10.2 Skills

插件可携带：

```text
skills/
  skill-name/
    SKILL.md
```

或：

```text
skills/
  SKILL.md
```

插件随附 Skill 会由 AstrBot 加载到 Skill Manager，通常作为插件来源只读展示。

### 10.3 Pages

适合复杂配置、Dashboard、日志、文件上传下载、SSE、自定义交互。

结构：

```text
pages/
  settings/
    index.html
    app.js
    style.css
    assets/
```

规则：

- `pages/` 下每个一级子目录是独立 Page；
- 必须包含 `index.html`；
- 简单配置优先用 `_conf_schema.json`。

后端注册 API 示例：

```python
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        context.register_web_api(
            "/astrbot_plugin_xxx/ping",
            self.page_ping,
            ["GET"],
            "Page ping",
        )
```

API 路由应带插件名作为前缀。

## 11. 国际化

插件可提供：

```text
.astrbot-plugin/i18n/zh-CN.json
.astrbot-plugin/i18n/en-US.json
```

可国际化内容：

- 元数据：`display_name`、`short_desc`、`desc`；
- 配置：`description`、`hint`、`labels`；
- Pages：`title`、`description`、页面自定义文案。

示例：

```json
{
  "metadata": {
    "display_name": "天气助手",
    "short_desc": "一句话天气查询。",
    "desc": "查询天气并提供出行建议。"
  },
  "config": {
    "enable": {
      "description": "启用",
      "hint": "是否启用这个插件。"
    }
  }
}
```

约束：

- 只读取 `.astrbot-plugin/i18n`；
- 文件名使用 WebUI locale，如 `zh-CN.json`；
- 内容必须是 JSON object；
- 不支持点号扁平 key，应使用嵌套结构。

## 12. 调试与热重载

调试插件通常需要启动 AstrBot 本体。修改插件后，可在 WebUI：

```text
插件管理 → 找到插件 → ... → 重载插件
```

如果插件因代码错误加载失败，可尝试 WebUI 的一键重载修复入口。

本项目移植时若没有完整 AstrBot 运行环境，应至少进行：

- Python 语法检查；
- 依赖可导入检查；
- 模拟核心业务逻辑测试；
- 对照原 R 插件输出样式检查。

## 13. 平台原始 API 与平台耦合

获取平台实例：

```python
platform_id = event.get_platform_id()
platform = self.context.get_platform_inst(platform_id)
```

OneBot / aiocqhttp 示例方向：

```python
if event.get_platform_name() == "aiocqhttp":
    client = event.bot
    await client.api.call_action("delete_msg", message_id=event.message_obj.message_id)
```

移植注意：

- 直接调用平台原始 API 会造成强平台耦合；
- 应优先用 AstrBot 抽象消息组件；
- 对 OneBot 专属功能提供平台判断和降级提示。

## 14. 打包与发布

发布到 AstrBot 插件市场通常流程：

1. 将插件代码推送到 GitHub 仓库；
2. 打开 AstrBot 插件市场；
3. 点击提交插件入口；
4. 填写基本信息、作者信息、仓库信息；
5. 提交到 AstrBot 仓库 Issue；
6. 等待审核/CI。

插件市场：

```text
https://plugins.astrbot.app
```

大小限制：

- 插件 zip 不得超过 16MB。

建议：

- 不提交 `.git`、`__pycache__`、`node_modules`、临时文件、大型日志；
- 压缩图片/音频等静态资源；
- 添加 `.gitignore`；
- 精简大体积依赖。

## 15. R 插件移植到 AstrBot 的技术注意事项

后续移植 `rconsole-plugin` 时应按以下顺序对照：

1. **命令映射**：原插件命令 → `@filter.command` 或 `@filter.command_group`。
2. **参数解析**：原命令参数规则 → AstrBot 函数签名或手动解析 `event.message_str`。
3. **权限控制**：原管理员/主人/群权限 → `@filter.permission_type` 或插件内部校验。
4. **消息样式**：原文本、图片、表情、At、换行、菜单 → `Plain` / `Image` / `At` / 平台专属组件。
5. **资源迁移**：原图片、字体、模板、静态文件 → 插件资源目录。
6. **配置迁移**：原配置文件 → `_conf_schema.json` + `AstrBotConfig`。
7. **异步适配**：原同步 IO / 网络请求 → 异步实现或线程隔离。
8. **平台能力**：OneBot 专属能力需在 AstrBot 平台判断后调用或降级。
9. **持久化数据**：避免写入插件目录，迁移到 AstrBot 数据目录。
10. **验证策略**：逐命令对照 R 插件原输出，记录功能/样式一致性。

## 16. 已查阅来源

- https://docs.astrbot.app/dev/star/plugin-new.html
- https://docs.astrbot.app/dev/star/guides/simple.html
- https://docs.astrbot.app/dev/star/guides/listen-message-event.html
- https://docs.astrbot.app/dev/star/guides/send-message.html
- https://docs.astrbot.app/dev/star/guides/plugin-config.html
- https://docs.astrbot.app/dev/star/guides/plugin-pages.html
- https://docs.astrbot.app/dev/star/guides/plugin-i18n.html
- https://docs.astrbot.app/dev/star/guides/other.html
- https://docs.astrbot.app/dev/star/plugin-publish.html
- https://docs.astrbot.app/dev/star/plugin.html

辅助 Markdown 源：

- https://raw.githubusercontent.com/AstrBotDevs/AstrBot/master/docs/zh/dev/star/plugin-new.md
- https://raw.githubusercontent.com/AstrBotDevs/AstrBot/master/docs/zh/dev/star/guides/simple.md
- https://raw.githubusercontent.com/AstrBotDevs/AstrBot/master/docs/zh/dev/star/guides/listen-message-event.md
- https://raw.githubusercontent.com/AstrBotDevs/AstrBot/master/docs/zh/dev/star/guides/send-message.md
- https://raw.githubusercontent.com/AstrBotDevs/AstrBot/master/docs/zh/dev/star/guides/plugin-config.md
- https://raw.githubusercontent.com/AstrBotDevs/AstrBot/master/docs/zh/dev/star/guides/plugin-pages.md
- https://raw.githubusercontent.com/AstrBotDevs/AstrBot/master/docs/zh/dev/star/guides/plugin-i18n.md
- https://raw.githubusercontent.com/AstrBotDevs/AstrBot/master/docs/zh/dev/star/guides/other.md
- https://raw.githubusercontent.com/AstrBotDevs/AstrBot/master/docs/zh/dev/star/plugin-publish.md
- https://raw.githubusercontent.com/AstrBotDevs/AstrBot/master/docs/zh/dev/star/plugin.md

## 17. 当前不确定性

- 未启动 AstrBot 本体运行验证示例代码。
- 不同 AstrBot 版本和不同平台适配器支持能力可能不同。
- Agent 钩子、配置 `_special` 内部项、平台适配器能力可能随版本变化。
- 后续应结合目标 AstrBot 版本和 R 插件实际功能做更细映射。
