# rconsole-plugin（R-Plugin）原版项目结构与约定分析报告

> 调研方式：GitHub API 被限流（`api.github.com` 返回 403 rate limit），改用 **gitee 镜像 API + raw.githubusercontent.com 直连（master 分支）** 完成枚举与文件读取。
> 已确认 GitHub 与 gitee 的 master 分支内容一致（README 的 MD5 完全相同），关键文件在 GitHub raw 与 gitee raw 均返回 200。

## 一、仓库基本信息

| 项 | 值 |
|---|---|
| 仓库名 | `rconsole-plugin`（R-Plugin / R插件） |
| GitHub | `https://github.com/zhiyu1998/rconsole-plugin`（默认分支 **master**，**不存在 main 分支**） |
| Gitee 镜像 | `https://gitee.com/kyrzy0416/rconsole-plugin.git` |
| 描述 | 专门为朋友们写的 Yunzai-Bot 插件，专注图片视频分享、生活、健康和学习的插件 |
| 语言 | JavaScript（Node.js ESM） |
| 创建 | 2022-11-20 |
| 最后更新 | 2026-08-01 |
| 规模 | Gitee 侧约 96 star / 10 fork / 15 open issues |

**这是 Yunzai-Bot（Yunzai / Miao-Yunzai / TRSS 等）的原生 JS 插件，不是独立应用**，必须运行在 Yunzai 框架中，强依赖 Yunzai 全局对象（`logger`、`plugin` 类、`segment`(oicq)、`puppeteer` 截图库、`lib/config/config.js`）。

## 二、顶层目录/文件结构

```
rconsole-plugin（master）
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug.yml  config.yml  feature.yml       # issue 表单模板
│   └── workflows/
│       ├── auto-label.yml                          # issue 自动打标签
│       ├── auto-reply-issues.yml                   # issue 自动回复
│       ├── auto-reply-prs.yml                      # PR 自动回复+打标签
│       ├── pr-agent.yml                            # PR Agent 自动审查
│       └── status-update.yml                       # 每周 stale issue 巡检
├── apps/                    # 插件主逻辑（每个文件 = 一个 class extends plugin）
│   ├── help.js              # 帮助菜单命令（#R帮助/#R命令/#R菜单…）
│   ├── query.js             # 查询类：#cat/#买家秀/#医药查询/#推荐软件/#累了
│   ├── songRequest.js       # 点歌：#点歌/#听/#播放（47KB）
│   ├── switchers.js         # 开关项：#设置海外解析/#设置R信任用户/#清理垃圾/#设置视频号Cookie
│   ├── tools.js             # 主解析引擎（297KB，全部平台分享解析+特殊指令）
│   └── update.js            # #R插件更新/#R插件强制更新/#R插件版本
├── config/                  # YAML 配置（运行时热加载）
│   ├── help.yaml            # 帮助菜单数据（group/list/icon/title/desc）
│   ├── tools.yaml           # 主配置（平台 cookie、代理、画质、点歌、AI 等 96 项）
│   └── version.yaml         # 版本号 + 更新日志（changelog）
├── constants/               # 常量/枚举
│   ├── constant.js          # 平台枚举、BILI_RESOLUTION_LIST 等所有下拉常量
│   ├── resolve.js           # 解析器控制器枚举 RESOLVE_CONTROLLER_NAME_ENUM
│   └── tools.js
├── model/                   # 数据模型（渲染数据/配置读写）
│   ├── base.js              # 基类：pluginName、screenData(截图模板路径)
│   ├── config.js            # YAML 配置读写(chokidar 热监听)
│   ├── help.js              # 帮助页数据组装
│   ├── version.js           # 版本页数据组装
│   ├── bili-info.js biliComment.js douyinComment.js kugou-status.js
│   ├── netease.js neteaseMusicInfo.js pick-song.js
├── resources/
│   ├── font/                # FZB.ttf、江城月湖体 400W.ttf（渲染字体）
│   ├── html/                # 每个 model 一个子目录：help/ version/ bili-info/
│   │                        # biliComment/ douyinComment/ kugou-status/ netease/
│   │                        # neteaseMusicInfo/ pick-song/ pick-song-kugou/
│   └── img/                 # icon/（30 个平台图标 png）+ rank/logo.png + default.png
├── utils/                   # 按平台/工具拆分的实现
│   ├── music-platform/  qqmusic/                  # 子目录
│   ├── bilibili.js douyin.js youtube.js tiktok.js instagram.js weibo.js
│   │   kugou.js qqmusic.js netease.js acfun.js mihoyo.js xiaoheihe.js
│   │   pipixia-scraper.js weixin-channel.js weixin-article-yuanbao.js
│   │   general-link-adapter.js bodian.js …
│   ├── a-bogus.cjs  x-bogus.cjs                   # 抖音/小红书签名逆向
│   ├── bbdown-util.js yt-dlp-util.js ffmpeg-util.js tdl-util.js  # 下载工具
│   ├── redis-util.js  llm-util.js  openai-builder.js  retry.js
│   ├── common.js  file.js  yunzai-util.js  trans-strategy.js …
├── .gitignore
├── .pr_agent.toml           # PR Agent 配置（GLM/中文审查）
├── LICENSE                  # 木兰宽松许可证第 2 版
├── README.md
├── guoba.support.js         # 锅巴（GUOBA）图形配置面板适配（48KB）
├── index.js                 # 插件入口：动态 import() apps/*.js
└── package.json             # 仅声明 name/type/dependencies
```

