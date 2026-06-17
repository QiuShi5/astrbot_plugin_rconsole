# Round 3/6 样式资源与输出复刻深审报告

## 审计范围

- 原 R 插件 `help/version/pick-song` HTML/CSS；
- AstrBot 版 `services/card_renderer.py`；
- 样式量化测试 `tests/test_style_quantitative.py`；
- 实际渲染图尺寸与关键 token。

## 发现并修复的问题

### 点歌列表远程封面未渲染

原 R 插件 `pick-song.html` 使用 `<img src="{{...cover}}">`，浏览器/Puppeteer 可直接加载远程专辑封面。此前 AstrBot 版 Pillow 渲染器只支持本地封面文件；当 `cover` 是 HTTP URL 时会退回默认图，导致网易云点歌列表在真实搜索结果下视觉复刻不足。

修复：

- `services/card_renderer.py` 新增 `_load_cover()`；
- 支持本地路径与 HTTP/HTTPS 封面 URL；
- 远程封面使用 `urllib.request` 下载，限制单图读取 2MB、超时 8 秒；
- 下载失败时仍安全退回默认图，不影响命令输出。

## 验证

```bash
python -m py_compile astrbot_plugin_rconsole/services/card_renderer.py astrbot_plugin_rconsole/tests/test_style_quantitative.py
python astrbot_plugin_rconsole/tests/test_style_quantitative.py
```

结果：通过。

样式量化继续确认：

- help 原宽 `788 * 1.5 = 1182`；
- version 原宽 `536 * 1.5 = 804`；
- pick-song 宽度 `1000`；
- 关键色 `#FFBD73`、背景 `#121212`、字体 `FZB.ttf`、图标数量 30；
- 渲染器包含 `neteaseRank.png` 与远程封面加载逻辑。

## 100% 信心循环

已对照原 CSS/HTML 的尺寸、字体、颜色、页脚、水印、图标和封面能力。当前仍不声称浏览器逐像素一致，但聊天场景核心图片输出已进一步接近原 R 插件行为。
