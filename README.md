# R插件 AstrBot版

> 将 [R-console / R-plugin](https://github.com/zhiyu1998/rconsole-plugin)（Yunzai-Bot 插件）迁移为 AstrBot 插件的高复刻移植版。
> 目标是在 AstrBot 中复刻原 R 插件的命令入口、帮助菜单、查询工具、网易云点歌、链接解析入口、管理命令和深色卡片样式。

- 作者：dsh
- 仓库：https://github.com/QiuShi5/astrbot_plugin_rconsole.git
- 版本：0.3.12
- 兼容 AstrBot：`>=4.14,<5`

---

## 功能概览

本插件把原 R 插件的 `apps/`（6 个模块）与 `utils/`（30+ 平台解析文件）迁移为 AstrBot 的 Python 服务层，核心能力包括：

- 帮助菜单 / 版本卡片的图片化高复刻渲染（Pillow，无需浏览器）
- 查询类：医药查询、猫图、推荐软件、买家秀、Cos 图片
- 翻译：翻中/英/日/文/俄/韩
- 网易云点歌：搜索列表、听序号、直接播放、播客/声音类型
- 链接解析：20+ 平台的识别/信息提取/直链解析
- B 站扫码登录（`#rbq`/`#rbs`，带自动轮询回调）
- 管理：海外解析开关、R 信任用户白名单、清理临时目录
- 能力诊断：`#R能力诊断` 探测富媒体组件、适配器、Cookie、外部工具
- 安全策略：不在聊天命令中执行强制更新、任意删除、任意 shell 命令

---

## 安装方式

1. 将整个 `astrbot_plugin_rconsole` 文件夹复制到 AstrBot 插件目录，例如：

```text
data/plugins/astrbot_plugin_rconsole
```

2. 在 AstrBot 虚拟环境中安装依赖：

```bash
pip install -r requirements.txt
```

3. 重启 AstrBot，或在 WebUI「插件管理」中重载插件。

4. 在插件配置界面按需填写 `_conf_schema.json` 中的配置，例如网易云 API、平台 Cookie、代理地址等。

也可以直接从仓库安装（AstrBot WebUI 支持 Git/URL 安装时填写仓库地址）：

```text
https://github.com/QiuShi5/astrbot_plugin_rconsole.git
```

### 运行时依赖

- `PyYAML`：读取原插件 `help.yaml` / `version.yaml`
- `Pillow`：渲染帮助 / 版本 / 点歌图片卡片
- `yt-dlp`：YouTube / TikTok / Twitter/X / B站 / AcFun / 通用视频站元信息、缩略图、直链提取与下载
- `qrcode`：B 站扫码登录二维码生成

外部系统能力（如 `BBDown`、`ffmpeg`、`aria2`、`tdl`、`freyr`）不作为默认执行链；相关命令保留配置入口，避免在聊天中触发不可控外部副作用。可用 `#R能力诊断` 检查当前环境是否具备这些外部工具。

---

## 命令清单

### 帮助与版本

| 命令 | 功能 | 权限 |
|---|---|---|
| `/rhelp`、`#R帮助`、`R帮助`、`rhelp` | 输出 R 插件帮助菜单图片 | 所有用户 |
| `/rversion`、`#R版本`、`R版本`、`rversion` | 输出 R 插件版本卡片图片 | 所有用户 |
| `/rcap`、`#R能力诊断`、`rcap` | 输出能力诊断（组件/适配器/Cookie/外部工具） | 所有用户 |

### 查询类

| 命令 | 功能 |
|---|---|
| `#医药查询 关键词` | 医药/疾病/症状/医院/医生/药品查询 |
| `#cat` | 猫图（多图） |
| `#推荐软件` | 推荐 PC / Android 软件 |
| `#买家秀` | 淘宝买家秀图片 |
| `#累了` | Cos 图片 |

### 翻译

| 命令 | 功能 |
|---|---|
| `翻中 文本` / `翻英 文本` / `翻日 文本` / `翻韩 文本` / `翻俄 文本` / `翻文 文本` | 翻译为对应语言 |
| `trans英 文本` 等 | 兼容原 R 插件 trans 命令写法 |

### 网易云音乐

| 命令 | 功能 |
|---|---|
| `#点歌 关键词` | 搜索歌曲，输出点歌列表（图片+文本） |
| `#点歌 关键词 2` | 搜索播客/声音类型 |
| `#听1` | 播放当前会话点歌列表第 1 首（会话缓存） |
| `#播放 关键词` | 搜索并直接播放第一首 |
| `#网易云状态` / `#rns` | 网易云配置状态提示 |
| `#我的云盘` / `#rnc` | 保留入口（需 Cookie 与平台文件能力） |
| `#上传云盘` / `#rnu` | 保留入口，安全降级 |

### 酷狗音乐

| 命令 | 功能 |
|---|---|
| 酷狗分享链接（t1/m/share/h5） | 自动识别并解析酷狗音乐（OpenGraph 预览） |
| `#酷狗状态` / `#rks` | 酷狗 Cookie 配置状态提示 |
| `#rkq` / `#RKQ` | 酷狗扫码登录入口（能力诊断提示） |

### Bilibili

| 命令 | 功能 | 权限 |
|---|---|---|
| `#rbq` / `#RBQ` | 生成 B 站扫码登录二维码，并自动轮询扫码状态，成功/失败/过期/超时都会回调；登录成功后自动写入插件配置 | 管理员 |
| `#rbs` / `#RBS` | 手动查询最近一次二维码扫码状态；成功后保存 Cookie 到插件数据目录 | 管理员 |

B 站视频解析支持按配置 `bilibili.comments` 附带评论（纯文本，`bilibili.comment_count` 控制条数，默认 5）。

### 管理命令（管理员）

| 命令 | 功能 |
|---|---|
| `#设置海外解析` | 切换海外解析状态 |
| `清理垃圾` | 清理插件受控临时目录（仅限插件自己的 `data/temp`） |
| `#设置R信任用户 QQ号` / `#R信任用户` / `#查询R信任用户 QQ号` / `#删除R信任用户 QQ号` | R 信任用户白名单管理 |
| `#设置视频号Cookie <cookie>` | 保存微信视频号（腾讯元宝）Cookie，用于视频号解析 |

### 链接解析入口（所有用户）

发送链接即可自动识别并解析，覆盖平台：

- 抖音 / TikTok
- Bilibili / b23.tv / BV 号
- Twitter/X
- AcFun
- 小红书
- 波点音乐
- 快手 / 西瓜 / 皮皮虾 / 即刻等通用入口
- YouTube
- 米游社
- 网易云音乐
- 微博 / 微视 / 最右
- Instagram（需海外网络/代理，OpenGraph 预览）
- 酷狗音乐 / 酷狗状态 / 酷狗扫码
- 微信视频号
- Apple Music / Spotify
- QQ 音乐 / 汽水音乐
- Telegram / 贴吧 / 小黑盒
- `#总结一下 URL` / 微信公众号 / arXiv / GitHub / 知乎 / V2EX 等网页总结入口

实现说明：

- B 站基础信息、网易云歌曲信息、网页总结已实现可用解析。
- B 站短链会先展开到真实 BV；B 站视频在 `yt-dlp` 失败或触发 HTTP 412 时 fallback 到官方 `view/playurl` 并下载成本地视频文件发送。
- 抖音 `jingxuan/discover?modal_id=...` 按上游逻辑提取 `aweme_id`，需要时使用 Cookie 访问官方 detail API。
- 小红书按上游逻辑保留 `xsec_token/xsec_source` 并读取页面 `window.__INITIAL_STATE__`。
- 解析器只产出 `ROutput` 内容（平台无关），统一发送模块负责文本、图片、音频、视频、文件发送。
- 远程视频默认本地化为稳定 `.mp4` 后按 AstrBot Video 组件发送，避免签名参数被适配器误识别。
- 账号私密内容、群文件/群语音仍需真实适配器、Cookie 或外部工具授权；缺少能力时给出明确提示，不静默失败。
- 对话级白名单/黑名单会先于规则执行（支持 `unified_msg_origin`、session_id、群号，支持 `*` 通配符），并同步执行 AstrBot 全局白名单检查。

---

## 配置说明

配置文件：`_conf_schema.json`（AstrBot 自动生成 WebUI 配置面板）

| 配置组 | 说明 |
|---|---|
| `enable_link_resolvers` | 链接解析总开关 |
| `identify_prefix` | 识别前缀，例如：✅ 识别：哔哩哔哩 |
| `conversation_whitelist` / `conversation_blacklist` | 对话级白名单/黑名单（`*` 通配符） |
| `global_black_list` | 平台级黑名单（抖音、哔哩哔哩、TikTok 等） |
| `global_image_limit` / `image_batch_threshold` / `msg_element_limit` | 图片/消息分批策略 |
| `default_path` | 插件临时媒体目录（实际运行时限制在插件数据目录内） |
| `video_size_limit` / `video_download_timeout` / `video_send_timeout` | 视频大小与超时 |
| `video_codec` | 视频编码选择（auto/av1/hevc/avc） |
| `queue_concurrency` / `video_download_concurrency` | 下载队列并发数 / 视频下载线程数 |
| `autoclear_cron` | 自动清理时间（沿用 R 插件 cron 语义） |
| `proxy_addr` / `proxy_port` / `force_overseas_server` | 海外平台代理 |
| `bilibili` | B 站 SESSDATA、扫码轮询、画质、封面/简介/总结、是否显示原始链接、`comments`/`comment_count` 评论开关；顶层 `bilibili_sessdata` 为兼容字段 |
| `netease` | 网易云 API、Cookie、音质、点歌数量等 |
| `douyin` | 抖音 Cookie、时长、封面、`comments`/`comment_count` 评论开关、BGM 策略 |
| `youtube` | YouTube 画质、时长、Cookie 路径 |
| `ytdlp` | 通用媒体解析模式：`off` 关闭 / `metadata` 仅信息 / `direct` 提取直链 / `download` 下载到临时目录；`enabled` 总开关 |
| `cookies` | 小红书、微博、小黑盒等平台 Cookie；`weibo_comments`/`weibo_comment_count` 控制微博评论展示 |
| `ai` | OpenAI-compatible 总结配置（base_url / api_key / model） |

配置字段命名保持稳定，避免后续版本重命名导致用户已填写配置丢失。新版 AstrBot 会自动为缺失配置项补默认值、移除已删除项。

---

## 样式复刻说明

原 R 插件使用 HTML/CSS + Puppeteer 渲染图片。AstrBot 部署环境未必包含 Chromium，因此本插件采用 Pillow 复刻核心卡片（原 HTML/CSS 资源仍保留在 `resources/html/` 供追溯）：

- 帮助菜单：深灰背景、FZB 字体、`#FFBD73` 标题/边框、双列功能卡、图标、页脚
- 版本卡片：深色版本卡、标题栏、更新项列表（版本卡片数据复刻原版 R 插件的 `resources/config/version.yaml`，展示的是原版版本号与更新日志）
- 点歌列表：网易云深色列表、序号、封面、歌手、时长、播客/云盘标签

样式复刻基于原 R 插件的 HTML/CSS/字体/图标资源（`resources/`），核心聊天图片用 Pillow 渲染。

---

## 目录结构

```text
astrbot_plugin_rconsole/
  main.py                  # AstrBot 插件入口与 46 条运行规则分发（+1 条按策略移除的更新入口）
  metadata.yaml            # 插件元信息
  _conf_schema.json        # 配置 schema
  requirements.txt         # Python 依赖
  logo.png                 # 插件图标（500x500，1:1）
  README.md                # 本文档
  services/                # 业务服务
    common.py              # ROutput 结构、HTTP 请求、配置读取工具
    paths.py               # AstrBot 持久化数据目录解析与旧数据迁移
    state.py               # 状态/白名单/点歌缓存/清理临时目录
    query.py               # 医药/猫图/软件/买家秀/Cos 查询
    translate.py           # 翻译服务
    netease.py             # 网易云点歌/播放
    resolver.py            # 平台链接识别与解析分发
    media_downloader.py    # yt-dlp 媒体解析/下载
    bilibili_auth.py       # B 站扫码登录
    bilibili_video.py      # B 站 playurl 提取与本地下载
    capabilities.py        # #R能力诊断
    help_version.py        # 帮助/版本数据服务
    card_renderer.py       # Pillow 卡片渲染
    output_sender.py       # 统一输出发送（组件链/降级）
  resources/               # 原 R 插件资源
    config/                # help.yaml / version.yaml
    html/                  # 6 套原 HTML/CSS 模板
    img/                   # 30 个平台图标 + 默认图
    font/                  # FZB.ttf、江城月湖体
  tests/                   # 沙箱测试脚本
  data/                    # 运行时数据（写入 AstrBot 持久化目录；迁移旧数据用）
```

---

## 数据持久化

插件运行时数据写入 AstrBot 官方持久化目录：

```text
data/plugin_data/astrbot_plugin_rconsole/
```

包括 `state.json`、`whitelist.json`、点歌/搜索缓存、`bilibili_auth.json`。因此在 AstrBot 插件管理中卸载插件时，只要不勾选「删除数据目录」，重装后会继续读取这些数据。

- 首次启动时会从旧安装目录内的 `data/` 复制已有 JSON 数据到 `plugin_data`，不删除旧数据。
- 视频下载缓存与渲染图片位于同一持久根下的 `temp/`、`rendered/`，可通过 `清理垃圾` 清理过期临时文件。

---

## 安全与兼容性

- 不在聊天命令中执行危险的强制更新、任意删除、任意 shell 命令（原插件的聊天内 git 更新入口已按产品要求移除）。
- `清理垃圾` 只清理插件自己的受控临时目录。
- 涉及 Cookie、账号、扫码、群文件/群语音等平台强耦合能力时，缺少授权或适配器能力会明确提示；公开视频/音频解析优先走 `yt-dlp` 真实提取链。
- 图片/音频/视频发送依赖 AstrBot 当前适配器能力；发送失败时降级为文本链接。
- OneBot11/aiocqhttp/NapCat/Lagrange 等保守实现会把文字+图片合并为一条消息，视频/音频/文件独立发送。

---

## 开发与验证

版本管理遵循 AstrBot 官方规范：入口 `main.py`、插件类继承 `Star`、日志用 `astrbot.api.logger`（注：`services/resolver.py` 目前含标准库 logging 兜底，属已知待清理项）、持久化写入 `data/plugin_data/`、发布 zip 不超过 16MB。

本插件携带了完整测试与文档：

- `tests/test_core_services.py`：核心服务冒烟
- `tests/test_astrbot_stub_e2e.py`：AstrBot API stub 端到端（命令分发、权限、富媒体、降级）
- `tests/test_media_resolvers.py`、`tests/test_bilibili_*.py`：解析器与 B 站链路
- `tests/test_style_quantitative.py`：样式量化检查
- `tests/test_persistent_data_path.py`：持久化路径
- `tests/test_capability_probe.py`、`tests/test_runtime_adapter_probe.py`：能力/运行时探针
- `tests/generate_full_parity_matrix.py`：自动生成原插件→AstrBot 规则对照矩阵（运行 `python tests/generate_full_parity_matrix.py` 生成）

在无完整 AstrBot 运行环境时：

```bash
python -m py_compile main.py services/*.py tests/*.py
python tests/test_core_services.py
python tests/test_astrbot_stub_e2e.py
```

真实 WebUI/适配器端到端加载需要在你的 AstrBot 实例中验证；`#R能力诊断` 可辅助检查前置条件。

---

## 致谢与许可

本项目是 [rconsole-plugin](https://github.com/zhiyu1998/rconsole-plugin)（Mulan PSL-2.0）的 AstrBot 移植版，保留了原项目的资源与样式语言。