# R 插件源码分析与 AstrBot 迁移映射

> 分析时间基准：2026-06-09 09:24:30 +08:00 Asia/Shanghai  
> 原仓库：`https://gitee.com/kyrzy0416/rconsole-plugin.git`  
> 本地来源目录：`source/rconsole-plugin/`  
> 目的：为后续制作 AstrBot 版本插件提供功能、配置、资源、样式和风险映射依据。

## 1. 仓库获取与基本信息

已成功克隆 Gitee 仓库：

```text
source/rconsole-plugin/
```

顶层结构：

```text
README.md
package.json
index.js
guoba.support.js
apps/
config/
constants/
model/
resources/
utils/
```

`package.json` 显示该插件为 Node.js ESM 项目：

```json
{
  "name": "rconsole-plugin",
  "description": "R-Plugin",
  "type": "module",
  "dependencies": {
    "axios": "^1.3.4",
    "form-data": "^4.0.1",
    "node-id3": "^0.2.6",
    "qrcode": "^1.5.3",
    "p-queue": "^8.0.1",
    "https-proxy-agent": "^6.2.1"
  }
}
```

README 定位：

- 面向 Yunzai-Bot / Miao-Yunzai 的 R-plugin；
- 主要功能集中在生活查询、视频/图文分享解析、音乐点歌、翻译、平台账号状态、插件更新；
- 依赖 ffmpeg 处理视频解析；
- 官方文档地址：`https://zhiyu1998.github.io/rconsole-plugin/`。

## 2. 入口与运行模型

`index.js`：

- 读取 `model/config.js` 中的版本配置；
- 从 `package.json` 获取插件名；
- 输出初始化日志：`R插件{version}初始化...`；
- 动态读取 `apps/*.js` 并导入；
- 将每个 app 模块导出到 Yunzai 插件系统。

Yunzai 运行模型：

- 每个 `apps/*.js` 通过 `class xxx extends plugin` 注册；
- `constructor()` 中配置 `name`、`dsc`、`event`、`priority`、`rule`；
- `rule` 使用正则 `reg` 匹配消息，并调用 `fnc` 方法；
- 权限通过 `permission: 'master'` 标注。

AstrBot 迁移方向：

- 统一为 `main.py` 中 `class RConsolePlugin(Star)`；
- Yunzai `rule.reg` 迁移为 AstrBot `@filter.command`、`@filter.command_group` 或全消息监听 + 正则分发；
- Yunzai `permission: 'master'` 迁移为 `@filter.permission_type(filter.PermissionType.ADMIN)` 或插件内管理员校验；
- Yunzai `e.reply()` 迁移为 `yield event.plain_result(...)`、`yield event.chain_result(...)` 或 `await event.send(...)`；
- Yunzai `segment.image/file/record` 迁移为 AstrBot `Comp.Image`、`Comp.File`、`Comp.Record`、`Comp.Video`。

## 3. 源码模块统计

关键模块：

```text
apps/       6 个业务入口
model/      8 个数据/模板模型
utils/      28 个平台解析与工具模块
constants/  3 个常量模块
resources/html/ 6 套 HTML/CSS 模板，共 12 个文件
resources/img/icon/ 30 个图标
```

### apps

```text
apps/help.js
apps/query.js
apps/songRequest.js
apps/switchers.js
apps/tools.js
apps/update.js
```

### model

```text
model/base.js
model/bili-info.js
model/config.js
model/help.js
model/netease.js
model/neteaseMusicInfo.js
model/pick-song.js
model/version.js
```

### utils

```text
utils/a-bogus.cjs
utils/acfun.js
utils/bbdown-util.js
utils/biliWbi.js
utils/bilibili.js
utils/bodian.js
utils/common.js
utils/ffmpeg-util.js
utils/file.js
utils/general-link-adapter.js
utils/kugou.js
utils/link-share-summary-util.js
utils/llm-util.js
utils/mihoyo.js
utils/openai-builder.js
utils/other.js
utils/pipixia-scraper.js
utils/redis-util.js
utils/retry.js
utils/tdl-util.js
utils/tiktok.js
utils/trans-strategy.js
utils/weibo.js
utils/x-bogus.cjs
utils/xiaoheihe.js
utils/youtube.js
utils/yt-dlp-util.js
utils/yunzai-util.js
```

## 4. 功能入口与命令清单

### 4.1 帮助菜单：`apps/help.js`

