# Round 5/6 打包、安装、文档与发布一致性验证报告

## 操作

1. 将根目录 `docs/*.md`、`docs/*.json` 同步到插件内 `astrbot_plugin_rconsole/docs/`；
2. 清理运行缓存：`data/test_*`、`data/temp`、`__pycache__`、`*.pyc`；
3. 重新运行 `scripts/build_package.py`；
4. 检查 zip 包内容、排除规则、metadata、schema 和关键文档。

## 验证结果

```text
ROUND5_PACKAGE_AUDIT_OK
entries 87
size_mb 7.35
sha256 9be2d3dc2b8eabf33ef517a5696a9cdfc8a7c71dea001d9bb9f4f110b09e7af6
```

## 包内容检查

确认 zip 包包含：

- `main.py`
- `services/capabilities.py`
- `services/card_renderer.py`
- `services/media_downloader.py`
- `docs/round1_consistency_audit.md`
- `docs/round2_business_audit.md`
- `docs/round3_style_audit.md`
- `docs/round4_runtime_toolchain_audit.md`
- `docs/full_original_to_astrbot_parity_matrix.md`
- `resources/font/FZB.ttf`

确认 zip 包排除：

- `data/`
- `tests/`
- `__pycache__/`
- `*.pyc`
- `resources/font/江城月湖体 400W.ttf`

## 配置/元数据检查

- `metadata.yaml`：`version = v0.3.0`；
- `_conf_schema.json`：`ytdlp.mode` 包含 `off` / `metadata` / `direct` / `download`；
- 发布包体积：7.35MB，低于 16MB 目标。

## 100% 信心循环

Round 5 未发现包内容缺失或发布配置不一致。最终 SHA256 已更新，进入 Round 6 做最终全量回归与交付。
