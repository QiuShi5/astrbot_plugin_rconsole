# AstrBot 插件开发与发布合规要求清单（Compliance Checklist）

> 数据来源：AstrBot 官方文档站 https://docs.astrbot.app/ （抓取于 2026-08-18）。
> 本文按类别汇总可查证的全部合规要求，逐条给出**原文引用**、**出处 URL** 和**解读**。
> 无法在文档中验证的项目在文末「未能验证 / 未在文档中发现」一节显式列出，**不对未找到的内容进行推测**。
> 另有两节「AstrBot 源码层校验」与「官方插件商店仓库提交流程」作为**补充证据**（非文档正文），已明确标注出处。

---

## 0. 已读取的文档页面清单

| 页面 | URL | 状态 |
|---|---|---|
| 发布插件到插件市场 | https://docs.astrbot.app/dev/star/plugin-publish.html | ✅ 已完整读取 |
| 插件开发指南（新，入口） | https://docs.astrbot.app/dev/star/plugin-new.html | ✅ 已完整读取 |
| 插件开发指南（旧，参考） | https://docs.astrbot.app/dev/star/plugin.html | ✅ 已完整读取（带「已过时」警告，仍可参考） |
| 最小实例 | https://docs.astrbot.app/dev/star/guides/simple.html | ✅ |
| 处理消息事件 | https://docs.astrbot.app/dev/star/guides/listen-message-event.html | ✅ |
| 消息的发送 | https://docs.astrbot.app/dev/star/guides/send-message.html | ✅ |
| 插件配置（_conf_schema.json） | https://docs.astrbot.app/dev/star/guides/plugin-config.html | ✅ |
| 会话控制 | https://docs.astrbot.app/dev/star/guides/session-control.html | ✅ |
| 插件存储 | https://docs.astrbot.app/dev/star/guides/storage.html | ✅ |
| 插件国际化 | https://docs.astrbot.app/dev/star/guides/plugin-i18n.html | ✅ |
| 插件 Pages | https://docs.astrbot.app/dev/star/guides/plugin-pages.html | ✅ |
| 文转图 | https://docs.astrbot.app/dev/star/guides/html-to-pic.html | ✅ |
| AI（LLM / Tool / Agent） | https://docs.astrbot.app/dev/star/guides/ai.html | ✅ |
| 插件市场 JSON 规范 2026-06-27 | https://docs.astrbot.app/dev/plugin-market/2026-06-27.html | ✅ 规范性文件 |
| 插件市场规范（索引） | https://docs.astrbot.app/dev/plugin-market/ | ✅（仅列出上述一个规范版本） |
| 开发一个平台适配器 | https://docs.astrbot.app/dev/plugin-platform-adapter.html | ✅ |
| AstrBot 配置文件 | https://docs.astrbot.app/dev/astrbot-config.html | ✅ |
| AstrBot HTTP API / Scope | https://docs.astrbot.app/dev/openapi.html 、https://docs.astrbot.app/dev/openapi-scopes.html | ✅（与插件合规基本无关，未发现额外要求） |
| FAQ | https://docs.astrbot.app/faq.html | ✅（含 requirements.txt 相关说明） |
| 使用插件（Star） | https://docs.astrbot.app/use/plugin.html | ✅（用户视角页面，无额外发布要求） |
| /dev/ 根路径 | https://docs.astrbot.app/dev/ | ⚠️ 返回 404（VitePress 无此目录页；所有 dev 子页已通过 sitemap/侧边栏枚举并抓取） |
| 外部「插件发布页面 / AstrBot Cloud」 | https://plugins.astrbot.app（文档内链接，需登录账号） | ⚠️ **未能抓取**：发布表单为需注册 AstrBot Cloud 账号的 Web 应用，非文档页面，其表单校验规则无法验证 |

---

## 1. 插件基础结构与命名规范

### 1.1 插件类与文件结构

| # | 要求 | 原文 | 出处 | 解读 |
|---|---|---|---|---|
| 1.1.1 | **插件类必须继承 `Star`**，并定义在 **`main.py`** 中 | 「插件是继承自 Star 基类的类实现。」／「插件类所在的文件名需要命名为 main.py。」 | https://docs.astrbot.app/dev/star/plugin.html ；https://docs.astrbot.app/dev/star/guides/simple.html | 插件入口文件必须叫 `main.py`，插件类必须 `class MyPlugin(Star)` 并调用 `super().__init__(context)`。 |
| 1.1.2 | **Handler 必须在插件类中注册，前两个参数必须是 `self` 和 `event`** | 「Handler 一定需要在插件类中注册，前两个参数必须为 self 和 event。如果文件行数过长，可以将服务写在外部，然后在 Handler 中调用。」 | https://docs.astrbot.app/dev/star/plugin.html ；https://docs.astrbot.app/dev/star/guides/simple.html | 所有事件处理函数都要写在插件类内部；业务逻辑可外置，但 handler 本体必须在类中。 |
| 1.1.3 | 插件名（仓库目录名 / Repository name）**推荐以 `astrbot_plugin_` 开头** | 「插件名格式: 推荐以 astrbot_plugin_ 开头；不能包含空格；保持全部字母小写；尽量简短。」 | https://docs.astrbot.app/dev/star/plugin-new.html （同旧版 https://docs.astrbot.app/dev/star/plugin.html ） | **注意：这是「推荐」而非「强制」**。官方模板、市场规范示例均使用 `astrbot_plugin_` 前缀，但文档未将其列为必须字段的校验规则。同时要求：不含空格、全小写、尽量简短。 |
| 1.1.4 | 事件监听器注册子必须先导入 `astrbot.api.event.filter` | 「事件监听器的注册器在 astrbot.api.event.filter 下，需要先导入。请务必导入，否则会和 python 的高阶函数 filter 冲突。」 | https://docs.astrbot.app/dev/star/guides/listen-message-event.html | `from astrbot.api.event import filter, AstrMessageEvent` 之后再使用 `@filter.command` 等装饰器。 |
| 1.1.5 | 同步取 LLM 的旧接口已弃用，异步 handler 必须用异步接口 | 「异步事件处理函数中请使用 get_using_provider_async()。为兼容现有插件，get_using_provider() 同步接口仍然可用，但已标记为弃用。」 | https://docs.astrbot.app/dev/star/plugin.html | 新插件在 async handler 中调用 provider 时使用 `await self.context.get_using_provider_async(umo=...)`。 |