| 原正则 | 方法 | 功能 | 输出样式 |
|---|---|---|---|
| `^#*(R|r)(插件)?(命令|帮助|菜单|help|说明|功能|指令|使用说明)$` | `help` | 生成 R 插件帮助菜单 | Puppeteer 渲染 `resources/html/help/help.html` 为图片 |

迁移：

- AstrBot 命令：`/r帮助`、`/R插件帮助`、`/r菜单` 等；
- 兼容原 `#R插件帮助` 文本触发；
- 样式需使用原 HTML/CSS、字体和图标资源生成图片，或实现等价 HTML 渲染。

### 4.2 查询类：`apps/query.js`

| 原正则 | 方法 | 功能 | 外部接口/资源 | 输出 |
|---|---|---|---|---|
| `^#医药查询(.*)$` | `doctor` | 医药/疾病/症状/医院/医生/药品搜索 | `https://server.dayi.org.cn/api/search` | 合并转发文本，格式含 `📌`、`📝` |
| `^#cat$` | `cat` | 猫图 | `shibe.online`、`thecatapi.com` | 先回复固定文案，再批量图片 |
| `^#推荐软件$` | `softwareRecommended` | 推荐 PC/Android 软件 | `ghxi.com/ghapi` | 合并转发文本 |
| `^#买家秀$` | `buyerShow` | 淘宝买家秀图片 | `api.suyanw.cn/api/tbmjx.php` | 图片 |
| `^#累了$` | `cospro` | cos 图片 | `imgapi.cn/cos*.php` | 固定文案 + 批量图片 |

迁移：

- 使用异步 HTTP 客户端 `httpx.AsyncClient`；
- AstrBot 不一定全平台支持合并转发，需做降级：能合并转发则合并，否则分条发送；
- 图片批量阈值沿用 `imageBatchThreshold`。

### 4.3 点歌/网易云：`apps/songRequest.js`

| 原正则 | 方法 | 权限 | 功能 |
|---|---|---|---|
| `^#点歌\s*(.+?)(?:\s+([12]))?$|#听[1-9][0-9]*|#听[1-9]*$` | `pickSong` | 普通 | 搜索网易云歌曲/播客/云盘，生成点歌列表图片，`#听N` 播放 |
| `^#播放\s*(.+?)(?:\s+([12]))?$` | `playSong` | 普通 | 搜索并直接播放第一首 |
| `^#?上传$` | `upLoad` | 普通 | 上传/处理音频相关 |
| `^#?我的云盘$|^#rnc$|^#RNC$` | `myCloud` | master | 查看网易云云盘 |
| `^#?云盘更新$|#?更新云盘$` | `songCloudUpdate` | master | 更新云盘缓存 |
| `^#?上传云盘|#?上传网盘$|#rnu|#RNU` | `uploadCloud` | master | 上传到网易云云盘 |
| `^#?清除云盘缓存$` | `cleanCloudData` | master | 清除云盘缓存 |

依赖与数据：

- 网易云 API：官方/自建/临时 API；
- Cookie：`neteaseCookie`、`neteaseCloudCookie`；
- Redis key：歌曲搜索列表、云盘列表；
- 图片模板：`resources/html/pick-song/`、`netease/`、`neteaseMusicInfo/`；
- 音频下载、ID3 写入、语音转换、群文件上传。

迁移：

- 搜索/播放可用 Python `httpx` + 本地 JSON 缓存实现；
- 音乐卡片、群语音、群文件上传高度依赖平台，AstrBot 需根据平台能力分别实现：
  - 普通平台：文本 + 音频文件/链接；
  - OneBot/aiocqhttp：尝试音乐卡片、语音、群文件；
- `#听N` 需要按会话保存上一次搜索列表。

### 4.4 开关/管理：`apps/switchers.js`

| 原正则 | 方法 | 权限 | 功能 |
|---|---|---|---|
| `^#设置海外解析$` | `setOversea` | master | 切换国内/海外解析模式 |
| `^清理垃圾$` | `clearTrash` | master | 清理 `data/` md5 文件和临时视频目录 |
| `^#设置R信任用户(.*)` | `setWhiteList` | master | 添加信任用户 |
| `^#R信任用户$` | `getWhiteList` | master | 查看信任用户列表 |
| `^#查询R信任用户(.*)` | `searchWhiteList` | master | 查询信任用户 |
| `^#删除R信任用户(.*)` | `deleteWhiteList` | master | 删除信任用户 |

