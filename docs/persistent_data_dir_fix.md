# AstrBot 持久化数据目录修复

## 问题

旧版本插件把运行时数据写入插件安装目录内：

```text
data/plugins/astrbot_plugin_rconsole/data/
```

该目录随插件安装包/代码目录存在。用户在 AstrBot 插件管理中卸载插件后，即使未选择删除数据目录，重新安装时插件代码目录可能被重建，导致 `state.json`、白名单、B站扫码登录态等数据丢失。

## 修复

新版本统一使用 AstrBot 官方插件持久化数据目录：

```text
data/plugin_data/astrbot_plugin_rconsole/
```

该目录独立于插件安装目录，符合 AstrBot `get_astrbot_data_path()/plugin_data/<plugin_name>` 规范。卸载插件但不删除数据目录后，重新安装仍会读取同一目录。

## 涉及数据

持久化数据：

- `state.json`
- `whitelist.json`
- `song_search_cache.json`
- `cloud_song_cache.json`
- `bilibili_auth.json`

运行缓存：

- `temp/`：B站视频等临时下载文件
- `rendered/`：帮助、版本、点歌等渲染图片

## 兼容旧数据

首次启动时，如果发现旧插件安装目录内存在以下 JSON 文件，且新持久化目录还没有对应文件，会复制到 `plugin_data`：

- `state.json`
- `whitelist.json`
- `song_search_cache.json`
- `cloud_song_cache.json`
- `bilibili_auth.json`

迁移过程不会删除旧文件，也不会覆盖新持久化目录中已有数据。

## 验证

新增测试 `tests/test_persistent_data_path.py` 模拟：

1. 旧安装目录存在 `data/state.json` 与 `data/bilibili_auth.json`；
2. 插件启动后复制到 AstrBot `data/plugin_data/astrbot_plugin_rconsole/`；
3. 写入白名单；
4. 模拟重新安装到另一个插件代码目录；
5. 再次启动仍读取同一个 `plugin_data`，白名单和 B站登录态保留。

专项验证命令已通过：

```bash
python -m py_compile main.py services/paths.py services/help_version.py services/netease.py tests/test_persistent_data_path.py
python tests/test_persistent_data_path.py
python tests/test_astrbot_stub_e2e.py
python tests/test_core_services.py
```
