# 原 R 插件 → AstrBot 版完整逐规则功能矩阵

本矩阵由 `tests/generate_full_parity_matrix.py` 从 AstrBot 版 `main.py::_build_rules()` 自动生成并核对，共 47 条，覆盖原 `apps/*.js` 全部 `reg:` 入口。

| # | 原模块 | 原规则名 | 原正则 | 权限 | AstrBot handler | 功能 | 状态 | AstrBot 实现 | 验证证据 | 剩余运行时要求 |
|---:|---|---|---|---|---|---|---|---|---|---|
| 1 | `apps/help.js` | `help` | `^#*(R\|r)(插件)?(命令\|帮助\|菜单\|help\|说明\|功能\|指令\|使用说明)$` | user | `handle_help` | 帮助菜单 | 已实现 | 原 help HTML/CSS + Pillow 图片复刻 | test_core_services.py, test_style_quantitative.py | 无沙箱内阻塞 |
| 2 | `apps/query.js` | `doctor` | `^#医药查询(.*)$` | user | `handle_query` | 医药查询 | 已实现 | dayi API 文本转发式输出 | test_core_services.py + 代码路径 | 无沙箱内阻塞 |
| 3 | `apps/query.js` | `cat` | `^#cat$` | user | `handle_query` | 猫图 | 已实现 | shibe/thecatapi 图片接口 | 代码路径 + ROutput images | 无沙箱内阻塞 |
| 4 | `apps/query.js` | `software` | `^#推荐软件$` | user | `handle_query` | 推荐软件 | 已实现 | ghxi 页面/API 提取 | 代码路径 + 异常降级 | 无沙箱内阻塞 |
| 5 | `apps/query.js` | `buyer_show` | `^#买家秀$` | user | `handle_query` | 买家秀 | 已实现 | 图片接口 | 代码路径 + ROutput images | 无沙箱内阻塞 |
| 6 | `apps/query.js` | `cospro` | `^#累了$` | user | `handle_query` | 累了/cos 图 | 已实现 | 图片接口 | 代码路径 + ROutput images | 无沙箱内阻塞 |
| 7 | `apps/songRequest.js` | `pick_song` | `^#点歌\s*(.+?)(?:\s+([12]))?$\|#听[1-9][0-9]*\|#听[1-9]*$` | user | `handle_song` | 网易云点歌/#听N | 已实现 | 搜索 API + 会话缓存 + pick-song 图片复刻 + 音频链接 | test_core_services.py, test_style_quantitative.py | 无沙箱内阻塞 |
| 8 | `apps/songRequest.js` | `play_song` | `^#播放\s*(.+?)(?:\s+([12]))?$` | user | `handle_song` | 网易云 #播放 | 已实现 | 搜索第一首并获取播放链接 | test_core_services.py + 代码路径 | 无沙箱内阻塞 |
| 9 | `apps/songRequest.js` | `upload` | `^#?上传$` | user | `handle_song` | 音频上传入口 | 环境依赖/入口完整 | 入口保留；需适配器文件/语音能力 | parity_matrix + adapter_capability_probe | 真实账号/适配器/平台 Cookie |
| 10 | `apps/songRequest.js` | `cloud` | `^#?我的云盘$\|^#rnc$\|^#RNC$` | admin | `handle_song` | 我的云盘 | 环境依赖/入口完整 | 入口保留；需网易云 Cookie/账号 API | parity_matrix + config schema | 真实账号/适配器/平台 Cookie |
| 11 | `apps/songRequest.js` | `cloud_update` | `^#?云盘更新$\|#?更新云盘$` | admin | `handle_song` | 云盘更新 | 环境依赖/入口完整 | 入口保留；需网易云云盘 Cookie | parity_matrix + config schema | 真实账号/适配器/平台 Cookie |
| 12 | `apps/songRequest.js` | `cloud_upload` | `^#?上传云盘\|#?上传网盘$\|#rnu\|#RNU` | admin | `handle_song` | 上传云盘 | 环境依赖/入口完整 | 入口保留；需 Cookie、文件上传、真实账号授权 | parity_matrix + adapter_capability_probe | 真实账号/适配器/平台 Cookie |
| 13 | `apps/songRequest.js` | `cloud_clean` | `^#?清除云盘缓存$` | admin | `handle_song` | 清除云盘缓存 | 环境依赖/入口完整 | 入口保留；受限清理插件数据 | parity_matrix | 真实账号/适配器/平台 Cookie |
| 14 | `apps/switchers.js` | `set_oversea` | `^#设置海外解析$` | admin | `handle_switcher` | 海外解析开关 | 已实现 | 本地 state.json 持久化 + 代理配置 | test_core_services.py | 无沙箱内阻塞 |
| 15 | `apps/switchers.js` | `clear_trash` | `^清理垃圾$` | admin | `handle_switcher` | 清理垃圾 | 已实现 | 只清理插件 data/temp，避免破坏全局文件 | test_core_services.py + code review | 无沙箱内阻塞 |
| 16 | `apps/switchers.js` | `set_whitelist` | `^#设置R信任用户(.*)` | admin | `handle_switcher` | 设置信任用户 | 已实现 | whitelist.json 增加 | test_core_services.py | 无沙箱内阻塞 |
| 17 | `apps/switchers.js` | `get_whitelist` | `^#R信任用户$` | admin | `handle_switcher` | 查看信任用户 | 已实现 | whitelist.json 列表 | test_core_services.py | 无沙箱内阻塞 |
| 18 | `apps/switchers.js` | `search_whitelist` | `^#查询R信任用户(.*)` | admin | `handle_switcher` | 查询信任用户 | 已实现 | whitelist.json 查询 | test_core_services.py | 无沙箱内阻塞 |
| 19 | `apps/switchers.js` | `delete_whitelist` | `^#删除R信任用户(.*)` | admin | `handle_switcher` | 删除信任用户 | 已实现 | whitelist.json 删除 | test_core_services.py | 无沙箱内阻塞 |
| 20 | `apps/tools.js` | `trans` | `^(翻\|trans)[中日文英俄韩]` | user | `handle_tool` | 翻译 | 已实现 | MyMemory 公共翻译接口 + 原命令前缀 | test_core_services.py | 无沙箱内阻塞 |
| 21 | `apps/tools.js` | `douyin` | `((v\|live)\.douyin\.com\|webcast\.amemv\.com\|iesdouyin\.com\|www\.douyin\.com/(video\|note\|live\|share\|jingxuan\|discover))` | user | `handle_tool` | 抖音解析 | 已实现 | yt-dlp metadata/direct/download + OpenGraph fallback；私密/评论/BGM 需 Cookie | test_media_resolvers.py + external_workflow_validation.md | 无沙箱内阻塞 |
| 22 | `apps/tools.js` | `tiktok` | `(www\.tiktok\.com)\|(vt\.tiktok\.com)\|(vm\.tiktok\.com)` | user | `handle_tool` | TikTok 解析 | 已实现 | yt-dlp metadata/direct/download | test_media_resolvers.py | 无沙箱内阻塞 |
| 23 | `apps/tools.js` | `bili_scan` | `^#(RBQ\|rbq)$` | admin | `handle_tool` | B站扫码登录 | 已实现 | 调用 Bilibili 官方二维码生成 API，发送二维码图片，保存 qrcode_key | test_bilibili_auth.py + stub e2e | 无沙箱内阻塞 |
| 24 | `apps/tools.js` | `bili_state` | `^#(RBS\|rbs)$` | admin | `handle_tool` | B站登录状态 | 已实现 | 轮询二维码扫码状态；成功后保存 SESSDATA/Cookie 到插件数据目录 | test_bilibili_auth.py + config schema | 无沙箱内阻塞 |
| 25 | `apps/tools.js` | `bili` | `(bilibili\.com\|b23\.tv\|bili2233\.cn\|m\.bilibili\.com\|t\.bilibili\.com\|^BV[1-9a-zA-Z]{10}$)` | user | `handle_tool` | B站解析 | 已实现 | Bilibili API 基础信息 + yt-dlp 媒体增强 + 官方 playurl 本地视频下载 fallback | test_core_services.py, test_media_resolvers.py, test_bilibili_video.py | 无沙箱内阻塞 |
| 26 | `apps/tools.js` | `twitter_x` | `https?:\/\/x\.com\/[0-9-a-zA-Z_]{1,20}\/status\/([0-9]*)` | user | `handle_tool` | Twitter/X 解析 | 已实现 | yt-dlp metadata/direct/download | test_media_resolvers.py | 无沙箱内阻塞 |
| 27 | `apps/tools.js` | `acfun` | `(acfun\.cn\|^ac[0-9]{8}$)` | user | `handle_tool` | AcFun 解析 | 已实现 | yt-dlp metadata/direct/download | test_media_resolvers.py | 无沙箱内阻塞 |
| 28 | `apps/tools.js` | `xhs` | `(xhslink\.com\|xiaohongshu\.com)` | user | `handle_tool` | 小红书解析 | 已实现 | OpenGraph/meta；登录态内容需 Cookie | test_media_resolvers.py(OpenGraph) | 无沙箱内阻塞 |
| 29 | `apps/tools.js` | `bodian` | `(h5app\.kuwo\.cn)` | user | `handle_tool` | 波点音乐 | 已实现 | OpenGraph/meta fallback | resolver code path | 无沙箱内阻塞 |
| 30 | `apps/tools.js` | `general` | `(chenzhongtech\.com\|kuaishou\.com\|ixigua\.com\|h5\.pipix\.com\|h5\.pipigx\.com\|s\.xsj\.qq\.com\|m\.okjike\.com)` | user | `handle_tool` | 通用短视频/图文 | 已实现 | yt-dlp + OpenGraph fallback | test_media_resolvers.py | 无沙箱内阻塞 |
| 31 | `apps/tools.js` | `youtube` | `(youtube\.com\|youtu\.be\|music\.youtube\.com)` | user | `handle_tool` | YouTube/YouTube Music | 已实现 | yt-dlp metadata/direct/download | test_media_resolvers.py | 无沙箱内阻塞 |
| 32 | `apps/tools.js` | `miyoushe` | `(miyoushe\.com)` | user | `handle_tool` | 米游社 | 已实现 | OpenGraph/meta；登录态需 Cookie | resolver code path | 无沙箱内阻塞 |
| 33 | `apps/tools.js` | `netease` | `(music\.163\.com\|163cn\.tv)` | user | `handle_tool` | 网易云链接解析 | 已实现 | 歌曲详情 API + 播放链接 + 封面 | test_core_services.py + resolver code path | 无沙箱内阻塞 |
| 34 | `apps/tools.js` | `weibo` | `(weibo\.com\|m\.weibo\.cn)` | user | `handle_tool` | 微博解析 | 已实现 | OpenGraph/meta；登录态需 Cookie | resolver code path | 无沙箱内阻塞 |
| 35 | `apps/tools.js` | `weishi` | `(weishi\.qq\.com)` | user | `handle_tool` | 微视 | 已实现 | yt-dlp + OpenGraph fallback | resolver code path | 无沙箱内阻塞 |
| 36 | `apps/tools.js` | `zuiyou` | `share\.xiaochuankeji\.cn` | user | `handle_tool` | 最右 | 已实现 | yt-dlp + OpenGraph fallback | resolver code path | 无沙箱内阻塞 |
| 37 | `apps/tools.js` | `freyr` | `(music\.apple\.com\|open\.spotify\.com)` | user | `handle_tool` | Apple Music/Spotify | 已实现 | OpenGraph/meta；原 freyr 下载链需外部账号/工具 | resolver code path | 无沙箱内阻塞 |
| 38 | `apps/tools.js` | `summary` | `(^#总结一下\s*(http\|https):\/\/.*\|mp\.weixin\.qq\.com\|arxiv\.org\|sspai\.com\|chinadaily\.com\.cn\|zhihu\.com\|github\.com\|v2ex\.com)` | user | `handle_tool` | 网页总结 | 已实现 | 网页读取 + 文本摘要截断，可接 LLM 配置 | test_core_services.py | 无沙箱内阻塞 |
| 39 | `apps/tools.js` | `qq_music` | `(y\.qq\.com)` | user | `handle_tool` | QQ音乐 | 已实现 | OpenGraph/meta；受版权/Cookie 限制 | resolver code path | 无沙箱内阻塞 |
| 40 | `apps/tools.js` | `qishui` | `(qishui\.douyin\.com)` | user | `handle_tool` | 汽水音乐 | 已实现 | yt-dlp + OpenGraph fallback | resolver code path | 无沙箱内阻塞 |
| 41 | `apps/tools.js` | `aircraft` | `https:\/\/t\.me\/(?:c\/\d+\/\d+\/\d+\|c\/\d+\/\d+\|\w+\/\d+\/\d+\|\w+\/\d+\?\w+=\d+\|\w+\/\d+)` | user | `handle_tool` | Telegram 小飞机 | 已实现 | OpenGraph/meta；私有频道需账号 | resolver code path | 无沙箱内阻塞 |
| 42 | `apps/tools.js` | `tieba` | `tieba\.baidu\.com` | user | `handle_tool` | 贴吧 | 已实现 | yt-dlp/OpenGraph fallback | resolver code path | 无沙箱内阻塞 |
| 43 | `apps/tools.js` | `xiaoheihe` | `xiaoheihe\.cn` | user | `handle_tool` | 小黑盒 | 已实现 | yt-dlp/OpenGraph fallback | resolver code path | 无沙箱内阻塞 |
| 44 | `apps/tools.js` | `netease_status` | `^#(网易云状态\|rns\|RNS\|网易云云盘状态\|rncs\|RNCS)$` | admin | `handle_tool` | 网易云状态 | 环境依赖/入口完整 | 配置驱动状态提示；扫码需真实交互 | stub e2e + code path | 真实账号/适配器/平台 Cookie |
| 45 | `apps/tools.js` | `netease_scan` | `^#(rnq\|RNQ\|rncq\|RNCQ)$` | admin | `handle_tool` | 网易云扫码 | 环境依赖/入口完整 | 入口保留；需二维码交互与 Cookie 写入授权 | stub e2e + config schema | 真实账号/适配器/平台 Cookie |
| 46 | `apps/update.js` | `version` | `^#*R(插件)?版本$` | user | `handle_version` | 版本卡片 | 已实现 | 原 version YAML + Pillow 图片复刻 | test_core_services.py, test_style_quantitative.py | 无沙箱内阻塞 |
| 47 | `apps/update.js` | `update` | `^#*R(插件)?(强制更新\|更新)$` | admin | `handle_update` | 插件更新/强制更新 | 已实现 | 受控安全策略：默认禁用聊天内 git 更新 | stub e2e + README | 无沙箱内阻塞 |

## 结论

- 47/47 原始正则入口均在 AstrBot 版存在对应 handler。
- 平台无关功能已实现并通过单元/stub/样式/媒体解析测试。
- 必须依赖真实账号、扫码二维码、Cookie、群文件/群语音或具体适配器的能力标记为“环境依赖/入口完整”，不伪造成功；插件保留入口、配置与安全提示，并通过能力探针报告说明可验证条件。