迁移：

- Redis 存储迁移为插件数据目录 JSON 文件或 AstrBot 可用存储；
- `清理垃圾` 属于文件删除操作，只允许清理插件自身临时目录，不能扫描 AstrBot 全局 `data/` 中无关文件；
- 信任用户可存为 `data/whitelist.json`。

### 4.5 工具/解析主模块：`apps/tools.js`

该文件为最大业务模块，包含翻译、短视频/图文/音乐/社区链接解析、AI 总结、登录状态等。

原规则清单：

| 原正则/触发 | 方法 | 权限 | 功能 |
|---|---|---|---|
| `^(翻|trans)[中/英/日/文/俄/韩]` | `trans` | 普通 | 翻译文本/回复消息 |
| 抖音链接 | `douyin` | 普通 | 抖音视频、图集、直播、评论、BGM 解析 |
| TikTok 链接 | `tiktok` | 普通 | TikTok 解析 |
| `#RBQ/#rbq` | `biliScan` | master | B 站扫码登录 |
| `#RBS/#rbs` | `biliState` | master | B 站登录状态 |
| B 站/BV/b23 链接 | `bili` | 普通 | 视频、专栏、番剧、直播、动态、音频解析 |
| X/Twitter 链接 | `twitter_x` | 普通 | Twitter/X 解析 |
| AcFun 链接/ac号 | `acfun` | 普通 | AcFun 解析 |
| 小红书链接 | `xhs` | 普通 | 小红书图文/视频解析 |
| 波点音乐链接 | `bodianMusic` | 普通 | 波点音乐解析 |
| 快手/西瓜/皮皮虾/即刻等 | `general` | 普通 | 通用平台解析 |
| YouTube 链接 | `sy2b` | 普通 | YouTube 视频/音乐解析 |
| 米游社链接 | `miyoushe` | 普通 | 米游社文章图文解析 |
| 网易云链接 | `netease` | 普通 | 网易云音乐解析 |
| 微博链接 | `weibo` | 普通 | 微博图文/评论解析 |
| 微视链接 | `weishi` | 普通 | 微视解析 |
| 最右链接 | `zuiyou` | 普通 | 最右解析 |
| Apple Music/Spotify | `freyr` | 普通 | 音乐解析，依赖外部 freyr/下载流程 |
| `#总结一下 URL`/指定网站 | `linkShareSummary` | 普通 | AI 网页总结 |
| QQ 音乐链接 | `qqMusic` | 普通 | QQ 音乐解析 |
| 汽水音乐链接 | `qishuiMusic` | 普通 | 汽水音乐解析 |
| Telegram 链接 | `aircraft` | 普通 | TG 内容解析，依赖 TDL |
| 贴吧链接 | `tieba` | 普通 | 贴吧解析 |
| 小黑盒链接 | `xiaoheihe` | 普通 | 小黑盒资讯/动态解析 |
| `#网易云状态/#rns/#rncs` | `neteaseStatus` | master | 网易云账号状态 |
| `#rnq/#rncq` | `netease_scan` | master | 网易云扫码登录 |

迁移：

- 需要一个 AstrBot 全消息监听器，对 `event.message_obj.message_str` 进行正则分发；
- 命令类可用 `@filter.command`，链接解析类更适合 `@filter.event_message_type(ALL)` + 正则；
- 视频下载、ffmpeg、yt-dlp、BBDown、Aria2、TDL 等属于本地外部工具，AstrBot 版应配置化开启，并默认提供安全降级；
- 网络接口多且部分依赖 Cookie/签名算法，应逐项用 Python 复刻或桥接原算法逻辑；
- 对不宜直接执行 shell 的功能必须做路径白名单和超时限制。

### 4.6 更新/版本：`apps/update.js`

| 原正则 | 方法 | 功能 |
|---|---|---|
| `^#*R(插件)?版本$` | `version` | 使用 `resources/html/version/` 生成版本图片 |
| `^#*R(插件)?(强制更新|更新)$` | `rconsoleUpdate` | 执行 git pull 更新插件，并合并配置 |

迁移：

- `版本` 可完整迁移为图片卡片；
- `更新/强制更新` 在 AstrBot 插件中属于对插件目录执行 git 操作，可能产生外部副作用，默认应禁用或仅给出手动更新提示；若用户明确开启 `allow_self_update`，再做受限实现。

