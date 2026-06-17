# Round 2/6 业务实现深审与修补报告

## 审计范围

- `main.py` 分发、权限、配置开关；
- `services/media_downloader.py` 的 yt-dlp 模式语义；
- 查询/状态/翻译/能力诊断服务；
- stub E2E 与媒体解析测试覆盖。

## 发现并修复的问题

### 1. `enable_link_resolvers` 未在统一分发中生效

问题：配置 schema 声明了链接解析总开关，但此前 `rconsole_dispatch()` 对所有链接规则仍会继续执行。

修复：新增 `RConsolePlugin._rule_disabled()`，对链接解析类规则执行前检查：

- `enable_link_resolvers=false` 时静默跳过链接解析；
- 不影响帮助、查询、点歌、管理、翻译、状态等非链接命令。

验证：`tests/test_astrbot_stub_e2e.py` 增加关闭总开关后 B站链接不发送消息的断言。

### 2. `global_black_list` 未在统一分发中生效

问题：配置 schema 声明全局平台黑名单，但此前业务路径未使用。

修复：`_rule_disabled()` 增加平台别名判断，例如：

- `B站` / `哔哩哔哩` / `bilibili` → `bili`
- `抖音` → `douyin`
- `YouTube` → `youtube`
- `网易云` → `netease`

验证：`tests/test_astrbot_stub_e2e.py` 增加 `global_black_list=['B站']` 后 B站链接不触发发送的断言。

### 3. `ytdlp.enabled` 与 `off` 模式不一致

问题：配置 schema 有 `enabled`，但 `main.py` 未使用；schema 也未提供 `off` 模式。

修复：

- `_conf_schema.json` 的 `ytdlp.mode` 增加 `off`；
- `main.py` 在 `ytdlp.enabled=false` 时传入 `off`；
- `YtDlpService` 支持 `off`，并返回明确文本：`yt-dlp 解析链已在配置中关闭`。

验证：`tests/test_media_resolvers.py` 增加 `mode='off'` 断言，不返回视频直链。

## 验证命令

```bash
python -m py_compile astrbot_plugin_rconsole/main.py astrbot_plugin_rconsole/services/media_downloader.py
python astrbot_plugin_rconsole/tests/test_astrbot_stub_e2e.py
python astrbot_plugin_rconsole/tests/test_media_resolvers.py
```

结果：全部通过。

## 100% 信心循环

已确认本轮修复均有对应自动测试覆盖，并且未改变原 47 条规则数量。仍需 Round 3 继续检查样式资源与输出一致性。
