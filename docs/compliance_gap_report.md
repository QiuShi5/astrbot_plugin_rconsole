# rconsole AstrBot 版：插件合规差距与优化点报告

> 目标：对照 AstrBot 官方插件文档（开发、发布、市场规范）检查 `astrbot_plugin_rconsole` 距「完美合规」还差什么。
> 依据：
> - 官方文档站 https://docs.astrbot.app/ 全量抓取摘要 → `astrbot_plugin_compliance_checklist.md`
> - 原参考项目 https://github.com/zhiyu1998/rconsole-plugin 结构调研 → `rconsole_original_report.md`
> - 本次直接抓取：发布页 plugin-publish、插件市场 JSON 规范 2026-06-27、插件开发指南（新/旧）、AstrBot PyPI 4.27.3 源码校验逻辑
> 原则：只报告差距与可优化点，不做代码修改（尊重「先不做修改」要求）。
> 结论分级：🔴 阻断/强建议 · 🟡 建议 · 🟢 可选/锦上添花

---

## 一、对照清单（逐项结论速览）

| 维度 | 结论 |
|---|---|
| 基础结构（main.py / Star / handler） | ✅ 通过 |
| metadata.yaml 必填字段 | ✅ 通过（name/desc/version/author 均非空） |
| metadata.yaml 可选字段 | 🟡 缺 `social_link`、`tags`；`version` 带 `v` 前缀；`repo` 指向源项目而非本插件仓库 |
| 版本号/兼容范围 | 🟡 `version: v0.3.11` 带 `v`、`astrbot_version: >=4.14,<5` 合法 |
| support_platforms | ✅ 5 个值均为合法 ADAPTER_NAME_2_TYPE key |
| _conf_schema.json | ✅ 合法 JSON、type 齐全、无禁用 _special；🟢 缺 hint 文案 |
| requirements.txt | ✅ 与 import 完全对应；✅ 未用 requests |
| 日志规范 | 🔴 `services/resolver.py` 用了标准库 `logging`（文档明确要求用 `astrbot.api.logger`） |
| 网络请求 | 🟡 用 `urllib` + `asyncio.to_thread`，文档推荐 aiohttp/httpx |
| 持久化 | ✅ 写入 `data/plugin_data/astrbot_plugin_rconsole/`，符合规范 |
| 存储/大文件 | ✅ 符合；🟢 大字体 30MB 在 git 中（包已排除） |
| Logo | ✅ 1:1 500x500；🟢 可压到 256x256 |
| 发布 zip 体积 | ✅ 7.42MB < 16MB |
| LICENSE | 🟡 缺失（原项目有 Mulan PSL-2.0，移植版应保留/注明） |
| CI / GitHub 托管 | 🟡 无 GitHub 仓库、无 .github workflow、无 ruff 配置 |
| 代码风格 | 🟡 main.py/resolver.py 多行超 120 字符，未按 ruff 默认 88 格式化 |
| i18n | 🟢 无 `.astrbot-plugin/i18n/`（可选） |
| Skills / Pages | 🟢 均无（可选） |
| 文档一致性 | 🟡 规则数 46 vs 47 的表述不统一；版本卡片显示的是原插件版本 |

---

## 二、🔴 阻断/强烈建议项（影响发布或违背明确规范）

### 2.1 `repo` 字段指向错误仓库（影响市场发布）
`metadata.yaml` 当前：
```yaml
repo: https://gitee.com/kyrzy0416/rconsole-plugin.git
```
- 该地址是**原 Yunzai R 插件**的 gitee 镜像，**不是本 AstrBot 移植版自己的仓库**。
- 官方插件市场 JSON 规范（2026-06-27）第 7.1/7.7.4：`repo` 必须是 `https://github.com/{owner}/{repository}` 形式的 **GitHub HTTPS 仓库级 URL**，明确禁止 SSH、gitee、非 GitHub、带 `.git` 结尾（提交流单额外要求 DO NOT end with `.git`）。
- 提交流单要求 `repo` 指向的仓库内必须包含本插件的 `metadata.yaml`，且 `author/name/version` 与市场记录一致（身份校验失败则安装直接失败）。
- **优化方向**：把本插件推送到一个 GitHub 仓库（如 `https://github.com/<你的用户名>/astrbot_plugin_rconsole`），并将 `repo` 改为不带 `.git` 的 HTTPS 地址。

### 2.2 `services/resolver.py` 使用标准库 `logging`
文档（插件指南「日志」节）原文：
> 请务必使用 `from astrbot.api import logger` 来获取日志对象，而不是使用 `logging` 模块。

`services/resolver.py` 第 16 行 `import logging`、第 32 行 `LOGGER = logging.getLogger(__name__)`——这是唯一违反该规范的文件（其余均用 `astrbot.api.logger`）。
- **影响**：日志不会经 AstrBot 的插件级路由与分级，WebUI 中无法单独调节该模块日志等级。
- **优化方向**：改为 `from astrbot.api import logger as LOGGER` 或直接使用 `logger`。

### 2.3 `author` 需要换成真实作者身份
`metadata.yaml` 当前 `author: ported-by-ai`。
- 市场规范中 `plugin_id = author/name`，`author` 是插件生态身份的一部分，应使用真实 GitHub 用户名/作者命名空间（非空、不含 `/`、不含控制字符）。
- **优化方向**：改为真实作者/维护者名字。

---

## 三、🟡 建议项（文档明确推荐或明显可优化）

### 3.1 版本号格式
- `version: v0.3.11` 带 `v` 前缀。发布页示例为 `version: 1.0.0`（遵循语义化版本规范，无 `v`）；AstrBot「版本对比」与 CLI 会剥离 `v`，所以**功能上可用**，但严格按发布页示例建议用 `0.3.11` 纯语义化版本号（模板既有 `v1.3.0` 也有 `1.0.0` 写法，文档自身不完全一致，以发布页为准最稳）。
- `astrbot_version: ">=4.14,<5"` 已是合法 PEP 440、无 `v` 前缀，✅ 无需改。

