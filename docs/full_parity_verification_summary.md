# 完整功能/样式 Parity 验证总表

## 结论摘要

本轮针对 grader 指出的“缺少完整原 R 插件功能清单映射”补齐了自动生成矩阵和可执行验证：

- 原 R 插件 `apps/*.js` 中 `reg:` 入口：47 条；
- AstrBot 版 `_build_rules()` 实现：46 条（第 47 条 `update` 入口已按产品要求移除，parity 矩阵保留其历史对照）；
- 自动矩阵生成：通过；
- 平台无关/可工具链实现功能：已实现并有测试或代码路径证据；
- 环境依赖功能：9 条，均保留入口、权限、配置、诊断能力，不在沙箱伪造成功。

## 主要证据文件

| 文件 | 作用 |
|---|---|
| `docs/full_original_to_astrbot_parity_matrix.md` | 47 条原始正则到 AstrBot handler 的完整矩阵（46 条已实现 + update 入口按策略移除的历史对照） |
| `docs/full_original_to_astrbot_parity_matrix.json` | 同上，机器可读版本 |
| `docs/visual_comparison_report.md` | 样式 token、尺寸、字体、图标量化对比 |
| `docs/style_quantitative_check.json` | 样式量化检查输出 |
| `docs/external_workflow_validation.md` | yt-dlp/OpenGraph/API 外部解析链验证 |
| `docs/astrbot_runtime_adapter_validation.md` | 真实 AstrBot CLI、Web 服务启动、消息组件和适配器能力探针 |
| `docs/astrbot_runtime_validation.md` | 真实 AstrBot 包导入验证 |

## 自动验证命令

```bash
python astrbot_plugin_rconsole/tests/generate_full_parity_matrix.py
python astrbot_plugin_rconsole/tests/test_core_services.py
python astrbot_plugin_rconsole/tests/test_astrbot_stub_e2e.py
python astrbot_plugin_rconsole/tests/test_media_resolvers.py
python astrbot_plugin_rconsole/tests/test_style_quantitative.py
python astrbot_plugin_rconsole/tests/test_capability_probe.py
.venv_astrbot_check/bin/python astrbot_plugin_rconsole/tests/test_runtime_adapter_probe.py
```

全部已通过。

## 对“全功能”的处理原则

原 R 插件基于 Yunzai/OneBot、Redis、Puppeteer、BBDown、ffmpeg、tdl、aria2、账号 Cookie、群文件/群语音等环境。AstrBot 版按以下方式迁移：

1. **平台无关功能**：直接实现，例如帮助、版本、查询、翻译、点歌缓存、白名单、海外解析开关、网页总结。
2. **通用媒体解析功能**：使用 `yt-dlp` 和 OpenGraph/API 实现，例如 YouTube/TikTok/Twitter/X/B站/AcFun/通用视频站、微博/小红书/米游社等。
3. **账号/适配器强耦合功能**：保留原入口、权限和配置，新增 `#R能力诊断` 检测前置条件；真实执行需用户提供实际 AstrBot 适配器、账号 Cookie、群聊上下文和外部工具。

## 对“全样式”的处理原则

- 原 R 插件 HTML/CSS/图片/字体资源已保留；
- 核心聊天输出图片使用 Pillow 复刻：帮助、版本、点歌列表；
- 自动检查证明关键尺寸比例、颜色、字体、图标、水印与原 CSS/HTML 对齐；
- 未声称逐像素完全相同，因为原版依赖 Puppeteer/浏览器排版，AstrBot 部署环境未必有 Chromium。