**不存在**：`tests/`、`coverage/`、`dist/`、`docs/` 源码目录、`_conf_schema.json`、`version.yaml` 之外的版本文件。文档（VitePress）在独立仓库 `zhiyu1998.github.io/rconsole-plugin/`，`.gitignore` 中可见 `.vitepress` 等条目。

## 三、LICENSE

有 LICENSE 文件，采用 **木兰宽松许可证第 2 版（MulanPSL-2.0，2020年1月）**（`http://license.coscl.org.cn/MulanPSL2`）。

## 四、README 结构

- **头部徽章区**：居中 logo 图（外加 gitee 链接）、大标题 "R-plugin"、一句话简介、SVG 动画图；**无标准 CI badge**。
- **特征**（5 条）：开箱即用、速度快（可配合 BBDown/Aria2）、画质策略（低画质看内容/高画质看品质）、健壮性、文档完善。
- **使用实例**：5 张功能截图（help / 小红书 xhs / YouTube y2b / 米游社 mys / 知乎 zy）。
- **必要安装**：git clone（国内 gitee / 海外 GitHub 两个地址）+ `pnpm i --filter=rconsole-plugin`（在 Yunzai-Bot/Miao-Yunzai 目录下）+ 安装 ffmpeg。
- **官方文档**：链接到 `https://zhiyu1998.github.io/rconsole-plugin/`，并推广一个 GLM 智能体答疑。
- 交流群二维码、贡献者图、赞助表格、相关链接（喵崽/TRSS/听语惊花/插件库/锅巴）、声明、日志图。
- **README 中没有完整命令列表**——命令以帮助菜单截图展示，完整列表在官方文档中。

## 五、配置格式

**YAML**，全部位于 `config/`，共三个文件：

| 文件 | 用途 |
|---|---|
| `config/tools.yaml` | **主配置**（96 项）：全局黑名单、图片合并阈值、`defaultPath: './data/rcmp4/'`、视频大小限制、代理 proxyAddr/proxyPort、平台 cookie（B站/抖音/小红书/微博/酷狗/QQ音乐/视频号/小黑盒）、画质/时长限制、点歌平台、网易云自建 API、deeplx 翻译接口列表、AI 识图（`aiBaseURL/aiApiKey/aiModel`）、队列并发、自动清理 cron 等 |
| `config/help.yaml` | 帮助菜单数据：`- group: 分组名` + `list: [{icon, title, desc}]` |
| `config/version.yaml` | 版本 changelog：根为数组，`[0].version`（当前 `1.14.5.14`）+ `data`（带 `<span class="cmd">` HTML 标签的更新条目） |

