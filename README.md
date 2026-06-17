# R插件 AstrBot版

> 将 [R-console / R-plugin](https://gitee.com/kyrzy0416/rconsole-plugin.git) 迁移为 AstrBot 插件的高复刻版本。目标是在 AstrBot 中复刻原 R 插件的命令入口、帮助菜单、查询工具、网易云点歌、链接解析入口、管理命令和深色卡片样式。

## 迁移完成度

本仓库已完成以下迁移工作：

- 已整理 AstrBot 插件开发要点：`docs/astrbot_plugin_dev_notes.md`
- 已分析原 R 插件源码与功能映射：`docs/rconsole_plugin_analysis.md`
- 已完成 AstrBot 插件骨架：`metadata.yaml`、`main.py`、`_conf_schema.json`、`requirements.txt`
- 已保留原 R 插件 HTML/CSS/图标/字体/配置资源
- 已实现 46 条运行规则映射；聊天内插件更新入口已移除，版本卡片入口保留
- 已实现核心服务：查询、翻译、网易云点歌、链接解析、白名单、海外解析切换、清理临时目录
- 已实现帮助菜单、版本卡片、点歌列表的图片化高复刻渲染
- 已接入 `yt-dlp` 通用媒体解析链：YouTube、TikTok、Twitter/X、B站、AcFun、通用视频站等可提取真实元信息/缩略图/直链，按配置可下载到插件临时目录；对仍需账号/Cookie 或平台强耦合的能力提供明确提示

## 安装方式

1. 将整个 `astrbot_plugin_rconsole` 文件夹复制到 AstrBot 的插件目录，例如：

```text
data/plugins/astrbot_plugin_rconsole
```

2. 在 AstrBot 虚拟环境中安装依赖：

```bash
pip install -r requirements.txt
```

3. 重启 AstrBot 或在管理面板重新加载插件。

4. 在 AstrBot 插件配置界面按需填写 `_conf_schema.json` 中的配置，例如网易云 API、平台 Cookie、代理地址等。

## 最小依赖

当前运行时核心依赖：

- `PyYAML`：读取原插件 `help.yaml/version.yaml`
- `Pillow`：渲染帮助、版本、点歌图片卡片

默认媒体解析链：

- `yt-dlp`：YouTube/TikTok/Twitter/X/B站/AcFun/通用视频站元信息、缩略图、直链提取；配置为 `download` 模式时可下载到插件临时目录

仍属于外部系统能力的工具如 `BBDown`、`ffmpeg`、`aria2`、`tdl`、`freyr` 不作为默认执行链；相关命令保留配置入口，避免在聊天中触发不可控外部副作用。

## 命令清单

### 帮助与版本

| 命令 | 功能 |
|---|---|
| `#R帮助` / `R帮助` / `rhelp` | 输出 R 插件帮助菜单图片 |
| `#R版本` / `R版本` / `rversion` | 输出 R 插件版本卡片图片 |

### 查询类

| 命令 | 功能 |
|---|---|
| `#医药查询 关键词` | 医药/疾病/症状/医院/医生/药品查询 |
| `#cat` | 猫图 |
| `#推荐软件` | 推荐软件 |
| `#买家秀` | 买家秀图片 |
| `#累了` | cos/图片接口 |

### 翻译

| 命令 | 功能 |
|---|---|
| `翻中 文本` | 翻译为中文 |
| `翻英 文本` | 翻译为英文 |
| `翻日 文本` | 翻译为日文 |
| `翻韩 文本` | 翻译为韩文 |
| `翻俄 文本` | 翻译为俄文 |
| `翻文 文本` | 自动/通用翻译 |
| `trans英 文本` | 兼容原 R 插件 trans 命令 |

### 网易云音乐

| 命令 | 功能 |
|---|---|
| `#点歌 关键词` | 搜索歌曲并输出复刻点歌列表图片 |
| `#点歌 关键词 2` | 搜索播客/声音类型 |
| `#听1` | 播放当前会话点歌列表第 1 首 |
| `#播放 关键词` | 搜索并直接播放第一首 |
| `#网易云状态` / `#rns` / `#RNS` | 网易云配置状态提示 |
| `#我的云盘` / `#rnc` / `#RNC` | 保留入口，需 Cookie 与平台文件能力 |
| `#上传云盘` / `#rnu` / `#RNU` | 保留入口，安全降级 |

### Bilibili 登录/状态

以下命令需要管理员权限：

| 命令 | 功能 |
|---|---|
| `#rbq` / `#RBQ` | 生成 B站扫码登录二维码，并自动轮询扫码状态，成功/失败/过期/超时都会回调；登录成功后自动写入插件配置 |
| `#rbs` / `#RBS` | 手动查询最近一次二维码扫码状态；成功后保存 Cookie 到插件数据目录，并自动回填 `bilibili.sessdata` 与顶层 `bilibili_sessdata` |

### 管理命令

以下命令需要管理员权限：

| 命令 | 功能 |
|---|---|
| `#设置海外解析` | 切换海外解析状态 |
| `清理垃圾` | 清理插件受控临时目录 |
| `#设置R信任用户 QQ号` | 添加信任用户 |
| `#R信任用户` | 查看信任用户 |
| `#查询R信任用户 QQ号` | 查询信任用户 |
| `#删除R信任用户 QQ号` | 删除信任用户 |

### 链接解析入口

已迁移并保留以下平台识别规则：

- 抖音 / TikTok
- Bilibili / b23.tv / BV号
- Twitter/X
- AcFun
- 小红书
- 波点音乐
- 快手 / 西瓜 / 皮皮虾 / 即刻等通用解析入口
- YouTube
- 米游社
- 网易云音乐
- 微博
- 微视
- 最右
- Apple Music / Spotify
- QQ 音乐
- 汽水音乐
- Telegram
- 贴吧
- 小黑盒
- `#总结一下 URL` / 公众号 / arXiv / GitHub / 知乎 / V2EX 等网页总结入口

- `#R能力诊断` / `/rcap`：检测 AstrBot 富媒体组件、当前适配器、Cookie、ffmpeg/BBDown/tdl/aria2c 等环境依赖，用于验证扫码、云盘、群文件/语音等强耦合能力前置条件

其中 Bilibili 基础信息、网易云歌曲信息、网页总结已实现可用解析；B站短链会先展开到真实 BV，B站视频在 `yt-dlp` 失败或触发 HTTP 412 时会 fallback 到官方 `view/playurl` 并下载成本地视频文件发送；抖音 `jingxuan/discover?modal_id=...` 会按上游 R 插件逻辑提取 `aweme_id` 并在需要时使用 Cookie 访问官方 detail API；小红书会按上游逻辑保留 `xsec_token/xsec_source` 并读取页面 `window.__INITIAL_STATE__`。解析器只产出 `ROutput` 内容，统一发送模块负责文本、图片、音频、视频和文件发送；远程视频默认在发送模块中下载为本地稳定 `.mp4` 后按 AstrBot Video 组件发送，避免签名参数被适配器误识别为 `mp4sign...` 这类错误后缀。发送层遵循 AstrBot 标准组件链路：普通适配器优先一条富媒体链，OneBot11/aiocqhttp/NapCat/Lagrange 等保守实现会把文字+图片合并为一条消息，视频/音频/文件独立按 AstrBot 组件发送；入口会记录规则命中、禁用/黑名单、抖音/小红书解析路径、B站 fallback、媒体输出数量和视频本地化结果，并在可读取 AstrBot 全局白名单配置时同步执行会话白名单检查。账号私密内容、群文件/群语音仍需真实适配器、Cookie 或外部工具授权。

## 配置说明

配置文件：`_conf_schema.json`

主要配置组：

- `enable_link_resolvers`：链接解析总开关
- `global_black_list`：平台黑名单
- `global_image_limit` / `image_batch_threshold` / `msg_element_limit`：图片和消息分批策略
- `video_size_limit`：视频大小限制
- `proxy_addr` / `proxy_port`：海外平台代理
- `bilibili_sessdata`：顶层兼容字段，填写哔哩哔哩 SESSDATA；如果 AstrBot UI 未展开嵌套配置，优先在这里填写
- `bilibili_qr_auto_poll` / `bilibili_qr_poll_interval` / `bilibili_qr_poll_timeout`：`#rbq` 扫码登录自动回调开关、轮询间隔和超时时间
- `bilibili`：B站 SESSDATA、扫码轮询、画质、封面/简介/总结、是否显示原始链接等配置
- `netease`：网易云 API、Cookie、音质、点歌数量等配置
- `douyin`：抖音 Cookie、时长、封面、评论、BGM 策略、是否显示原始链接
- `youtube`：YouTube 画质、时长、Cookie 路径、是否显示原始链接
- `ytdlp`：通用媒体解析模式，`metadata` 仅信息、`direct` 提取直链、`download` 下载到临时目录
- 发送策略：解析器只产出 `ROutput`，统一发送模块按 AstrBot 组件发送；远程视频会先稳定化为本地 `.mp4`，是否转文件或保留预览由 AstrBot 适配器处理
- `cookies`：小红书、微博、小黑盒等平台 Cookie，以及这些平台是否显示原始链接
- `ai`：OpenAI-compatible 总结配置

- `docs/full_original_to_astrbot_parity_matrix.md`：原 R 插件入口到 AstrBot handler 的映射与证据
- `docs/full_parity_verification_summary.md`：完整功能/样式 parity 验证总表
- `docs/astrbot_runtime_adapter_validation.md`：真实 AstrBot CLI、Web 服务启动、富媒体组件和适配器能力探针

## 样式复刻说明

原 R 插件使用 HTML/CSS + Puppeteer 渲染图片。AstrBot 部署环境未必包含 Chromium，因此本插件采用 Pillow 复刻核心卡片：

- 帮助菜单：深灰背景、FZB 字体、`#FFBD73` 标题/边框、双列功能卡、图标、页脚
- 版本卡片：深色版本卡、标题栏、更新项列表
- 点歌列表：网易云深色列表、水印、序号、封面、歌手、时长、云盘/播客标签

样式对照记录见：`docs/style_replication_report.md`；量化检查见：`docs/visual_comparison_report.md` 和 `docs/style_quantitative_check.json`。

## 安全与兼容性

- 不在聊天命令中执行危险的强制更新、任意删除、任意 shell 命令。
- `清理垃圾` 只清理插件自己的 `data/temp`。
- 涉及 Cookie、账号、扫码、群文件/群语音等平台强耦合能力时，会在缺少授权或适配器能力时明确提示；公开视频/音频解析优先走 `yt-dlp` 真实提取链。
- 图片/音频/视频发送依赖 AstrBot 当前适配器能力；发送失败时会使用文本链接降级。

## 目录结构

```text
astrbot_plugin_rconsole/
  main.py                  # AstrBot 插件入口与 46 条运行规则分发
  metadata.yaml            # 插件元信息
  _conf_schema.json        # 配置 schema
  requirements.txt         # Python 依赖
  logo.png                 # 插件图标
  services/                # 业务服务
    common.py
    state.py
    query.py
    translate.py
    netease.py
    resolver.py
    media_downloader.py
    bilibili_auth.py
    capabilities.py
    help_version.py
    card_renderer.py
  resources/               # 原 R 插件资源与配置
    config/
    html/
    img/
    font/
  data/                    # 仅保留说明；运行时持久数据写入 AstrBot data/plugin_data/astrbot_plugin_rconsole
  tests/                   # 沙箱验证脚本
```

## 数据持久化

插件运行时数据默认写入 AstrBot 官方持久化目录：`data/plugin_data/astrbot_plugin_rconsole/`，包括 `state.json`、`whitelist.json`、点歌/云盘缓存和 `bilibili_auth.json`。因此在 AstrBot 插件管理中卸载插件时，只要不勾选删除数据目录，重新安装后会继续读取这些数据。

为兼容旧版本，插件首次启动时会从旧安装目录内的 `data/` 复制已有 JSON 数据到 `plugin_data`；不会删除旧数据。视频下载缓存与渲染图片位于同一持久根下的 `temp/`、`rendered/`，可通过 `清理垃圾` 清理过期临时文件。

## 验证方式

开发时已使用以下验证：

```bash
python -m py_compile main.py services/*.py
python tests/test_core_services.py
python tests/test_astrbot_stub_e2e.py
python ../../scripts/build_package.py
```

此外已生成帮助/版本/点歌图片样例并检查尺寸和资源完整性；发布包已验证小于 16MB。真实 AstrBot WebUI/适配器端到端加载需要在你的 AstrBot 实例中完成，插件已提供 stub 端到端测试作为无 AstrBot 服务进程环境下的最强替代证据。
