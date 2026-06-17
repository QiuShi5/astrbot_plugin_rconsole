# B站扫码 #rbq 修复报告

## 用户反馈

历史反馈分三轮：

1. `#rbq/#rbs` 只返回通用能力诊断或看不到二维码，未真正实现扫码登录流程；
2. `#rbq` 登录后没有成功/失败自动回调，且插件设置里不容易看到 B站 `SESSDATA` 配置项；
3. 扫码登录成功后虽然已保存 `data/bilibili_auth.json`，但插件配置页中的 `bilibili.sessdata`/顶层 `bilibili_sessdata` 仍为空。

## 根因

早期版本中：

```python
if rule.name in {"bili_scan", "bili_state"}:
    return self.capability_service.probe(event)
```

后来虽然已实现二维码生成与 `#rbs` 手动查询，但 `#rbq` 仍只提示“发送 #rbs 查看状态”，没有后台轮询任务，因此用户扫码确认后不会收到自动成功/失败/过期/超时回调。

配置方面，原 schema 只提供嵌套字段 `bilibili.sessdata`，且字段类型为 `text`。部分 AstrBot 设置 UI 对嵌套 object 或该类型展示不明显，导致用户误以为没有 B站 SESSDATA 设置。

## 修复内容

### `#rbq` 自动回调

`#rbq/#RBQ` 现在会：

- 调用 Bilibili 官方二维码生成接口：
  - `https://passport.bilibili.com/x/passport-login/web/qrcode/generate`
- 生成二维码 PNG 并发送给用户；
- 自动启动后台轮询任务；
- 根据扫码状态主动回调：
  - 登录成功；
  - 二维码已失效；
  - 查询失败；
  - 超时未确认；
- `#rbs/#RBS` 仍保留为手动查询入口。

### 轮询任务安全性

- 重复发送 `#rbq` 会取消上一轮自动轮询；
- 使用内部 token 区分新旧轮询任务，避免旧任务取消后的 `finally` 误清理新任务引用；
- 插件卸载时取消正在运行的轮询任务；
- 日志记录自动轮询启动、状态变化、结束、超时和取消；
- 日志只记录 Cookie 字段名或脱敏文本，不输出真实 `SESSDATA`、`bili_jct` 等敏感值。

### SESSDATA 自动回填配置

扫码登录成功后，插件会从 `data/bilibili_auth.json` 读取刚保存的 `SESSDATA`，并自动：

- 写入当前运行时配置 `bilibili.sessdata`；
- 同步写入顶层兼容字段 `bilibili_sessdata`；
- 调用 AstrBotConfig 的 `save_config()` 持久化到插件配置文件；
- 立即同步当前 B站解析服务使用的新登录态。

用户回复和日志只说明是否已自动写入，不输出真实 `SESSDATA` 值。若 AstrBot 设置页因前端缓存未立即显示新值，刷新页面或重载插件即可重新读取持久配置。

### SESSDATA 设置项可见性

`_conf_schema.json` 现在同时提供：

- 顶层兼容字段：`bilibili_sessdata`
- 嵌套字段：`bilibili.sessdata`

读取优先级：

1. `bilibili.sessdata`
2. `bilibili_sessdata`

这样即使 AstrBot UI 没有明显展开嵌套 B站配置，也可以在顶层看到并填写 `bilibili_sessdata`。

同时新增扫码自动轮询配置：

- `bilibili_qr_auto_poll` / `bilibili.qr_auto_poll`
- `bilibili_qr_poll_interval` / `bilibili.qr_poll_interval`
- `bilibili_qr_poll_timeout` / `bilibili.qr_poll_timeout`

## 验证

### 单元与 E2E 测试

```bash
python astrbot_plugin_rconsole/tests/test_bilibili_auth.py
python astrbot_plugin_rconsole/tests/test_astrbot_stub_e2e.py
```

覆盖：

- 二维码生成；
- QR 图片文件生成；
- 未扫码状态；
- 登录成功状态；
- SESSDATA 保存提示；
- 已配置状态提示；
- 顶层 `bilibili_sessdata` 可被 `#rbs` 和能力诊断识别；
- schema 中顶层与嵌套 SESSDATA 均存在且为 `string`；
- `#rbq` 自动轮询关闭时只发送二维码不启动任务；
- 自动轮询成功时发送成功回调；
- 超时时发送超时回调；
- 重复 `#rbq` 会取消上一轮轮询，并保留新任务引用。

### 全量回归

已通过：

- `py_compile`
- `test_persistent_data_path.py`
- `test_round1_consistency_audit.py`
- `generate_full_parity_matrix.py`
- `test_bilibili_auth.py`
- `test_bilibili_video.py`
- `test_core_services.py`
- `test_astrbot_stub_e2e.py`
- `test_media_resolvers.py`
- `test_style_quantitative.py`
- `test_capability_probe.py`

## 使用方式

1. 发送：`#rbq`
2. Bot 返回 B站登录二维码；
3. 用 B站 App 扫码并确认；
4. 等待 Bot 自动回调成功/失败/过期/超时结果；
5. 登录成功后插件会自动写入 `bilibili.sessdata` 和顶层 `bilibili_sessdata`；
6. 如设置页仍显示为空，刷新页面或重载插件后再查看；如需手动复核状态，可发送：`#rbs`。

## 注意

- Matrix 等适配器日志里的 `Prepare to send -` 对纯图片或链式消息可能显示为空，这是 AstrBot/适配器日志展示问题；实际消息包含文字说明和二维码图片。
- 沙箱无法替用户真实扫码确认 B站账号，因此真实扫码成功需在用户 AstrBot 环境中验证；插件层自动回调、状态分支和保存逻辑已由测试覆盖。

