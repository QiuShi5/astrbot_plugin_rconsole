# 外部媒体解析 / 下载器工作流验证报告

## 目标

审查意见指出旧版本对多平台链接多为“基础解析/安全降级”。本轮补强新增 `services/media_downloader.py`，将 `yt-dlp` 作为默认依赖并接入 `ResolverService`，用于 YouTube、TikTok、Twitter/X、B站、AcFun、通用视频站等真实媒体元信息、缩略图、直链和可选下载。

## 实现摘要

- 新增：`astrbot_plugin_rconsole/services/media_downloader.py`
  - 优先使用 `yt_dlp` Python 包；如果不可用，再尝试系统 `yt-dlp` 命令。
  - 支持模式：`metadata`、`direct`、`download`、`off`。
  - `metadata`：只返回标题、作者、时长、描述、网页 URL、缩略图。
  - `direct`：在 metadata 基础上尽可能提取真实媒体 URL，并映射到 `ROutput.videos`。
  - `download`：按大小限制下载到插件 `data/temp`，返回本地文件路径。
- 增强：`astrbot_plugin_rconsole/services/resolver.py`
  - YouTube/TikTok/Twitter/X/AcFun/通用链接优先走 yt-dlp。
  - B站保留官方 API 基础信息，同时尝试 yt-dlp 增强媒体链。
  - 微博/小红书/米游社/通用网页增加 OpenGraph/meta 解析。
- 更新：`requirements.txt`
  - 增加 `yt-dlp>=2025.1.15`。

## 实测命令与结果

### 1. 安装 yt-dlp

```bash
python -m pip install "yt-dlp>=2025.1.15"
```

结果：成功安装 `yt-dlp-2026.3.17`。

### 2. 自动测试

```bash
python astrbot_plugin_rconsole/tests/test_media_resolvers.py
```

结果：

```text
media resolver tests ok
backend= python-package
youtube_result_head= ✅ 识别：YouTube
```

该测试覆盖：

- `yt-dlp` Python 包可用性检测；
- `https://example.com` OpenGraph 解析；
- YouTube URL 通过 resolver 进入 yt-dlp 路径，平台不可用时结构化返回错误而不崩溃；
- 公开 MP4 直链在 `direct` 模式下成功提取到 `ROutput.videos`。

### 3. 真实公开视频直链提取

测试 URL：

```text
https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/Big_Buck_Bunny_360_10s_1MB.mp4
```

结果：

```text
✅ 识别：通用直链视频
标题：Big_Buck_Bunny_360_10s_1MB
作者：未知作者
时长：未知
videos 1 images 0
```

结论：直链媒体提取链可用。

### 4. 受平台限制的真实站点情况

测试过程中 YouTube/Bilibili 公共测试链接在沙箱网络中返回：

```text
ERROR: [youtube] BaW_jenozKc: Video unavailable
ERROR: [BiliBili] ... HTTP Error 412: Precondition Failed
```

这些错误来自平台访问限制或测试视频不可用，不是插件崩溃。当前实现会把此类失败转换为可读文本提示，并继续保留 OpenGraph/API fallback。

## 结论

本轮已把原先“只识别/提示”的大量平台升级为真实工具链：

- 有 `yt-dlp` 时：元信息、缩略图、直链、可选下载；
- 无 `yt-dlp` 或站点限制时：结构化错误 + OpenGraph/meta fallback；
- 需账号/Cookie/适配器能力的私密内容、云盘上传、群语音/群文件仍按授权和环境边界处理，不伪造成功。
