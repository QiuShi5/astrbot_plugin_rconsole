# R 插件 AstrBot 版样式复刻对照记录

## 目标

在 AstrBot 版中复刻原 R 插件基于 Puppeteer + HTML/CSS 的核心可视化输出，尤其是帮助菜单、版本卡片、网易云点歌列表。由于 AstrBot 部署环境不一定存在 Chromium，本次实现采用双层方案：

1. 保留原插件 `resources/html/*`、`resources/img/*`、`resources/font/*`，用于可追溯和后续浏览器渲染扩展；
2. 新增 `services/card_renderer.py`，用 Pillow 复刻原 CSS 的主要视觉语言，保证无浏览器环境也可稳定输出图片。

## 原 R 插件视觉特征

### 帮助菜单 `resources/html/help/help.html + help.css`

- 宽度：原 CSS `788px`，`transform: scale(1.5)`；AstrBot 版渲染宽度采用 `1182px`。
- 字体：原使用 `FZB.ttf`；AstrBot 版优先使用复制的 `resources/font/FZB.ttf`。
- 颜色：深灰背景 `#444`，内容区 `#222`，功能项 `#2b2b2b`。
- 强调色：标题和边框使用 `#FFBD73`。
- 布局：顶部标题卡 + 分组卡片 + 双列功能项。
- 图标：继续读取 `resources/img/icon/*.png`。
- 页脚：保留 `Created By Yunzai-Bot & R-Plugin`。

### 版本卡片 `resources/html/version/version.html + version.css`

- 宽度：原 CSS `536px`，`transform: scale(1.5)`；AstrBot 版渲染宽度采用 `804px`。
- 字体：优先 FZB。
- 背景：`#1e1e1e` / `#2c2c2c` / `#3a3a3a` 深色层次。
- 标题色：`#FFBD73`。
- 内容：从 `resources/config/version.yaml` 中提取版本号和更新项。

### 点歌列表 `resources/html/pick-song/pick-song.html + pick-song.css`

- 背景：`#121212` 网易云深色列表风格。
- 字体：编号优先使用原 `江城月湖体 400W.ttf`，其他优先 FZB。
- 布局：序号 + 封面 + 歌名/歌手 + 时长；支持 `云盘`、`播客` 标签。
- 水印：保留 `resources/img/icon/neteaseRank.png` 半透明水印。
- 页脚：保留 `Created By Yunzai-Bot & R-Plugin`。

## AstrBot 版实现位置

- 渲染器：`astrbot_plugin_rconsole/services/card_renderer.py`
- 帮助/版本服务：`astrbot_plugin_rconsole/services/help_version.py`
- 点歌服务：`astrbot_plugin_rconsole/services/netease.py`
- 发送逻辑：`astrbot_plugin_rconsole/main.py::_send_output()`

## 用户可见输出行为

- `#R帮助` / `R帮助` / `rhelp`：发送帮助菜单图片；若图片组件不可用，附带文本降级。
- `#R版本` / `R版本` / `rversion`：发送版本卡片图片；若图片组件不可用，附带文本降级。
- `#点歌 关键词`：发送点歌列表图片，同时保留文本和 forward_texts 降级。

## 验证记录

执行命令：

```bash
python -m py_compile astrbot_plugin_rconsole/main.py astrbot_plugin_rconsole/services/card_renderer.py astrbot_plugin_rconsole/services/help_version.py astrbot_plugin_rconsole/services/netease.py
python astrbot_plugin_rconsole/tests/test_core_services.py
python - <<'PY'
# 生成帮助、版本、点歌样例图片并检查尺寸
PY
```

验证结果：

- `py_compile`：通过。
- 核心服务测试：通过。
- 样例图片生成：通过。
- 帮助图尺寸：`1182 x 2216`，符合原 `788px * 1.5` 宽度。
- 版本图尺寸：`804 x 910`，符合原 `536px * 1.5` 宽度。
- 点歌图尺寸：`1000 x 492`，符合深色列表布局。

## 复刻结论

AstrBot 版已在无需浏览器的情况下复刻原 R 插件核心可视化输出：深色卡片、FZB 字体、`#FFBD73` 强调色、圆角阴影、帮助双列布局、版本卡片、点歌列表、水印与页脚。剩余差异主要是：未直接执行原 ArtTemplate/Puppeteer 模板，而是使用 Pillow 实现等价视觉输出；这能显著提升 AstrBot 部署稳定性。