### 3.2 补全 metadata 可选字段（提升市场展示）
- `social_link`：作者主页/项目主页（发布页「（可选）你的个人网站、GitHub 主页等」）。
- `tags`：市场分类与搜索标签（发布页「（可选）标签列表」，如 `rss`、`解析`、`音乐`、`工具`）。
- `desc`：当前为单行，文档说明支持多行 Markdown，可扩写安装/命令/配置要点，利于市场卡片。

### 3.3 网络请求层：urllib → aiohttp / httpx
文档开发原则原文：
> 不要使用 requests 库来进行网络请求，可以使用 aiohttp, httpx 等异步网络请求库。

当前实现用 `urllib.request` 包在 `asyncio.to_thread()` 里（未用 requests，技术上未违反字面规定），但并非文档推荐的异步 HTTP 库。重构为 `httpx.AsyncClient` / `aiohttp` 可消除线程池占用并符合文档推荐。

### 3.4 代码风格：引入 ruff
文档开发原则原文：**「在进行提交前，请使用 ruff 工具格式化您的代码。」**
- 当前无 `pyproject.toml` / `ruff.toml`；`main.py` 18 行、`resolver.py` 25 行超 120 字符，未达 ruff 默认 88 列。
- **优化方向**：加 `pyproject.toml`（含 `[tool.ruff]`），提交前 `ruff check --fix` + `ruff format`。

### 3.5 LICENSE
- 原参考项目采用木兰宽松许可证第 2 版（MulanPSL-2.0）；移植版未携带 LICENSE 文件。
- 文档未强制要求 LICENSE，但作为 GitHub 公开仓库与移植作品，保留/注明上游许可证是良好实践（尤其资源、代码源自原项目）。

### 3.6 版本卡片内容与插件自身版本不一致
- `resources/config/version.yaml` 仍是原 R 插件的 `version: 1.14.5.14` 与更新日志，渲染出的「版本卡片」会向用户展示原插件版本号，而非本移植版 `0.3.11`。
- 若希望版本卡片体现本插件的版本与 changelog，需替换为移植版自己的版本数据；若刻意保留「高复刻」原卡片样式，建议在文案/README 中说明。

### 3.7 文档中规则数的表述不一致
- `README.md` 写「46 条运行规则」，`docs/full_parity_verification_summary.md` / `final_review_report.md` 写「47 条」；`main.py` 实际为 46 条（第 47 条 `update` 入口已按产品要求移除，但 parity 矩阵仍保留历史对照）。
- 建议统一口径：实现 46 条 + 1 条按策略移除（或注明矩阵含历史映射）。

---

## 四、🟢 可选/锦上添花项

| 项 | 说明 |
|---|---|
| Logo 尺寸 | 当前 500x500（0.05MB，1:1 合规）；文档推荐 256x256，可无损缩小 |
| i18n | 增加 `.astrbot-plugin/i18n/zh-CN.json`、`en-US.json`，国际化 `display_name`/`desc`/配置 `description`/`hint`（可选） |
| Skills | 可将查询/翻译/点歌等能力封装为 `skills/`（可选，随插件只读展示） |
| Pages | 复杂配置/Dashboard 再引入 `pages/<name>/index.html`（当前 `_conf_schema.json` 已足够） |
| CI | 加 GitHub Actions（如 `ruff` / `pytest` / 官方商店 smoke 校验），提升发布可信度 |
| `.gitattributes` / git-lfs | 大字体 30MB 已从 zip 排除；若推 GitHub 仓库建议 git-lfs 或发布分支，控制仓库体积 |
| `_conf_schema.json` 文案 | 多数配置项有 `description` ✅；可补充 `hint`/`obvious_hint` 提升 WebUI 体验 |
| `initialize()` | 模板含可选 `async def initialize()`；当前未实现（合法，非必填） |

---

## 五、已确认合规（无需改动）

- 目录结构：`main.py` 入口、插件类继承 `Star`、handler 全部在类内且前两参为 `self/event` ✅
- `metadata.yaml`：必填四字段非空；`name` 为合法 Python 标识符、`astrbot_plugin_` 前缀、全小写、无空格 ✅
- `_conf_schema.json`：合法 UTF-8 JSON；每个配置项含 `type`；类型均在 string/text/int/float/bool/object/list/dict/template_list 内；未使用禁用 `_special` ✅
- `requirements.txt`：PyYAML/Pillow/yt-dlp/qrcode 与代码 import 一一对应 ✅
- 持久化：写入 `data/plugin_data/astrbot_plugin_rconsole/`（storage 文档要求）✅
- 发布体积：zip 7.42MB < 16MB✅
- 日志：除 resolver.py 外均用 `astrbot.api.logger` ✅
- `terminate()` 已实现（async）✅；未使用事件钩子 ✅

---

## 六、最高优先级行动清单（如后续要发布市场）

1. 创建/确定 GitHub 仓库，改 `repo` 为不带 `.git` 的 HTTPS 地址（🔴）
2. 改 `author` 为真实用户（🔴）
3. `resolver.py` 的 `logging` → `astrbot.api.logger`（🔴）
4. `version` 去掉 `v` 前缀、补 `social_link`/`tags`（🟡）
5. 引入 ruff + pyproject 并格式化（🟡）
6. 补充 LICENSE（🟡）

---

*生成时间：2026-08-18。对照来源文档版本：发布页（Last updated 指向 git 历史）、插件市场规范 2026-06-27、AstrBot PyPI 4.27.3。*