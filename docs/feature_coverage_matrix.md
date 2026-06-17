# R插件 AstrBot版功能覆盖矩阵

| 原 R 插件模块 | 原功能 | AstrBot 版状态 | 实现/降级说明 | 验证方式 |
|---|---|---|---|---|
| `apps/help.js` | R帮助菜单 | 已实现 | 读取 `help.yaml`，Pillow 生成复刻帮助图 | 样例图生成 + 尺寸检查 |
| `apps/update.js` | R版本 | 已实现 | 读取 `version.yaml`，Pillow 生成版本卡片 | 样例图生成 + 尺寸检查 |
| `apps/update.js` | R插件更新/强制更新 | 安全降级 | 默认禁用聊天内 git 更新，提示手动更新 | 静态逻辑检查 |
| `apps/query.js` | `#医药查询` | 已实现 | 使用 dayi API，保留原输出文案格式 | 服务测试/外部接口可选 |
| `apps/query.js` | `#cat` | 已实现 | 使用 shibe/thecatapi 图片接口 | 服务测试/外部接口可选 |
| `apps/query.js` | `#推荐软件` | 已实现 | 使用 ghxi 页面/API 降级提取 | 服务测试/外部接口可选 |
| `apps/query.js` | `#买家秀` | 已实现 | 使用图片接口返回 URL | 服务测试/外部接口可选 |
| `apps/query.js` | `#累了` | 已实现 | 使用 cos 图片接口 | 服务测试/外部接口可选 |
| `apps/songRequest.js` | `#点歌` | 已实现 | 网易云 API 搜索 + 会话缓存 + 图片列表 | 单元测试 + 样式样例 |
| `apps/songRequest.js` | `#听N` | 已实现 | 按会话缓存播放/链接降级 | 单元测试 |
| `apps/songRequest.js` | `#播放` | 已实现 | 搜索第一首并获取播放链接 | 代码路径检查 |
| `apps/songRequest.js` | 云盘/上传 | 环境依赖/入口完整 | 需要账号 Cookie、文件上传、平台语音/文件能力；已增加 `#R能力诊断` 检测 Cookie/API/ffmpeg/适配器组件 | 能力诊断测试 + 配置检查 |
| `apps/switchers.js` | 海外解析开关 | 已实现 | 本地 `state.json` 持久化 | 单元测试 |
| `apps/switchers.js` | R信任用户管理 | 已实现 | `whitelist.json` 增删查 | 单元测试 |
| `apps/switchers.js` | 清理垃圾 | 已实现 | 仅清理插件 `data/temp`，不碰全局目录 | 代码检查 |
| `apps/tools.js` | 翻译 | 已实现 | MyMemory 公共接口，支持原命令 | 单元测试 |
| `apps/tools.js` | Bilibili 解析 | 已实现增强 | BVID 详情、标题、UP、简介、封面；短链先展开到真实 BV；优先 yt-dlp 提取媒体，失败或 HTTP 412 时 fallback 到官方 view/playurl 并下载成本地视频文件发送 | 单元测试 + 媒体解析测试 + B站 playurl/短链 fallback 轻量验证 |
| `apps/tools.js` | B站扫码/状态 | 已实现增强 | `#rbq/#RBQ` 调用 B站二维码接口并生成 QR 图片，随后自动后台轮询扫码状态，成功/二维码失效/查询失败/超时都会主动回调；`#rbs/#RBS` 保留手动查询；成功后保存 Cookie 到 AstrBot `data/plugin_data/astrbot_plugin_rconsole/`，并自动回填运行时与持久插件配置 `bilibili.sessdata`、顶层兼容字段 `bilibili_sessdata`；若设置页缓存未立即刷新，刷新页面或重载插件即可看到新值 | `test_bilibili_auth.py` + `test_astrbot_stub_e2e.py` + `test_persistent_data_path.py` + schema 检查 |
| `apps/tools.js` | 网易云链接解析 | 已实现增强 | 解析歌曲 ID、标题、歌手、专辑、封面，并尝试获取播放链接 | 代码路径检查 + 服务测试 |
| `apps/tools.js` | AI 总结 | 已实现基础 | 读取网页文本、提取标题并摘要截断；可后续接 OpenAI-compatible API 做 LLM 摘要 | 单元测试 |
| `apps/tools.js` | YouTube/TikTok/Twitter/X/AcFun/B站/通用视频站 | 已实现增强 | 通过 `yt-dlp` Python 包提取真实元信息、缩略图、直链；`download` 模式可下载到插件临时目录 | `test_media_resolvers.py` + 直链媒体实测 |
| `apps/tools.js` | 小红书/微博/米游社/Telegram/Apple Music/Spotify/QQ音乐等网页型平台 | 已实现元信息解析 | 通过 OpenGraph/页面 meta 提取标题、简介、封面/视频字段；账号私密内容需 Cookie | OpenGraph 测试 + 规则覆盖 |
| `apps/tools.js` | 扫码登录/云盘上传/群文件/群语音 | 环境依赖/入口完整 | 命令入口、配置项和提示完整；新增 `#R能力诊断` 可检测 AstrBot 富媒体组件、适配器名、Cookie、ffmpeg/BBDown/tdl/aria2c；真实执行依赖 AstrBot 适配器、账号 Cookie 和用户授权 | `test_capability_probe.py` + runtime adapter probe |
| 运行时发送层 | 富媒体跨协议发送 | 已实现增强 | 解析器统一产出 `ROutput`，`services/output_sender.py` 负责发送；Matrix 等平台优先链式消息；OneBot11/aiocqhttp/NapCat/Lagrange 等保守实现自动合并文字+图片为一条消息，视频/音频/文件独立按 AstrBot 组件发送；本地视频发送前校验文件存在，远程视频默认由发送模块下载为稳定 `.mp4` 后发送；最终才兜底为可见文本 | stub E2E + 真实组件探针 |
| `resources/html/*` | HTML/CSS 样式 | 已保留/复刻 | 原资源完整复制，核心卡片由 Pillow 生成 | 资源检查 + 样例图 |
| `config/*.yaml` | 帮助/版本配置 | 已迁移 | 复制到 `resources/config/` 并被服务读取 | 文件检查 |
| `model/utils/constants` | 公共能力 | 部分等价重写 | Python 服务模块替代 Node/Yunzai/Redis/Puppeteer 依赖 | py_compile + tests |

## 说明

“全功能迁移”在 AstrBot 语境下分为三类：

1. **可直接平台无关实现**：已实现，如帮助、版本、查询、翻译、点歌缓存、B站/网易云信息、OpenGraph 网页解析、白名单等。
2. **可通过通用媒体工具链实现**：已接入 `yt-dlp` Python 包，覆盖 YouTube/TikTok/Twitter/X/B站/AcFun/通用视频站元信息、缩略图、直链与可选下载。
3. **依赖账号、Cookie 或 AstrBot 具体适配器能力**：保留配置和入口，如群文件上传、群语音、扫码登录、网易云云盘上传、BBDown/tdl/freyr/ffmpeg/aria2 专用下载链。默认不在聊天中触发危险或不可控外部副作用；用户提供真实环境和授权后可继续开启增强链。
