# B站短链与 yt-dlp 412 fallback 修复

## 问题

用户提供的运行日志中，B站短链：

```text
https://b23.tv/vQMt0c5
```

被识别为哔哩哔哩后，直接返回：

```text
yt-dlp 解析失败：ERROR: [BiliBili] 1HsovBGETx: Unable to download JSON metadata: HTTP Error 412
```

复现确认：

- `b23.tv/vQMt0c5` 会跳转到 `BV1HsovBGETx`；
- 该视频本身不是不可解析；B站官方 `view`/`playurl` API 可返回 metadata 和 MP4 播放地址；
- 失败点是 `yt-dlp` 页面解析触发 B站 `HTTP 412` 后，旧逻辑没有继续进入 B站官方 API fallback。

## 修复

### 1. 短链先展开

`ResolverService.resolve_bili()` 现在会对 B站短链/移动端链接先带 UA/Referer 展开：

```text
b23.tv / bili2233.cn -> www.bilibili.com/video/BV...
```

展开后再提取 BVID。

### 2. yt-dlp 失败后继续官方 API fallback

新逻辑：

```text
短链/直链 -> 提取 BVID -> view API 获取 title/cid -> yt-dlp 尝试 -> 失败/关闭/未安装时走官方 playurl -> 下载本地视频 -> 发送真实视频
```

因此 `HTTP 412` 不再直接成为最终回复。

### 3. 运行日志增强

新增关键阶段日志：

- 命中规则：rule、handler、source module；
- 权限拦截；
- `enable_link_resolvers=false` 或 `global_black_list` 命中；
- B站短链展开；
- BVID/CID/title；
- yt-dlp 成功/失败；
- 官方 playurl fallback 成功/失败；
- 输出媒体数量。

### 4. AstrBot 全局白名单入口保护

插件入口会在可读取 AstrBot 运行时配置时同步检查：

```text
platform_settings.enable_id_white_list
platform_settings.id_whitelist
platform_settings.wl_ignore_admin_on_group
platform_settings.wl_ignore_admin_on_friend
```

如果会话不在 AstrBot 全局白名单中，rconsole 会记录日志、停止事件，不继续解析或发送。

> 正常 AstrBot pipeline 本身也有白名单阶段；这里是插件侧保守补充，用于避免特殊 hook/环境下出现绕过。

## 验证

新增/更新测试覆盖：

- `b23.tv` 展开到 `BV1HsovBGETx`；
- 模拟 `yt-dlp HTTP 412` 后继续调用官方 API/native fallback；
- 最终输出视频，不包含 `yt-dlp 解析失败`；
- `enable_link_resolvers=false` 与 `global_black_list` 不发送；
- AstrBot 全局白名单不命中时不发送并停止事件，命中时允许处理。

## 版本

本修复随 `v0.3.6` 发布。