## 5. 配置项映射

原配置文件：`config/tools.yaml`。

主要分组：

### 5.1 全局

| 原字段 | 默认 | 说明 | AstrBot 配置建议 |
|---|---:|---|---|
| `globalBlackList` | `[]` | 全局禁用解析 | `list` |
| `globalImageLimit` | `0` | 图片是否合并转发阈值 | `int` |
| `defaultPath` | `./data/rcmp4/` | 视频暂存目录 | `string`，限制到插件数据目录 |
| `videoSizeLimit` | `70` | 视频大小限制 MB | `int` |
| `proxyAddr`/`proxyPort` | `127.0.0.1`/`7890` | 代理 | `string` |
| `identifyPrefix` | `''` | 识别前缀 | `string` |
| `forceOverseasServer` | `false` | 强制海外服务器/代理策略 | `bool` |
| `videoCodec` | `auto` | 视频编码 | `string` with options |
| `queueConcurrency` | `1` | 下载队列并发 | `int` |
| `videoDownloadConcurrency` | `1` | 视频下载线程数 | `int` |
| `autoclearTrashtime` | cron | 自动清理时间 | `string` |
| `imageBatchThreshold` | `50` | 图片批量阈值 | `int` |
| `msgElementLimit` | `50` | 单条消息元素限制 | `int` |

### 5.2 Bilibili

字段包括：

- `biliSessData`
- `biliIntroLenLimit`
- `biliDuration`
- `biliDisplayCover`
- `biliDisplayInfo`
- `biliDisplayIntro`
- `biliDisplayOnline`
- `biliDisplaySummary`
- `biliUseBBDown`
- `biliCDN`
- `biliDefaultCDN`
- `biliDownloadMethod`
- `biliResolution`
- `biliBangumiDirect`
- `biliBangumiResolution`
- `biliBangumiDuration`
- `biliSmartResolution`
- `biliFileSizeLimit`
- `biliMinResolution`

迁移：`_conf_schema.json` 中使用 bool/int/string/list/options；敏感 Cookie 默认空，不写入文档示例值。

### 5.3 网易云音乐

字段包括：

- `useLocalNeteaseAPI`
- `useNeteaseSongRequest`
- `isSendVocal`
- `songRequestMaxList`
- `neteaseCookie`
- `neteaseCloudCookie`
- `neteaseCloudAPIServer`
- `neteaseCloudAudioQuality`
- `neteaseUserId`
- `neteaseCloudUserId`

迁移：Cookie/API/音质/用户 ID 写入 AstrBot 配置，搜索结果和云盘缓存写入插件数据文件。

### 5.4 YouTube / 抖音 / 小红书 / 微博 / AI / 小黑盒

字段包括：

- `youtubeGraphicsOptions`
- `youtubeClipTime`
- `youtubeDuration`
- `youtubeCookiePath`
- `douyinCookie`
- `douyinDuration`
- `douyinCompression`
- `douyinDisplayCover`
- `douyinComments`
- `douyinMusic`
- `douyinBGMSendType`
- `xiaohongshuCookie`
- `weiboCookie`
- `weiboComments`
- `xiaoheiheCookie`
- `aiBaseURL`
- `aiApiKey`
- `aiModel`

迁移：敏感字段设置为 `string`/`text` 且默认空；AI 总结功能需要 OpenAI-compatible 客户端。

## 6. 资源与样式分析

### 6.1 HTML 模板

共有 6 套渲染模板：

```text
resources/html/help/help.html + help.css
resources/html/version/version.html + version.css
resources/html/pick-song/pick-song.html + pick-song.css
resources/html/bili-info/bili-info.html + bili-info.css
resources/html/netease/netease.html + netease.css
resources/html/neteaseMusicInfo/neteaseMusicInfo.html + neteaseMusicInfo.css
```

原插件使用 Yunzai 的 Puppeteer：

```js
puppeteer.screenshot("help", data)
puppeteer.screenshot("version", data)
puppeteer.screenshot("pick-song", data)
```

AstrBot 迁移策略：

- 复制原 HTML/CSS/字体/图片资源；
- 使用 Python 模板引擎生成 HTML；
- 使用 Playwright/Chromium 或 AstrBot 可用 html-to-image 能力截图；
- 若运行环境不支持浏览器，降级为纯文本/图片拼接，但这会降低“样式高度一致”程度；因此推荐依赖 `playwright`。