读写由 `model/config.js` 完成：`YAML.parse/stringify` + `chokidar` 监听文件热重载（变更时打日志并重置内容），路径写死为 `./plugins/rconsole-plugin/config/<name>.yaml`。**没有 `_conf_schema.json`**——配置的"图形化 schema"由 `guoba.support.js`（锅巴插件）动态生成。

## 六、帮助菜单 / resources 组织

- **帮助数据**：`config/help.yaml`（icon 字段引用 `resources/img/icon/<icon>.png`，如 `doctor.png`、`tiktok.png`、`bilibili.png`）。
- **生成管线**：`apps/help.js` 拦截 `^#*(R|r)(插件)?(命令|帮助|菜单|help|说明|功能|指令|使用说明)$` → `model/help.js` 读取 help.yaml + 群禁用配置（`cfg.getGroup(...).disable`）→ 组装数据 → `puppeteer.screenshot("help", data)` 渲染 `resources/html/help/help.html`（art-template 语法 `{{each helpData}}`，链接 `{{pluResPath}}`）→ 以**图片**回复；带 md5 缓存。
- **resources/html/ 约定**：每个 model 一个同名子目录和下划线命名（`biliComment/` `douyinComment/`），`model/base.js` 的 `screenData` 统一推算模板路径 `resources/html/<model>/<model>.html`。
- **resources/img/**：`icon/`（30 个平台 png）、`rank/logo.png`、`default.png`。注意 `help.html` 中 preload 了 `{{pluResPath}}img/bg.jpg`，但该文件在 master 分支**不存在（404）**。
- **resources/font/**：FZB.ttf、江城月湖体 400W.ttf。

## 七、插件入口 / 应用结构

- **入口**：`index.js`（Yunzai 约定从插件根目录加载它）。ESM（`package.json` 里 `"type": "module"`，`import fs from "node:fs"` 等）。
- **加载机制**：读 `model/config.js` 拿 version → 启动日志 → `fs.readdirSync('./plugins/<name>/apps')` → 对每个 `.js` 文件 `import('./apps/<file>')` 并 `Promise.allSettled` → 收集失败日志 → 最终 `export { apps }`。
- **每个 `apps/*.js` 导出一个 `class X extends plugin`**，构造函数中 `super({ name, dsc, event:"message", priority, rule:[{ reg, fnc }] })`——这是 Yunzai 插件的标准约定（`reg` 正则 + `fnc` 方法名，另有事件类型与优先级）。
- **`package.json`**：仅 `name`/`description`/`type`/`dependencies`，**无 `main` 字段**、无 scripts、无 devDependencies。依赖：`@the-convocation/twitter-scraper`、`axios`、`cycletls`、`form-data`、`https-proxy-agent`、`node-id3`、`p-queue`、`qrcode`。README 里提到的 axios@0.27.2/tunnel/openai 等是旧版说明，与当前 package.json 已脱节。
- **依赖 Yunzai 全局环境**：`logger`、`global.plugin`、`segment`（`await import("oicq")`）、puppeteer 截图（`../../../lib/puppeteer/puppeteer.js`）、`lib/config/config.js`（群配置）。

## 八、命令 / 功能清单（README 及代码中宣传）

**链接分享解析（apps/tools.js，29+ 平台）**：B站、抖音、快手、西瓜、YouTube、TikTok、Twitter/X、Instagram、小红书、微博、微信视频号、ACFun、皮皮虾、最右、贴吧、米游社、波点音乐、QQ音乐、酷狗、网易云、Apple Music/Spotify、Telegram、小黑盒、汽水音乐等。

**前缀指令**：
- B站扫码：`#RBQ/#rbs/#rkq/#rnq`（含 `#RBS/#RBS` 变体）
- 链接 AI 总结：`#总结一下 <链接>`（或直接发微信公众号/arxiv/sspai/zhihu/github/v2ex/chinadaily 链接）
- 平台状态：`#网易云状态/#rns`、`#网易云云盘状态/#rncs`、`#酷狗状态/#rks`
- 点歌（apps/songRequest.js）：`#点歌/#听/#播放`
- 查询（apps/query.js）：`#cat`、`#买家秀`、`#医药查询 xxx`、`#推荐软件`、`#累了`
- 开关（apps/switchers.js）：`#设置海外解析`、`#设置/查询/删除R信任用户`、`#清理垃圾`、`#设置视频号Cookie`
- 更新（apps/update.js，仅 master 权限）：`#R插件更新`、`#R插件强制更新`、`#R插件版本`（内容为 `git reset --hard + clean + pull`，并先备份 `config/tools.yaml`）

**帮助菜单分组（config/help.yaml）**：查询类功能 / 工具类合集 / 其他指令。

## 九、CI / 工作流（.github/workflows）

全部 5 个工作流都只做 **issue/PR 自动化与代码审查**，**没有任何 test/lint/build 流水线**（与本项目无 npm scripts、无测试框架一致）：

| workflow | 触发 | 作用 |
|---|---|---|
| auto-label.yml | issues:opened | 按标题/正文关键词自动打标签（bug/enhancement/documentation/question/performance/security/priority） |
| auto-reply-issues.yml | issues:opened | 自动回复 issue 并附处理清单 |
| auto-reply-prs.yml | pull_request:opened | 自动回复 PR + 按标题打标签 |
| pr-agent.yml | pull_request_target / issue_comment | 用 `the-pr-agent/pr-agent@v0.39.0` 自动 review/improve；模型 `glm-5.2`（fallback deepseek-v4-flash），密钥走仓库 secrets/vars |
| status-update.yml | schedule 每周一 + workflow_dispatch | 7 天无更新的 issue 提醒，30 天 stale 自动关闭 |

`ISSUE_TEMPLATE/` 提供 bug/config/feature 三个表单模板。`根目录 .pr_agent.toml` 配置 PR Agent（中文审查、`response_language="zh-CN"`）。

## 十、版本管理

- **`config/version.yaml`** 是唯一版本信息来源：数组结构 `[{version: "1.14.5.14", data: [更新条目…]}]`，更新条目允许嵌入 HTML（`<span class="cmd">`）。
- `index.js` 启动时输出 `R插件<ver>初始化` 日志；`apps/update.js`/`model/version.js` 用 `puppeteer` 渲染 `resources/html/version/version.html` 生成版本截图。
- 更新机制：`git pull`（强制更新 = `git reset --hard HEAD` + `git clean -fd`），更新前备份 `config/tools.yaml`，更新后重启。

## 十一、其他特别之处

- **`guoba.support.js`**：锅巴（GUOBA）图形化配置面板的适配层（48KB），导出 `supportGuoba()`，用 `constants/constant.js` 与 `constants/resolve.js` 的枚举构建成组配置 schema；`pluginInfo` 声明名称/作者/图标（`mdi:stove`、`resources/img/rank/logo.png`）。**这是原版"配置面板"，功能上等同 AstrBot 的 `_conf_schema.json`。**
- **数据目录**：`./data/rcmp4/`（`config/tools.yaml` 的 `defaultPath`，存下载视频）——运行期生成，不在仓库内。
- **Redis 可选**：`utils/redis-util.js` + 常量 `REDIS_YUNZAI_ISOVERSEA`/`REDIS_YUNZAI_WHITELIST`（海外解析开关与信任用户列表）。
- 逆向签名：`utils/a-bogus.cjs`（抖音）、`utils/x-bogus.cjs`（小红书）。
- 外部服务依赖：各平台 cookie、可选自建网易云 API、deeplx 翻译接口列表（http 明文）、AI 识图接口（Kimi/Moonshot 兼容）、BBDown/yt-dlp/ffmpeg/tdl 外部下载器。
- **无 web 控制台、无订阅/feed 类外部服务配置。**

## 十二、与原版 vs AstrBot 移植版结构差异对照

| 维度 | 原版 rconsole-plugin（Yunzai, Node.js ESM） | AstrBot 移植版（Python） |
|---|---|---|
| 入口 | `index.js`（动态 `import('./apps/*.js')` + `export { apps }`） | `main.py`（AstrBot 插件入口约定，注册 `async def` 或继承 AstrBot 基类） |
| 元数据 | `package.json`（name/type/dependencies） | `metadata.yaml`（标识、版本、作者、依赖声明） |
| 配置 | `config/*.yaml`（tools.yaml + help.yaml + version.yaml, chokidar 热加载） | `_conf_schema.json`（AstrBot 自动生成配置面板）+ AstrBot 的配置存储 |
| Python 依赖 | `package.json.dependencies`（npm）+ Yunzai 全局 API | `requirements.txt`（pip） |
| 命令路由 | 类内 `super({rule:[{reg, fnc}]})` 正则表 | AstrBot `@asst.register(...)` / `Command` 装饰器 + 处理器函数 |
| 主逻辑位置 | `apps/tools.js`（297KB 单文件）+ `utils/` 平台文件 | `services/`（按平台拆分的 Python 模块） |
| 帮助菜单 | `config/help.yaml` + `resources/html/help/*` puppeteer 截图成图 | `resources/`（文本/图片帮助资源，AstrBot 文本回复更常见） |
| 图片渲染 | 每组数据一个 html 模板 + Yunzai puppeteer | 无 pagerender；通常用文本卡片或 PIL/HTML 渲染（可另接 pagerender 插件） |
| 消息发送 | `this.reply(img)`、`segment`(oicq) 富文本 | AstrBot Provider 消息对象（`reply`、图片路径发送） |
| 平台解析 | `utils/*.js` + `constants/*.js` 枚举 | `services/` + `_conf_schema.json` 里的枚举选项（下拉框） |
| 版本更新 | `config/version.yaml` + 内置 git pull 更新命令 | 通常无内置更新；AstrBot 插件市场处理 |
| CI | 仅 issue/PR 自动化 + PR Agent 审查，**无测试/lint/build** | 可对照补充 pytest + ruff（原版没有可移植的） |

**移植要点提示**：原版的"配置 schema"分散在 `guoba.support.js` + `constants/*.js` 枚举，移植时可直接映射为 `_conf_schema.json`；帮助菜单的 YAML 分组结构（group/list/icon/title/desc）可原样搬到 AstrBot 的 resources；`tools.yaml` 中平台分类主要是 cookie、画质/时长限制，与平台无关的统一消歧逻辑（`constants/resolve.js` 的 `RESOLVE_CONTROLLER_NAME_ENUM`）适合做成 `services/` 的分发器。

## 未能获取的部分

- **GitHub API**（`api.github.com`）因 IP 限流返回 403，未能用官方 API 枚举树/提交历史/统计。
- **GitHub 仓库页面 HTML** 无法访问（连接失败）。已通过 `raw.githubusercontent.com` 对 master 分支逐个验证关键文件均 200，且 README 与 gitee 完全一致，判定两镜像内容同步。
- **git 提交历史**未拉取（未 clone，仅文件快照）。
- **大文件全文**：`apps/tools.js`（297KB）与 `guoba.support.js`（48KB）只读了关键片段（命令正则、模块导入、头部结构），未逐行阅读。
- `resources/img/bg.jpg` 在 help.html 被引用但 master 上游不存在（404）——可能为历史遗留或改由其他资源替代。