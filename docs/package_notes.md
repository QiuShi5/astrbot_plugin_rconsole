# 打包与体积说明

## AstrBot 插件市场体积约束

AstrBot 插件发布通常需要关注包体积。原 R 插件资源中包含较大的字体和默认图片：

- `resources/font/FZB.ttf`：约 10.83 MB
- `resources/font/江城月湖体 400W.ttf`：约 18.45 MB
- `resources/img/default.png`：约 6.59 MB

若原样保留，插件目录约 36 MB，不适合 16 MB 左右的市场包。

## 本迁移版处理策略

- 保留 `FZB.ttf`：帮助菜单和版本卡片高复刻的核心字体。
- 移除/排除 `江城月湖体 400W.ttf`：仅用于点歌序号字体，非关键资源；Pillow 渲染器会自动回退到 FZB 或系统字体。
- 压缩 `resources/img/default.png`：用于点歌封面占位，压缩后视觉影响较小。
- 不把运行时目录、缓存、测试、`__pycache__`、已生成样例图打进市场包。

## 推荐打包命令

在插件父目录执行：

```bash
python scripts/build_package.py
```

脚本会输出：

```text
dist/astrbot_plugin_rconsole.zip
```

并自动排除：

- `data/`
- `tests/`
- `__pycache__/`
- `*.pyc`
- `.DS_Store`
- 大数字字体 `resources/font/江城月湖体 400W.ttf`

## 高复刻完整资源包

如果你不受市场 16 MB 限制，想保留原 R 插件全部资源，可直接复制整个 `astrbot_plugin_rconsole/` 文件夹运行，不使用市场包排除规则。完整资源包更接近原仓库资源，但体积更大。