### 6.2 帮助菜单样式

`help.html` 结构：

- 容器 `container`，宽 `788px`；
- 顶部 `head_box`：显示 `R-Plugin`、`Ver：v{{version}}`、logo；
- 分组 `data_box` + `tab_lable`；
- 每个功能项为 `item`，左侧 icon，右侧 title/desc；
- 底部 `Created By Yunzai-Bot & R-Plugin`。

`help.css` 风格：

- 使用 `FZB.ttf` 字体；
- 整体深色背景：`#444` / `#222` / `#2b2b2b`；
- 点缀色 `#FFBD73`；
- 圆角、阴影、卡片式布局；
- `body` 宽 788px，`transform: scale(1.5)`；
- 每行两个功能卡片。

### 6.3 版本卡片样式

`version.html/css`：

- 容器宽 `536px`；
- 深色背景 `#2c2c2c`；
- 版本卡 `version-card`；
- 标题渐变黑灰 + `#FFBD73`；
- 内容区 `#2b2b2b`；
- `.cmd` 使用金色标签样式；
- 底部同样保留 `Created By Yunzai-Bot & R-Plugin`。

### 6.4 图片/字体资源

```text
resources/font/FZB.ttf
resources/font/江城月湖体 400W.ttf
resources/img/default.png
resources/img/icon/*.png  # 30 个功能图标
resources/img/rank/*      # logo 等排名/品牌图片
```

迁移：全部复制到 AstrBot 插件 `resources/`，保留相对路径或改写模板变量。

## 7. 常量与解析控制

`constants/resolve.js` 定义全局解析控制名称：

```text
抖音、哔哩哔哩、TikTok、Twitter、Acfun、小红书、波点、通用、YouTube、米游社、网易云音乐、微博、微视、最右、AM+Spotify、扣扣音乐、汽水音乐、小飞机、贴吧、小黑盒、AI总结
```

`constants/constant.js`：

- 翻译语言映射：中/日/文/英/俄/韩；
- 抖音类型映射；
- Redis key；
- 公共 UA；
- B 站分辨率、下载方式、CDN、视频编码；
- AI 网页总结 prompt；
- 帮助文档地址。

`constants/tools.js`：

- 大量平台 API URL；
- Bilibili、抖音、小红书、网易云、QQ 音乐、汽水音乐、微博、米游社、通用解析等接口。

迁移：需要将 JS 常量转为 Python 常量模块；部分签名算法如 `a-bogus`、`x-bogus` 需单独复刻或暂时桥接。

## 8. 外部依赖与系统工具

Node 依赖：

- `axios`：HTTP；
- `node-fetch`：HTTP；
- `form-data`：上传；
- `node-id3`：音频 ID3；
- `qrcode`：二维码；
- `p-queue`：下载队列；
- `https-proxy-agent`：代理。

系统工具/可选工具：

- `ffmpeg`：视频/音频转换、直播片段、合并；
- `yt-dlp`：YouTube 等视频解析；
- `BBDown`：B 站高画质下载；
- `Aria2` / `axel` / `wget`：下载加速；
- `tdl`：Telegram 解析；
- Chromium/Puppeteer：模板截图。

Python/AstrBot 迁移依赖建议：

```text
httpx
PyYAML
Pillow
qrcode
mutagen
playwright
beautifulsoup4
```

外部命令默认不强制要求，但在 README 标明增强功能依赖。

## 9. 数据存储映射

原插件使用 Redis key：

```text
Yz:rconsole:tools:oversea
Yz:rconsole:tools:songinfo
Yz:rconsole:tools:cloudsonglist
Yz:rconsole:tools:whitelist
Yz:rconsole:resolve:controller
```

AstrBot 迁移建议：

```text
plugin_data/
  state.json                  # oversea、resolve_controller
  whitelist.json              # 信任用户
  song_search_cache.json       # 各群/会话点歌缓存
  cloud_song_cache.json        # 网易云云盘缓存
  temp/                        # 视频/音频临时文件
```

存储 key 按 `event.unified_msg_origin` 或 `group_id/session_id` 分会话隔离。

## 10. 全功能复刻优先级

由于 R 插件体量大且包含大量平台解析，AstrBot 版建议分层实现：

### P0：必须完整复刻