### 1.2 插件生命周期（生命周期 / 异步初始化与销毁）

| # | 要求 | 原文 | 出处 | 解读 |
|---|---|---|---|---|
| 1.2.1 | 可选择性实现异步 `initialize()`（实例化后自动调用） | 「可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。」 | 官方模板 helloworld 的 main.py（模板由文档链接引用： https://github.com/Soulter/helloworld ）；旧版文档同样示例：https://docs.astrbot.app/dev/star/plugin.html#最小实例 | 新版推荐用 `async def initialize(self)`；文档主文未强制，但模板中为标准写法。 |
| 1.2.2 | 可选择性实现异步 `terminate()`（卸载/停用时调用） | 「可选择实现 terminate 函数，当插件被卸载/停用时会调用。」 | https://docs.astrbot.app/dev/star/plugin.html ；https://docs.astrbot.app/dev/star/guides/simple.html | 需要做资源清理（关连接、存状态）时实现它。注意模板中该函数也是 `async`。 |

### 1.3 事件钩子（Event Hooks）约束

| # | 要求 | 原文 | 出处 | 解读 |
|---|---|---|---|---|
| 1.3.1 | 事件钩子**不能**与指令/事件类型/平台/权限过滤器混用 | 「事件钩子不支持与上面的 @filter.command, @filter.command_group, @filter.event_message_type, @filter.platform_adapter_type, @filter.permission_type 一起使用。」 | https://docs.astrbot.app/dev/star/guides/listen-message-event.html ；https://docs.astrbot.app/dev/star/plugin.html | `on_llm_request` / `on_llm_response` / `on_decorating_result` / `after_message_sent` 等钩子独立使用。 |
| 1.3.2 | 钩子内**不能 `yield` 发消息**，只能用 `event.send()` | 「这里不能使用 yield 来发送消息。如需发送，请直接使用 event.send() 方法。」 | https://docs.astrbot.app/dev/star/plugin.html （各钩子小节） | `on_llm_request`、`on_llm_response`、`on_decorating_result`、`after_message_sent`、`on_agent_begin`、`on_using_llm_tool`、`on_llm_tool_respond`、`on_agent_done` 均适用。 |
| 1.3.3 | 不要每轮把动态内容追加进 `system_prompt`（破坏缓存、显著增加成本） | 「不建议把每轮都会变化的内容追加到 system_prompt…这类写法会让系统提示词在每轮请求中变化，容易破坏模型服务端的提示词缓存，显著增加请求成本和首 token 延迟。对于每轮都会变化…优先通过 req.extra_user_content_parts 追加」 | https://docs.astrbot.app/dev/star/plugin.html ；https://docs.astrbot.app/dev/star/guides/listen-message-event.html | 属于性能/成本规范；动态内容用 `req.extra_user_content_parts`（临时内容可 `.mark_as_temp()`，需 ≥ v4.24.0）。 |

---

## 2. metadata.yaml —— 插件元数据要求

> 文档主页面：https://docs.astrbot.app/dev/star/plugin-publish.html （发布页给出「完整的插件元数据示例，系统会自动解析这些信息」）。

### 2.1 文件本身

