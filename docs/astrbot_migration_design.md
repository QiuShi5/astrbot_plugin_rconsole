# AstrBot 插件骨架与迁移设计

> 对应 Goal Task 3。  
> 基于 `docs/astrbot_plugin_dev_notes.md` 与 `docs/rconsole_plugin_analysis.md`。

## 1. 产物目录

本轮建立 AstrBot 插件目录：

```text
astrbot_plugin_rconsole/
  main.py
  metadata.yaml
  requirements.txt
  _conf_schema.json
  services/
    __init__.py
  resources/
    config/
      help.yaml
      version.yaml
    html/
      help/
      version/
      pick-song/
      bili-info/
      netease/
      neteaseMusicInfo/
    img/
    font/
  data/
    README.md
  tests/
```

## 2. AstrBot 规范对应

| AstrBot 要求 | 当前实现 |
|---|---|
| 插件入口 `main.py` | 已创建 |
| 插件类继承 `Star` | `RConsolePlugin(Star)` |
| 构造函数接收 `Context` 与配置 | `__init__(self, context: Context, config: AstrBotConfig)` |
| 元数据 | `metadata.yaml` |
| 配置 schema | `_conf_schema.json` |
| 依赖声明 | `requirements.txt` |
| 资源目录 | 已复制原 R 插件 `resources/html`、`resources/img`、`resources/font` |
| 运行状态目录 | `data/README.md` 占位，后续实现 JSON 状态存储 |

## 3. 命令/事件迁移设计

### 3.1 命令类

已提供 AstrBot 显式命令：

- `/rhelp`，别名：`R帮助`、`r帮助`、`R插件帮助`、`R菜单`、`r菜单`
- `/rversion`，别名：`R版本`、`R插件版本`、`r版本`

这些命令当前为骨架占位，后续 Task 5/6 替换为真实帮助图、版本图。

### 3.2 原 R 插件正则兼容

`main.py` 中定义 `RuleSpec`，并在 `rconsole_dispatch()` 通过：

```python
@filter.event_message_type(filter.EventMessageType.ALL)
```

监听全部消息，读取 `event.message_obj.message_str`，对原 R 插件正则进行分发。

已覆盖来源模块：

- `apps/help.js`
- `apps/query.js`
- `apps/songRequest.js`
- `apps/switchers.js`
- `apps/tools.js`
- `apps/update.js`

已迁移规则类型：

- 帮助/版本；
- 查询类命令；
- 点歌/播放/云盘；
- 海外解析/白名单/清理；
- 翻译；
- 抖音、TikTok、Bilibili、Twitter/X、AcFun、小红书、波点、通用、YouTube、米游社、网易云、微博、微视、最右、Apple Music/Spotify、AI 总结、QQ 音乐、汽水音乐、Telegram、贴吧、小黑盒；
- 网易云/B 站登录状态类管理命令；
- R 插件更新命令。

## 4. 权限设计

原插件 `permission: 'master'` 迁移为 `RuleSpec.permission = 'admin'`。

后续实现策略：

1. 对明确管理功能使用 AstrBot 权限过滤或内部管理员校验；
2. 对通过统一分发入口匹配的管理功能，在 handler 内检查 `rule.permission`；
3. 不允许普通用户触发自更新、扫码登录、清理缓存、信任用户管理、云盘上传/清理等操作。

## 5. 配置 schema 设计

`_conf_schema.json` 已覆盖原 `config/tools.yaml` 核心配置，包含：

- 全局解析开关；
- 识别前缀；
- 全局黑名单；
- 图片分批阈值；
- 消息元素限制；
- 临时目录与视频大小限制；
- 代理配置；
- 视频编码与队列并发；
- Bilibili 配置；
- 网易云配置；
- 抖音配置；
- YouTube 配置；
- 小红书/微博/小黑盒 Cookie；
- AI 总结配置；
- 自更新允许开关。

敏感字段默认空，不写入任何真实密钥或 Cookie。

## 6. 资源与样式设计

已复制原 R 插件资源：

- 6 套 HTML/CSS 模板；
- `FZB.ttf` 与 `江城月湖体 400W.ttf`；
- 30 个功能图标；
- 原图片资源。

后续 Task 6 实现：

1. 使用 Python 模板引擎读取 `resources/html/*/*.html`；
2. 适配原模板变量：`pluResPath`、`version`、`helpData`、`songData`、`versionData` 等；
3. 使用 Playwright/Chromium 渲染截图；
4. 无浏览器环境时降级为文本或 Pillow 卡片，但记录样式一致性差异；
5. 与原 CSS 对照保留深色卡片、FZB 字体、`#FFBD73` 点缀色、圆角/阴影/双列帮助布局。

## 7. 安全与副作用设计

- 默认不执行 `#R插件更新` 的 git 操作，只返回手动更新提示；
- `allow_self_update=false` 为默认值；
- 下载、ffmpeg、yt-dlp、BBDown、Aria2、TDL 等后续实现必须在插件临时目录内运行，并设置超时；
- 清理垃圾只能清理插件受控临时目录，不扫描 AstrBot 全局数据目录；
- Cookie/API Key 只从 AstrBot 配置读取，不输出到日志或回复。

## 8. 后续实现拆分

| 后续任务 | 内容 |
|---|---|
| Task 4 | 检查 Task 1-3 文档、分析、骨架是否一致 |
| Task 5 | 实现核心功能：查询、开关、翻译、基础链接解析框架、点歌缓存等 |
| Task 6 | 实现 HTML/CSS 图片渲染和样式复刻 |
| Task 7 | 完善 README、配置说明、依赖、安装/运行说明 |
| Task 8 | 对功能/样式/文档进行综合 debug |
| Task 9 | 最终 review、修复、交付 |

## 9. 当前边界

本 Task 只要求建立可语法检查的骨架与设计文档，不声称已经完成全功能移植。占位 handler 会在后续 Task 替换为真实业务实现。