- 帮助菜单图片；
- 版本图片；
- 查询类功能：医药查询、cat、推荐软件、买家秀、累了；
- 开关/信任用户/海外解析状态；
- 翻译；
- 链接识别分发框架；
- 配置 schema；
- 原资源、字体、HTML/CSS 样式迁移。

### P1：核心解析复刻

- 抖音；
- Bilibili；
- 小红书；
- 网易云；
- 微博；
- YouTube；
- 通用解析；
- AI 链接总结。

### P2：增强/平台强耦合能力

- B 站扫码登录；
- 网易云扫码/云盘上传；
- 音乐卡片；
- 群语音；
- 群文件上传；
- BBDown/Aria2/TDL/freyr 外部工具链。

P2 需要平台支持和外部工具，AstrBot 版应实现能力检测和降级。

## 11. 迁移风险

1. **功能体量大**：`apps/tools.js` 超过 5000 行，解析平台多，全部 Python 化需要逐平台实现和测试。
2. **平台能力差异**：Yunzai/OneBot 的合并转发、音乐卡片、群语音、群文件上传在 AstrBot 并非所有平台可用。
3. **外部接口不稳定**：抖音、小红书、微博、B 站、网易云等接口可能需要 Cookie/签名/UA，随时变化。
4. **签名算法迁移**：`a-bogus.cjs`、`x-bogus.cjs` 需要 Python 复刻或受控 Node 子进程桥接。
5. **安全风险**：更新、下载、ffmpeg、Aria2、TDL、git 等命令需严格限制路径、超时和开关。
6. **样式复刻依赖截图环境**：若 AstrBot 运行环境没有 Chromium/Playwright，HTML 样式图片无法完全一致。
7. **版权/素材声明**：原 README 声明素材来源网络、严禁商业/非法用途，AstrBot 版需保留声明。

## 12. 后续 AstrBot 实现映射表

| 原模块 | AstrBot 目标模块 | 迁移动作 |
|---|---|---|
| `apps/help.js` | `main.py` + `services/render.py` | 帮助命令与 HTML 截图 |
| `apps/query.js` | `services/query.py` | 异步 HTTP 查询与图片发送 |
| `apps/songRequest.js` | `services/netease.py` + `services/music.py` | 点歌、播放、缓存、云盘能力 |
| `apps/switchers.js` | `services/state.py` | 状态、白名单、清理 |
| `apps/tools.js` | `services/resolvers/*` | 平台链接解析分模块实现 |
| `apps/update.js` | `services/version.py` | 版本图；更新命令默认降级 |
| `config/tools.yaml` | `_conf_schema.json` | AstrBot 配置 schema |
| `config/help.yaml` | `resources/config/help.yaml` | 帮助菜单数据 |
| `config/version.yaml` | `resources/config/version.yaml` | 版本数据 |
| `resources/html/*` | `resources/html/*` | 原样复制并适配模板变量 |
| `resources/img/*` | `resources/img/*` | 原样复制 |
| `resources/font/*` | `resources/font/*` | 原样复制 |
| Redis key | `data/*.json` | JSON 状态存储 |

## 13. Task 2 验证记录

已完成的验证：

1. `git clone` 成功，仓库进入 `source/rconsole-plugin/`。
2. 读取并确认：
   - `README.md`
   - `package.json`
   - `index.js`
   - `apps/help.js`
   - `apps/query.js`
   - `apps/songRequest.js`
   - `apps/switchers.js`
   - `apps/tools.js`
   - `apps/update.js`
   - `config/help.yaml`
   - `config/tools.yaml`
   - `config/version.yaml`
   - `model/base.js`
   - `model/help.js`
   - `model/pick-song.js`
   - `model/version.js`
   - `constants/constant.js`
   - `constants/resolve.js`
   - `constants/tools.js`
   - 关键 HTML/CSS 模板。
3. 使用 `grep` 提取 `apps/*.js` 中所有 `reg:` 命令/触发规则。
4. 使用 Python 脚本统计关键目录文件数量。
5. 形成功能清单、配置映射、资源样式说明和迁移风险。

未完成/不可在 Task 2 验证的事项：

- 未运行原 Yunzai 插件，因为当前环境不是 Yunzai-Bot；
- 未调用所有外部 API，避免产生大量外部请求和不可控副作用；
- 未验证下载/ffmpeg/BBDown/TDL/freyr 等工具链；
- 未开始 AstrBot 代码实现，按 goal 流程留到后续 Task。
