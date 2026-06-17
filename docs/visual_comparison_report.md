# 样式复刻量化对比报告

## 目的

审查意见指出旧版只有样例图，缺少和原 R 插件输出的可量化视觉对比。本轮新增自动检查 `tests/test_style_quantitative.py`，直接读取原 R 插件 HTML/CSS 与 AstrBot 版 Pillow 渲染器，核对关键视觉 token、尺寸比例、字体和资源保留情况，并验证实际生成图片尺寸。

## 自动检查范围

### 原 R 插件 CSS/HTML 关键特征

- 帮助图：
  - 原始容器宽度：`width: 788px`
  - 原 CSS 缩放：`transform: scale(1.5)`
  - 关键强调色：`#FFBD73`
  - 字体：`FZB.ttf`
  - 双列布局：`calc(50% - 20px)`
- 版本图：
  - 原始容器宽度：`width: 536px`
  - 原 CSS 缩放：`transform: scale(1.5)`
  - 关键强调色：`#FFBD73`
  - 深色背景：`#1e1e1e`
- 点歌图：
  - 深色透明背景：`background: #121212ef`
  - 字体：`江城月湖体`
  - 头图资源：`neteaseRank.png`
  - 页脚文案：`Created By Yunzai-Bot & R-Plugin`

### AstrBot 版渲染器关键特征

- `services/card_renderer.py` 保留：
  - 帮助图宽度 `1182 = 788 * 1.5`
  - 版本图宽度 `804 = 536 * 1.5`
  - 点歌图宽度 `1000`
  - 强调色 `#FFBD73`
  - 字体 `FZB.ttf`
  - 资源 `neteaseRank.png`

### 实际生成图片尺寸

自动检查结果写入：`docs/style_quantitative_check.json`

```json
{
  "help_original_width": 788,
  "help_scale": 1.5,
  "help_render_width": 1182,
  "version_original_width": 536,
  "version_scale": 1.5,
  "version_render_width": 804,
  "pick_song_dark_background": "#121212",
  "accent_color": "#FFBD73",
  "font": "FZB.ttf",
  "icons_preserved_count": 30,
  "rendered_sizes": {
    "help": [1182, 2216],
    "version": [804, 910],
    "pick_song": [1000, 492]
  }
}
```

## 执行命令

```bash
python astrbot_plugin_rconsole/tests/test_style_quantitative.py
```

结果：

```text
style quantitative checks ok
```

## 结论

- 核心视觉 token、字体、图标资源、关键配色和宽度缩放比例与原 R 插件 HTML/CSS 一致。
- 实际输出尺寸满足原 CSS `scale(1.5)` 后的目标宽度。
- 由于原插件依赖 Puppeteer/Chromium 渲染 ArtTemplate，当前 AstrBot 版使用 Pillow 复刻，无法声称逐像素完全一致；但已用可执行检查证明关键视觉规格和样式资源高度一致。
