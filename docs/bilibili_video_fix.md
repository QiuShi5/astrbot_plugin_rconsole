# B站视频只发图文不发视频修复报告

## 用户反馈

B站视频解析现在只发出图片和文字，没有发出视频。

## 根因

`ResolverService.resolve_bili()` 原流程：

1. 调 B站 view API 获取标题、UP、简介、封面；
2. 尝试 `yt-dlp` 提取视频直链；
3. 只有当 `yt-dlp` 文本中包含 `已提取` 时才把 `media_out.videos` 放入输出。

在当前环境中，B站 `yt-dlp` 经常返回：

```text
HTTP Error 412: Precondition Failed
```

因此 `videos=[]`，最终只剩封面图片和文字。

另外，即使拿到 B站远程直链，Matrix/AstrBot 适配器也可能因 B站防盗链、Referer/Cookie、远程 URL 访问限制而无法直接发送。

## 修复内容

新增 `services/bilibili_video.py`：

- 使用 B站官方 `x/player/playurl` API 获取播放地址；
- 使用 `cid` + `bvid` 获取 `durl`；
- 自动按清晰度降级尝试：`qn=64 → 32 → 16`；
- 优先选择不超过 `video_size_limit` 的视频；
- 用正确 `Referer` / `User-Agent` / 可选 `SESSDATA` 下载到插件本地 `data/temp`；
- 返回本地视频文件路径给 AstrBot `Video.fromFileSystem()`，避免远程直链防盗链导致适配器发送失败；
- 若用户通过 `#rbq/#rbs` 保存过 SESSDATA，会自动读取 `data/bilibili_auth.json` 作为 Cookie 来源。

更新 `services/resolver.py`：

- `yt-dlp` 成功时继续使用；
- `yt-dlp` 失败或无视频时，自动 fallback 到 B站原生 playurl + 本地下载；
- 输出文本中追加本地视频获取/下载状态。

## 验证

### 单元测试

```bash
python astrbot_plugin_rconsole/tests/test_bilibili_video.py
```

结果：

```text
bilibili video tests ok
```

覆盖：

- playurl 数据解析；
- 本地 mp4 文件输出；
- resolver 在 yt-dlp 关闭/失败时 fallback 到原生 B站视频服务；
- 输出 `ROutput.videos`。

### 真实 B站 playurl 轻量验证

使用公开 BVID：`BV1xx411c7mD`

```text
view_code 0 cid 62131 title 字幕君交流场所
best_qn 32 code 0 size_mb 55.17 durl_len 1
```

说明：B站官方 view/playurl API 可用；在默认 70MB 限制下，自动从 64 降级到 32 后找到约 55.17MB 的可下载视频。

## 使用建议

- 默认 `video_size_limit=70` 可发送较小 B站视频；
- 如果仍提示超过大小限制，可在插件配置中调大 `video_size_limit`；
- 如果视频需要登录/高权限内容，先使用 `#rbq` 扫码；扫码成功后插件会自动回填 `bilibili.sessdata` 与顶层 `bilibili_sessdata`，如设置页未立即显示可刷新页面或重载插件；
- Matrix 日志对视频链式消息可能仍显示 `Prepare to send -` 空白，但实际消息链会包含本地视频组件。