| # | 要求 | 原文 | 出处 | 解读 |
|---|---|---|---|---|
| 2.1.1 | 插件根目录必须有 `metadata.yaml`，AstrBot 识别插件依赖它 | 「请务必修改此文件，AstrBot 识别插件元数据依赖于 metadata.yaml 文件。」／「AstrBot 插件市场的信息展示依赖于 metadata.yaml 文件。」 | https://docs.astrbot.app/dev/star/plugin-new.html ；https://docs.astrbot.app/dev/star/plugin.html | 无 metadata 插件不能正确展示/识别；市场信息全部来自该文件。 |
| 2.1.2 | 也可接受 `metadata.yml`（源码层） | 源码 `PLUGIN_METADATA_FILENAMES = ("metadata.yaml", "metadata.yml")` | 补充来源（AstrBot 源码 astrbot/core/star/updater.py） | 文档正文只写 `metadata.yaml`，源码额外接受 `.yml` 扩展名。 |
| 2.1.3 | metadata 文件必须为 UTF-8 编码、≤ 1MB、合法 YAML dict | 源码校验：`{filename} 必须使用 UTF-8 编码。`、`{filename} 格式错误。`、`{filename} 超过 1MB。` | 补充来源（AstrBot 源码 astrbot/core/star/updater.py） | 文档正文未提这些硬性限制，属源码层校验。 |
| 2.1.4 | `name` 必须是合法 Python 标识符（不含 `/`、`\`、非关键字），不可导入时将加载失败 | 「metadata 文件中 name 含有路径分隔符，不可用于 importlib 加载。」／「metadata 文件中 name 不是合法的模块名称（应为合法 Python 标识符且非关键字）。」 | 补充来源（AstrBot 源码 astrbot/core/star/star_manager.py）与文档的命名格式要求（第 1.1.3 条） | 若 `name` 无法作为模块名，插件加载失败。 |

### 2.2 必填字段（文档视角）

发布页给出完整示例，末尾注释明确标注了每个字段的含义。**文档未逐字段标注 required**，但示例中以非注释形式给出以下字段；结合源码校验判定其「必填」：

```yaml
name: astrbot_plugin_example                 # 插件标识符，英文，唯一
display_name: 示例插件名称                    # 插件展示名称
# short_desc: 一句话介绍你的插件功能           # （可选）
desc: 详细描述插件的功能、特性、使用方法等信息。 # 详细描述插件的信息（支持多行/Markdown）
version: 1.0.0                               # 插件版本号（遵循语义化版本规范）
author: 作者名称                              # 作者名称
repo: https://github.com/your-name/repo      # 插件仓库地址
```

出处：https://docs.astrbot.app/dev/star/plugin-publish.html

| 字段 | 文档原文（注释） | 文档明确的可选性 | 源码层必填判定 |
|---|---|---|---|
| `name` | 「插件标识符，英文，唯一」 | — | **必填**：`PLUGIN_METADATA_REQUIRED_FIELDS = ("name", "desc", "version", "author")`，须为非空字符串 |
| `desc` | 「详细描述插件的信息，可以写多行文本，支持 Markdown」 | — | **必填**（可用 `description` 作为别名，源码会自动转换） |
| `version` | 「插件版本号（遵循语义化版本规范）」 | — | **必填**，须为非空字符串 |
| `author` | 「作者名称」 | — | **必填**，须为非空字符串 |
| `repo` | 「插件仓库地址」 | — | **非必填**（源码 `repo=metadata["repo"] if "repo" in metadata else None`；安装时缺省会回填仓库 URL） |
| `display_name` | 「插件展示名称」（v4.5.0+ 生效） | — | 可选 |
| `short_desc` | 一行短描述，无则回退显示 `desc` | ✅ 注释标注「（可选）」 | 可选 |

> 出处（源码层）：https://github.com/AstrBotDevs/AstrBot/blob/master/astrbot/core/star/updater.py
> 「desc / description 别名」与「必填字段」原文：`if "desc" not in normalized_metadata and "description" in normalized_metadata: normalized_metadata["desc"] = normalized_metadata["description"]`

**重要提示（文档/源码差异）**：发布页示例把 `display_name` 与 `repo` 也显示为非注释的常规字段，但**源码校验的必填字段只有 `name`/`desc`/`version`/`author` 四个**。若以「最小必然被接受」为准，底线是 4 个；若以「发布页完整示例」为准，则上述全部常规字段都应填写。

### 2.3 可选字段

| 字段 | 原文 | 出处 | 解读 |
|---|---|---|---|
| `short_desc` | 「（可选）紧凑 UI 使用的短描述」 | 发布页 | 插件市场卡片短描述；缺省回退 `desc`。 |
| `astrbot_version` | 「（可选）支持的 AstrBot 版本范围」 | 发布页 | 见 2.4。 |
| `support_platforms` | 「（可选）支持的平台适配器列表」 | 发布页 | 见 2.5。 |
| `social_link` | 「（可选）你的个人网站、GitHub 主页等」 | 发布页 | 展示作者社交链接。 |
| `tags` | 「（可选）标签列表，用于插件市场分类和搜索」 | 发布页 | 市场分类/搜索。 |
| `pages` | （Pages 章节隐式声明，插件可注册 Page） | https://docs.astrbot.app/dev/star/guides/plugin-pages.html 、源码 StarMetadata.pages | 可选列表。 |

### 2.4 `astrbot_version` 格式要求（兼容性 / 最低版本声明）

| # | 要求 | 原文 | 出处 | 解读 |
|---|---|---|---|---|
| 2.4.1 | 格式与 pyproject.toml 依赖约束一致（**PEP 440**），**不要加 `v` 前缀** | 「格式与 pyproject.toml 依赖版本约束一致（PEP 440），且不要加 v 前缀。」 | https://docs.astrbot.app/dev/star/plugin-new.html ；https://docs.astrbot.app/dev/star/plugin.html | 合法示例：`>=4.17.0`、`>=4.16,<5`、`~=4.17`。 |
| 2.4.2 | 只声明最低版本可直接写 `>=4.17.0` | 「如果你只想声明最低版本，可以直接写：>=4.17.0」 | 同上 | 用 `SpecifierSet` 解析（源码层用 `packaging` 的 `SpecifierSet` 校验）。 |
| 2.4.3 | 当前 AstrBot 版本不满足时**插件会被阻止加载** | 「当当前 AstrBot 版本不满足该范围时，插件会被阻止加载并提示版本不兼容。 在 WebUI 安装插件时，你可以选择“无视警告，继续安装”来跳过这个检查。」 | 同上 | 写错范围或空值会加载失败/提示；用户可显式跳过。非法 specifier 源码会提示「Invalid astrbot_version. Use a PEP 440 range, e.g. >=4.16,<5.」。 |

### 2.5 `support_platforms` 允许值（平台适配器 key 列表）

| # | 要求 | 原文 | 出处 |
|---|---|---|---|
| 2.5.1 | 值必须使用 `ADAPTER_NAME_2_TYPE` 的 key | 「support_platforms 中的值需要使用 ADAPTER_NAME_2_TYPE 的 key，目前支持：…」 | https://docs.astrbot.app/dev/star/plugin-new.html ；旧版 https://docs.astrbot.app/dev/star/plugin.html |

**新版指南（plugin-new.html）列出的完整允许值：**

```
aiocqhttp, qq_official, qq_official_webhook, telegram, wecom, wecom_ai_bot,
lark, dingtalk, discord, slack, kook, vocechat, weixin_official_account,
weixin_oc, satori, misskey, line, matrix, mattermost
```

**旧版指南（plugin.html）列出的列表较旧（缺 qq_official_webhook / wecom_ai_bot / weixin_oc / matrix / mattermost）：**

```
aiocqhttp, qq_official, telegram, wecom, lark, dingtalk, discord,
slack, kook, vocechat, weixin_official_account, satori, misskey, line
```

> **解读**：以**新版指南/源码 ADAPTER_NAME_2_TYPE** 为准。`support_platforms` 只影响 WebUI 展示，非法值不会导致加载失败，但无法正确展示支持平台。注意当前 AstrBot 还支持 `WEBCHAT`、`ALL` 等平台类型（见 listen-message-event 的 `PlatformAdapterType` 枚举），但文档仅列出上述值用于声明插件支持平台。

### 2.6 `version` 字段版本号格式

| # | 要求 | 原文 | 出处 | 解读 |
|---|---|---|---|---|
| 2.6.1 | 插件版本号遵循**语义化版本规范** | 「version: 1.0.0 # 插件版本号（遵循语义化版本规范）」 | https://docs.astrbot.app/dev/star/plugin-publish.html | 即 `X.Y.Z` 形式。 |
| 2.6.2 | ⚠️ 官方模板却使用 `v` 前缀 | 模板 metadata.yaml 注释：「插件版本号。格式：v1.1.1 或者 v1.1」，示例 `version: v1.3.0` | 官方模板 https://github.com/Soulter/helloworld （文档链接引用） | **文档/模板不一致**：发布页写「语义化版本」（示例无 `v`），模板写「v1.1.1 或 v1.1」。保险做法：按发布页示例用无 `v` 的纯语义化版本 `X.Y.Z`；源码层对 `version` 只要求非空字符串（updater.py），`v1.3.0` 也能通过。 |

---

## 3. `_conf_schema.json` —— 插件配置 Schema 要求

> 文档页面：https://docs.astrbot.app/dev/star/guides/plugin-config.html （旧版同内容亦见 https://docs.astrbot.app/dev/star/plugin.html#插件配置 ）

| # | 要求 | 原文 | 出处 | 解读 |
|---|---|---|---|---|
| 3.1 | 注册配置**必须在插件目录下添加 `_conf_schema.json`**，JSON 格式 | 「要注册配置，首先需要在您的插件目录下添加一个 _conf_schema.json 的 json 文件。」 | plugin-config 指南；旧版 plugin.html | 文件名为固定 `_conf_schema.json`。 |
| 3.2 | **`type` 是唯一必填字段**，支持 `string, text, int, float, bool, object, list, dict, template_list` | 「type: 此项必填。配置的类型。支持 string, text, int, float, bool, object, list, dict, template_list。」 | plugin-config 指南（旧版 plugin.html 列表缺少 `dict`、`template_list`） | 其余字段均可选。 |
| 3.3 | 各字段定义 | 「description: 可选。配置的描述。… hint: 可选。配置的提示信息… obvious_hint: 可选。… default: 可选。配置的默认值。… items: 可选。如果配置的类型是 object，需要添加 items 字段。… invisible: 可选。配置是否隐藏。默认是 false。… options: 可选。… editor_mode: 可选。… editor_language: 可选。…（默认为 json） editor_theme: 可选。…（vs-light 默认/ vs-dark） _special: 可选。…」 | plugin-config 指南 | `type` 之外全部可选；`description`/`hint` 建议写一整句。 |
| 3.4 | 默认值规则 | 「default: 可选。配置的默认值。… int 是 0，float 是 0.0，bool 是 False，string 是 ""，object 是 {}，list 是 []。」 | plugin-config 指南 | 未给 default 时的隐式默认值。 |
| 3.5 | `_special` 内部取值**禁止插件使用** | 「AstrBot Core 内部还使用了 select_providers、provider_pool、persona_pool、select_plugin_set、t2i_template、get_embedding_dim、select_agent_runner_provider:* 等 _special 值。这些属于内部实现，随时可能变动，请勿在插件中使用。」 | plugin-config 指南 | 插件只能用 `select_provider`、`select_provider_tts`、`select_provider_stt`、`select_persona`、`select_knowledgebase`。 |
| 3.6 | `file` 类型（v4.13.0+） | 「file 类型的 schema：在 v4.13.0 之后引入，允许插件定义文件上传配置项…"default": [] …"file_types": ["pdf", "docx"]」 | plugin-config 指南 | 需配套 `default: []` 与 `file_types` 才可多文件上传。 |
| 3.7 | `dict` 类型（可视化 dict） | 「用于可视化编辑一个 Python 的 dict 类型的配置。」（可配 `template_schema` 供 WebUI 快速编辑） | plugin-config 指南 | — |
| 3.8 | `template_list` 类型（v4.10.4 引入，PR #4208） | 「插件开发者可以在_conf_schema中按照以下格式添加模板配置项…templates: {...}」 | plugin-config 指南 | 模板可选字段 `display_item`、`hide_hint_in_list`；保存后键形如 `__template_key`。 |
| 3.9 | 配置文件落盘位置 | 「AstrBot 在载入插件时会检测插件目录下是否有 _conf_schema.json 文件，如果有，会自动解析配置并保存在 data/config/<plugin_name>_config.json 下，并在实例化插件类时传入给 __init__()。」 | plugin-config 指南；旧版 plugin.html | `__init__(self, context, config: AstrBotConfig)`；`config` 继承自 `Dict`。 |
| 3.10 | Schema 版本管理 | 旧版：「AstrBot 会递归检查 Schema 的配置项，如果发现配置文件中缺失了某个配置项，会自动添加默认值。但是 AstrBot 不会删除配置文件中多余的配置项。」新版改为：「自动为缺失的配置项添加默认值、移除不存在的配置项。」 | 旧版 plugin.html / 新版 plugin-config 指南 | 发布新版本升级 Schema 时，新版会自动补默认值并移除已删除项（注意两版表述有差异）。 |
| 3.11 | 文件编码 | 源码：`插件配置 schema 必须使用 UTF-8 编码` / `插件配置 schema 不是有效的 JSON`（接受 UTF-8 BOM） | 补充来源（astrbot/core/star/star_manager.py） | 文档未写编码要求，源码强制 UTF-8 + 合法 JSON。 |
| 3.12 | 配置项文案国际化 | 「配置项的 description、hint 和下拉选项 labels 支持按 WebUI 语言显示，详见插件国际化。」 | plugin-config 指南 | 经 `.astrbot-plugin/i18n/*.json` 实现（见第 6 节）。 |

---

## 4. 依赖（Dependencies）与打包要求

| # | 要求 | 原文 | 出处 | 解读 |
|---|---|---|---|---|
| 4.1 | 插件依赖必须写入插件目录下的 **`requirements.txt`** | 「目前 AstrBot 对插件的依赖管理使用 pip 自带的 requirements.txt 文件。如果你的插件需要依赖第三方库，请务必在插件目录下创建 requirements.txt 文件并写入所使用的依赖库，以防止用户在安装你的插件时出现依赖未找到(Module Not Found)的问题。」 | https://docs.astrbot.app/dev/star/plugin-new.html ；https://docs.astrbot.app/dev/star/plugin.html | 依赖库列表放插件根目录 `requirements.txt`；格式遵循 pip 官方文档。 |
| 4.2 | 缺少 requirements.txt 是已知的插件安装失败主因 | 「安装插件后报错 No module named 'xxx'…插件作者没有填写 requirements.txt 文件…如果发现插件作者没有填写 requirements.txt 文件，请在插件仓库提交 Issue，提醒作者补充。」 | https://docs.astrbot.app/faq.html | 侧面印证：凡有第三方依赖，填写 requirements.txt 是社区/官方预期行为。 |
| 4.3 | **不要使用 `requests`** 做网络请求，用异步库 | 「不要使用 requests 库来进行网络请求，可以使用 aiohttp, httpx 等异步库。」（新指南：「…异步网络请求库。」） | https://docs.astrbot.app/dev/star/plugin.html ；https://docs.astrbot.app/dev/star/plugin-new.html | 网络调用用 aiohttp / httpx 等异步库。 |
| 4.4 | 压缩包（zip）大小不得超过 **16MB** | 「发布到插件市场的插件压缩包（zip）大小不得超过 16MB。如果超过此限制，CI/CD 流水线将自动拒绝该发布请求。」 | https://docs.astrbot.app/dev/star/plugin-publish.html | 硬性门槛 + 自动化拒绝；超限可联系维护者手动 bypass。 |
| 4.5 | 打包体积建议（gitignore / 资源压缩 / .gitattributes 或发布分支） | 「清理不必要的文件：避免将 .git 目录、__pycache__、node_modules、开发用配置文件等非必需文件提交到插件仓库中。建议在仓库根目录添加 .gitignore 来排除它们。」「压缩图片等静态资源…优化依赖体积…使用 .gitattributes 或发布分支」 | 同上 | 建议项（推荐），非强制性校验（除 16MB 硬限外）。 |

---

## 5. 日志（Logging）与错误处理规范

| # | 要求 | 原文 | 出处 | 解读 |
|---|---|---|---|---|
| 5.1 | **必须使用 `from astrbot.api import logger`，不要用 Python 标准库 `logging`** | 「请务必使用 from astrbot.api import logger 来获取日志对象，而不是使用 logging 模块。」 | https://docs.astrbot.app/dev/star/plugin.html | 标准库 logging 会被路由/分级机制绕过。 |
| 5.2 | 每个插件自动拥有独立 `self.logger` | 「每个插件在 __init__ 后会自动拥有独立的 self.logger。这个 logger 的等级可以在 WebUI 的插件配置弹窗中单独设置，不会影响其他插件和核心。也可以继续使用 from astrbot.api import logger，它会根据调用位置自动路由到当前插件的 logger。」 | 同上 | 可用 `self.logger` 或 `logger`（模块级路由到当前插件）。 |
| 5.3 | 良好的错误处理机制，插件不应因一个错误崩溃 | 「良好的错误处理机制，不要让插件因一个错误而崩溃。」 | https://docs.astrbot.app/dev/star/plugin.html ；https://docs.astrbot.app/dev/star/plugin-new.html | 兜底 try/except + 记日志是官方原则（示例见会话控制章节用 `logger.error(...)` + 异常提示）。 |
| 5.4 | `@filter.llm_tool` 装饰器须按规范写 docstring，否则参数被静默丢弃 | 「Args: 段是必须的，且格式不能写错。」「@filter.llm_tool 装饰器通过解析函数的 docstring 来生成工具的参数 schema…如果 docstring 缺少 Args: 段，或格式不符合 参数名(类型): 描述 的规范，框架生成的参数 schema 将为空…」 | https://docs.astrbot.app/dev/star/guides/ai.html | 参数类型层支持 `string, number, object, boolean, array`（v4.5.7 后支持 `array[string]`）。 |
| 5.5 | 平台适配器必须实现特定方法 | 「send_by_session…必须实现」「meta()…必须实现」「run()…必须实现」，事件处理要 `commit_event(...)`、发送要 `await super().send(message)` | https://docs.astrbot.app/dev/star/plugin-platform-adapter.html | 仅对「平台适配器插件」生效（业务插件不适用）。 |

---

## 6. 存储与资源目录规范

| # | 要求 | 原文 | 出处 | 解读 |
|---|---|---|---|---|
| 6.1 | **持久化数据存 `data/` 目录，不存插件自身目录**（防止更新/重装覆盖） | 「持久化数据请存储于 data 目录下，而非插件自身目录，防止更新/重装插件时数据被覆盖。」 | https://docs.astrbot.app/dev/star/plugin.html ；https://docs.astrbot.app/dev/star/plugin-new.html | 插件目录在更新时会被整体替换。 |
| 6.2 | 大文件存放目录规范：`data/plugin_data/{plugin_name}/` | 「为了规范插件存储大文件的行为，请将大文件存储于 data/plugin_data/{plugin_name}/ 目录下。」 | https://docs.astrbot.app/dev/star/guides/storage.html | 用 `get_astrbot_data_path()` 拼路径；`self.name` 在 v4.9.2+ 可用。 |
| 6.3 | 插件 Logo：目录下 `logo.png`，长宽比 1:1，推荐 256x256（v4.5.0+ 生效） | 「你可以在插件目录下添加一个 logo.png 文件…请保持长宽比为 1:1，推荐尺寸为 256x256。」 | https://docs.astrbot.app/dev/star/plugin.html ；新指南 https://docs.astrbot.app/dev/star/plugin-new.html | 低版本不报错、不生效。 |
| 6.4 | Skills：可在插件目录提供 `skills/` 文件夹（`skills/<name>/SKILL.md` 或直接 `skills/SKILL.md`） | 「插件可以在自己的目录下提供 skills/ 文件夹。AstrBot 加载插件后会自动把其中合法的 Skill 纳入 Skill Manager…」 | https://docs.astrbot.app/dev/star/plugin.html ；新指南同 | 插件卸载/更新后随文件变化；WebUI Skills 页只读展示。 |
| 6.5 | Pages：`pages/<page_name>/index.html`（每个一级子目录一个 Page） | 「pages/ 下的每个一级子目录是一个独立 Page。AstrBot 只扫描 pages/<page_name>/index.html，没有 index.html 的目录会被忽略。」「page_name 应使用简单目录名…不要使用空目录名、.、..、以 . 开头的目录名，或包含 /、\ 的名称。」 | https://docs.astrbot.app/dev/star/guides/plugin-pages.html | 只能含 `index.html` 的目录；Page 名有命名限制。 |
| 6.6 | Pages 后端 API：路由须包含插件名前缀；优先用 `astrbot.api.web`，避免暴露 FastAPI/Starlette/Quart 原始对象 | 「路由需要包含插件名作为前缀。」「插件后端推荐使用 astrbot.api.web，不要把 FastAPI、Starlette 或 Quart 的原始请求对象作为插件公共 API 暴露给自己的业务代码。」 | 同上 | Web API 用 `context.register_web_api(route, handler, methods, desc)` 注册。 |
| 6.7 | Pages 安全约束：受限 iframe（allow-scripts allow-forms allow-downloads），不能访问 Dashboard cookies/LocalStorage/DOM，须走 bridge，后端必须校验输入 | 「Page 不能直接访问 Dashboard cookies、LocalStorage 或父页面 DOM…」「后端 handler 仍然要验证输入。不要信任 Page 传来的路径、文件名、格式或数值范围；文件落盘时应使用安全目录，并对文件名做白名单或重新命名。」 | 同上 | 前端通过 `window.AstrBotPluginPage` bridge 通信。 |
| 6.8 | 国际化文件目录 `.astrbot-plugin/i18n/*.json` | 「插件可以在自己的目录下提供 .astrbot-plugin/i18n/*.json，让 WebUI 根据当前语言显示插件名称、描述和配置项文案。」 | https://docs.astrbot.app/dev/star/guides/plugin-i18n.html | — |
| 6.9 | i18n 文件必须是 JSON object，且必须用嵌套结构 | 「文件内容必须是 JSON object。」「插件国际化只读取 .astrbot-plugin/i18n 目录。语言文件必须使用嵌套 JSON 结构，不支持点号扁平 key。」 | 同上 | 语言文件名用 WebUI locale（如 zh-CN.json）；缺翻译回退到 metadata/conf_schema 默认文案。 |

---

## 7. 插件市场发布（Store Submission）要求

> 主页面：https://docs.astrbot.app/dev/star/plugin-publish.html

| # | 要求 | 原文 | 出处 | 解读 |
|---|---|---|---|---|
| 7.1 | 插件由 **GitHub 托管**，发布前先推送到 GitHub 仓库 | 「AstrBot 使用 GitHub 托管插件，因此你需要先将插件代码推送到之前创建的 GitHub 插件仓库中。」 | 发布页 | 发布的前提是有一个 GitHub 仓库。 |
| 7.2 | 发布需通过官方发布页面并**注册 AstrBot Cloud 账号** | 「你可以前往 AstrBot 插件发布页面 发布你的插件，发布插件需要注册 AstrBot Cloud 账号。」 | 发布页 | 发布流程在外部 Web 应用（plugins.astrbot.app）完成，需登录账号。 |
| 7.3 | 系统自动解析 metadata.yaml 中的信息 | 「以下是一个完整的插件元数据示例（metadata.yaml），系统会自动解析这些信息」 | 发布页 | metadata.yaml 是市场信息唯一来源。 |
| 7.4 | 驳回上限：zip ≤ 16MB；CI/CD 自动拒绝，可联系维护者 bypass | 「发布到插件市场的插件压缩包（zip）大小不得超过 16MB。如果超过此限制，CI/CD 流水线将自动拒绝该发布请求。」「如果插件确实因业务需要无法压缩到 16MB 以内，可以联系维护者手动 bypass 此限制。」 | 发布页 | 硬性限制 + 唯一人工例外通道。 |
| 7.5 | 打包建议（推荐项） | 「压缩图片等静态资源…清理不必要的文件…建议在仓库根目录添加 .gitignore…优化依赖体积…使用 .gitattributes 或发布分支」 | 发布页 | — |
| 7.6 | 需要 `metadata.yaml` 才能通过市场身份校验 | 「安装后，后端读取已安装的 metadata.yaml。已安装的 metadata.yaml.author/name 必须等于选中的 plugin_id。如果身份校验失败，安装必须失败。」 | 市场 JSON 规范 https://docs.astrbot.app/dev/plugin-market/2026-06-27.html | 市场安装/校验强依赖 metadata.yaml 的 author/name 与市场记录一致。 |

### 7.7 插件市场 JSON 规范（2026-06-27，版本 1）——市场源记录（plugins.json）要求

> 出处：https://docs.astrbot.app/dev/plugin-market/2026-06-27.html。该文档规范的是**插件市场源 JSON（registry）**，不是插件自身文件，但它定义了市场记录与 metadata.yaml 的一致性约束，发布时同样要满足。

| # | 要求 | 原文 | 解读 |
|---|---|---|---|
| 7.7.1 | 插件身份 `plugin_id = metadata.author + "/" + metadata.name`，须全局唯一 | 「plugin_id 定义为：metadata.author + "/" + metadata.name」「plugin_id 必须在 AstrBot 插件生态内全局唯一。」 | author 与 name 组合成全局身份。 |
| 7.7.2 | 市场记录 `author` / `name` / `version` 必须分别等于 metadata.yaml 中的对应字段 | 「author 必须等于 metadata.yaml.author。」「name 必须等于 metadata.yaml.name。」「version 必须匹配 metadata.yaml.version。」 | **一致性要求**：metadata.yaml 中这三项一旦发布即被当作事实来源。 |
| 7.7.3 | `author` 与 `name` 的约束 | 「必须是非空字符串。必须去除首尾空白。不得包含 /。不得包含 ASCII 控制字符。应该是稳定的包身份值，而不是展示名。」 | 身份字段禁止 `/`、控制字符、空白。 |
| 7.7.4 | `repo` 必须是上述三种 GitHub HTTPS URL 之一 | 「repo 必须是以下之一：https://github.com/{owner}/{repository}、https://github.com/{owner}/{repository}.git、https://github.com/{owner}/{repository}/tree/{branch}」「owner、repository、branch 必须匹配：[A-Za-z0-9_-]+」 | 允许 `.git` 与 `/tree/{branch}` 形式。 |
| 7.7.5 | `repo` 禁止类型 | 「repo 不得是：HTTP URL、SSH URL、非 GitHub URL、GitHub Enterprise URL、GitHub 文件、release、pull request、issue 或子目录 URL」 | 只能是 HTTPS GitHub 仓库级 URL。 |
| 7.7.6 | `repo` **不是插件身份** | 「repo 不得用作插件身份。root_dir_name、本地目录名、展示名、registry 名称不得用作插件身份。」 | — |
| 7.7.7 | 必填记录字段 | 「每个 PluginRecord 必须包含：author / name / version / repo / desc」 | 市场记录层面五字段必填。 |
| 7.7.8 | 可选字段 | display_name、short_desc、download_url、logo、tags、category、support_platforms、astrbot_version、social_link、updated_at、i18n、pinned、stars、download_count | — |
| 7.7.9 | 安装/更新身份校验 | 「已安装的 metadata.yaml.author/name 必须等于选中的 plugin_id。如果身份校验失败，安装必须失败。」 | — |
| 7.7.10 | 保留字段/弃用字段 | 不得在 PluginRecord 中使用 plugin_id、market_plugin_id、root_dir_name、local_plugin_name 等；`support_platform`、`platform` 已弃用，用 `support_platforms` 替代 | 面向市场源维护方。 |

> ⚠️ **发现一处官方内部不一致**（见第 8.2 节）：官方商店仓库的提交流单要求 `repo` 不要以 `.git` 结尾，而 2026-06-27 规范明确允许 `.git` 形式。

---

## 8. 官方插件商店仓库（AstrBot_Plugins_Collection）的实际提交流程

> 出处：官方插件商店仓库 https://github.com/AstrBotDevs/AstrBot_Plugins_Collection
> （发布页与市场规范的 $meta 示例均指向该仓库；仓库 README 的「How to submit a plugin?」直接跳转回 docs 发布页。）
> **此节内容来自仓库文件而非文档站**，作为流程/表单层证据补充。

| # | 来源文件 | 原文要点 | 解读 |
|---|---|---|---|
| 8.1 | `.github/ISSUE_TEMPLATE/PLUGIN_PUBLISH.yml`（商店提交流单） | 提交 JSON 字段：「{"name", "display_name", "desc", "author", "repo", "tags"(optional), "social_link"(optional)}」；`repo` 提示：「https://xxxx. **DO NOT end with `.git`**」 | 商店提交表单实际要求：JSON 含 name/display_name/desc/author/repo；tags、social_link 可选；repo 是 HTTPS 且不要以 `.git` 结尾；另需填写三个**必选勾选框**。 |
| 8.1b | 同上（必选勾选项） | 「My plugin has undergone thorough testing. (required)」「My plugin does not contain malicious code. (required)」「I have read and agree Code of Conduct. (required)」 | 提交流单层面的**合规承诺**：已充分测试、不含恶意代码、同意社区行为准则。 |
| 8.2 | `.github/workflows/validate_json.yml` | 校验 plugins.json 为合法 JSON（jq），并逐个 curl 检查 `repo` 可达性（不可达则 CI 失败） | 仓库 `repo` URL 必须真实可访问。 |
| 8.3 | `.github/workflows/validate-plugin-smoke.yml` | PR 修改 plugins.json 时对变更插件进行 smoke 校验（clone AstrBot → 装 requirements → 跑校验脚本生成 validation-report.json） | 新提交插件会经历自动 smoke test。 |

> ⚠️ **内部不一致确认**：提交流单（8.1）说 repo 「DO NOT end with `.git`」，而官方市场规范（7.7.4）明确允许 `https://github.com/{owner}/{repository}.git`。给插件作者的建议：**提交到商店的 repo 字段写不带 `.git` 的 HTTPS 仓库 URL 最为稳妥**（同时满足两边要求）。

---

## 9. AstrBot 源码层校验（补充证据，非文档正文）

> 出处：AstrBot 主仓库 https://github.com/AstrBotDevs/AstrBot （master）——`astrbot/core/star/updater.py`、`astrbot/core/star/star_manager.py`、`astrbot/core/star/star.py`。

| # | 校验 | 原文（源码） | 解读 |
|---|---|---|---|
| 9.1 | 元数据必填字段集合 | `PLUGIN_METADATA_REQUIRED_FIELDS = ("name", "desc", "version", "author")` | 加载时缺任一字段即报「缺少必需字段」；字段须为非空字符串。 |
| 9.2 | metadata 文件大小/编码 | `PLUGIN_METADATA_MAX_BYTES = 1024 * 1024`；「{filename} 必须使用 UTF-8 编码」「{filename} 格式错误」「{filename} 超过 1MB」 | metadata.yaml/.yml ≤1MB 且 UTF-8。 |
| 9.3 | `desc`/`description` 别名 | 「if "desc" not in normalized_metadata and "description" in normalized_metadata: …」 | 可用 `description` 代替 `desc`。 |
| 9.4 | `name` 的可导入性 | 「metadata 文件中 name 含有路径分隔符，不可用于 importlib 加载」「不是合法的模块名称（应为合法 Python 标识符且非关键字）」 | `name` 须是合法 Python 标识符。 |
| 9.5 | `astrbot_version` 解析 | `SpecifierSet(normalized_spec)`；失败提示「Invalid astrbot_version. Use a PEP 440 range, e.g. >=4.16,<5.」；`Version(VERSION)` 不满足范围则拒绝加载 | 与文档 2.4 一致。 |
| 9.6 | 配置 schema 校验 | 「插件配置 schema 必须使用 UTF-8 编码」「插件配置 schema 不是有效的 JSON」 | 见 3.11。 |
| 9.7 | `register` / `register_star` 装饰器已废弃 | `register_star` docstring：「[DEPRECATED] 该装饰器已废弃，将在未来版本中移除。在 v3.5.19 版本之后（不含），您不需要使用该装饰器…AstrBot 会自动识别继承自 Star 的类并将其作为插件类加载。」 | 新插件不依赖 `@register`；继承 `Star` 即自动识别（docs 最小实例也不使用）。 |
| 9.8 | 插件 i18n 文件限制 | 单个 i18n 文件 >1MB 跳过、非 JSON object 跳过、locale 名 ≤32 字符 | 与第 6 节文档要求呼应。 |

---

## 10. 开发原则（官方「原则/遵守」条目）

> 出处：https://docs.astrbot.app/dev/star/plugin.new.html（开发原则）与 https://docs.astrbot.app/dev/star/plugin.html（原则）。

| # | 原文 | 解读 |
|---|---|---|
| 10.1 | 「功能需经过测试。」 | 发布前测试（商店提交流单的必选勾选项亦要求）。 |
| 10.2 | 「需包含良好的注释。」 | 良好的注释；handler docstring 会被解析用于展示/文档（minimal 示例注释「这是 handler 的描述，将会被解析方便用户了解插件内容。非常建议填写。」）。 |
| 10.3 | 「持久化数据请存储于 data 目录下，而非插件自身目录，防止更新/重装插件时数据被覆盖。」 | 见 6.1。 |
| 10.4 | 「良好的错误处理机制，不要让插件因一个错误而崩溃。」 | 见 5.3。 |
| 10.5 | 「在进行提交前，请使用 ruff 工具格式化您的代码。」 | 提交前 ruff 格式化（文档级规范，非硬性 CI 校验）。 |
| 10.6 | 「不要使用 requests 库来进行网络请求，可以使用 aiohttp, httpx 等异步网络请求库。」 | 见 4.3。 |
| 10.7 | 「如果是对某个插件进行功能扩增，请优先给那个插件提交 PR 而不是单独再写一个插件（除非原插件作者已经停止维护）。」 | 生态协作规范。 |

---

## 11. 未能验证 / 未在文档中发现的项目

以下条目在**文档站全文和官方插件商店仓库**中均未找到明确要求。按任务约定，**不推测**，仅标记为「未能验证」：

| 项目 | 结论 | 说明 |
|---|---|---|
| 插件是否**必须有 README** | **未能验证**（文档未要求） | docs 正文未规定 README 格式；FAQ 仅在用户手动装依赖时提到「参考插件的 README」（https://docs.astrbot.app/faq.html ）。商店提交流单/市场规范均未将 README 列为必填。 |
| 插件是否**必须带 LICENSE 文件** | **未能验证**（文档未要求） | 文档无任何 LICENSE 条款；官方商店仓库根目录虽有 LICENSE 文件，但那是仓库自身的许可证（MPL 类），非对插件的强制要求。仅提交流单要求同意 GitHub「Code of Conduct」。 |
| `metadata.yaml` **是否有官方 JSON Schema / XSD** 规范文件 | **未能验证** | 文档只有示例 + 字段注释；市场 JSON 规范（2026-06-27）也是面向市场源而非 metadata.yaml 本身的 schema。 |
| 插件**实验（experimental/experiments）特性标记** | **文档中未发现** | 全站搜索「实验」无插件相关命中；无任何 experimental 字段要求。 |
| 插件**审核（review）通过标准清单**（除 16MB 与元数据校验外） | **未能验证** | 文档明确写出的「自动拒绝」条件只有 16MB 超限（CI/CD），其余审核维度未公开。商店仓库仅有 smoke validate + JSON 校验 + 可访问性校验工作流。 |
| 日志/异常处理的**强制规范**（如必须捕获异常、必须写错误日志） | **文档中未发现硬性条文** | 只有原则性条目（5.3「不要让插件因一个错误而崩溃」）与必须用 astrbot logger（5.1）。 |
| `requirements.txt` 是否**必填**（无第三方依赖时） | **文档未要求必填** | 文档/FAQ 的表述是「如果/如果你的插件需要依赖第三方库…请务必创建」。无依赖时可省略。 |
| `main.py` 之外是否可拆分模块 | 可（文档明确允许） | 「如果文件行数过长，可以将服务写在外部，然后在 Handler 中调用。」——handler 本体仍在 main.py 类中。 |
| 发布页「插件发布页面/plugins.astrbot.app」的表单字段与校验规则 | **未能抓取**（外部应用，需登录 AstrBot Cloud 账号） | 页面链接在发布页第 4 段；无法验证其表单侧要求，详见第 0 节。 |

---

## 12. 快速合规自查清单（Checklist 汇总）

### A. 文件结构
- [ ] 插件目录根目录有 `metadata.yaml`（或 `metadata.yml`），UTF-8、≤1MB
- [ ] 入口文件名为 `main.py`，插件类 `class MyPlugin(Star)` 继承 Star
- [ ] Handler 全部写在插件类内，前两个参数为 `self, event`
- [ ] 有第三方依赖时在插件根目录提供 `requirements.txt`
- [ ] 网络请求使用 aiohttp/httpx 等异步库，不用 requests
- [ ] 日志用 `from astrbot.api import logger`（或 `self.logger`），不用 logging
- [ ] 提交前 ruff 格式化；功能经测试；好的注释与错误处理

### B. metadata.yaml
- [ ] `name`：英文、唯一、合法 Python 标识符（无空格、无 `/`、非关键字），推荐 `astrbot_plugin_` 前缀
- [ ] `desc` 必填（非空字符串；可用 `description` 别名）
- [ ] `version` 必填，遵循语义化版本（建议纯 `X.Y.Z`，与发布页一致）
- [ ] `author` 必填，非空字符串
- [ ] `repo` 建议填写 HTTPS GitHub 仓库 URL（发布/market 层必须为合法 GitHub HTTPS URL）
- [ ] `display_name` 建议填写
- [ ] `short_desc` / `social_link` / `tags` 可选
- [ ] `astrbot_version`（可选）为 PEP 440 表达式且不带 `v` 前缀，如 `>=4.17.0`
- [ ] `support_platforms`（可选）值来自 ADAPTER_NAME_2_TYPE key 列表

### C. _conf_schema.json（如用配置）
- [ ] 文件名为 `_conf_schema.json`，合法 JSON、UTF-8
- [ ] 每个配置项有 `type`（唯一必填字段；受支持类型 string/text/int/float/bool/object/list/dict/template_list）
- [ ] `description`/`hint` 建议填写
- [ ] `_special` 只用 `select_provider`/`select_provider_tts`/`select_provider_stt`/`select_persona`/`select_knowledgebase`

### D. 数据与资源
- [ ] 持久化数据存 `data/`（不要写回插件目录）
- [ ] 大文件存 `data/plugin_data/{plugin_name}/`
- [ ] Logo（可选）`logo.png`，1:1，推荐 256x256
- [ ] 如不经由 _conf_schema：`pages/`、`skills/`、`.astrbot-plugin/i18n/` 按文档目录约定放置

### E. 发布
- [ ] 推送 GitHub 仓库；注册 AstrBot Cloud 账号，经官方发布页提交
- [ ] zip ≤ 16MB
- [ ] 仓库不含 `.git` / `__pycache__` / `node_modules` 等；建议根目录 `.gitignore`
- [ ] 商店提交（若走 issue 表单）repo 为 HTTPS 且不以 `.git` 结尾；勾选「已充分测试 / 不含恶意代码 / 同意 Code of Conduct」三项
- [ ] metadata.yaml 的 author/name/version 与商店记录一致（plugin_id = author/name 全局唯一）

---

## 附：本次研究未能访问/确认的资源

1. https://docs.astrbot.app/dev/ —— 404（无此目录页；不影响子页面采集）。
2. https://plugins.astrbot.app（AstrBot 插件发布页面）—— 外部 Web 应用，需登录，表单校验规则未验证。
3. 英文版文档（/en/dev/**/*）除发布页外未逐页核对（中文为文档主语言，本报告以中文为准）。
4. 官方插件商店仓库（AstrBot_Plugins_Collection）的 smoke 校验脚本 `scripts/validate_plugins/run.py` 具体校验断言未展开（仅确认其存在及工作流触发方式）。