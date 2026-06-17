# 真实 AstrBot 运行时与适配器能力验证报告（增强版）

## 目标

回应审查意见：仅有 stub 测试和 import 检查不足以证明插件运行时兼容。本轮增加真实 AstrBot CLI、插件元数据扫描、Web 服务短时启动、真实消息组件构造和适配器能力探针。

## 真实 AstrBot 包与 CLI

环境：隔离 venv `.venv_astrbot_check`，安装 `astrbot==4.14.6`。

### CLI 可用性

```bash
astrbot --help
astrbot init --help
astrbot plug --help
astrbot run --help
```

结果：CLI 正常输出版本 `4.14.6`，支持 `conf/init/plug/run`，`plug` 支持 `install/list/new/remove/search/update`。

### 插件元数据扫描

由于 `astrbot init` 默认会交互确认并下载 Dashboard，沙箱非交互环境会在 Dashboard 步骤 abort。为验证插件扫描，按 AstrBot CLI 源码要求手动创建最小根目录：

```text
astrbot_runtime_probe/
  .astrbot
  data/config/
  data/plugins/astrbot_plugin_rconsole/
  data/temp/
```

执行：

```bash
astrbot plug list
```

结果：真实 CLI 成功识别插件：

```text
未发布的插件
名称                   版本         状态         作者              描述
-------------------------------------------------------------------------------------
astrbot_plugin_rconsole v0.3.0     PluginStatus.NOT_PUBLISHED ported-by-ai    将 Yunzai-Bot R插件迁移到 AstrBot，复刻...
```

这证明 `metadata.yaml` 在真实 AstrBot 插件扫描逻辑下可读取，插件目录结构可被识别。

### 真实 AstrBot Web 服务短时启动

`astrbot run` 默认检查 Dashboard；为避免沙箱交互下载，预置 `data/dist/assets/version=4.14.6`。执行：

```bash
timeout 45 astrbot run -p 6199
```

结果：

```text
[INFO] Running on http://0.0.0.0:6199 (CTRL + C to quit)
```

命令最终由 `timeout` 终止，退出码 124 是长驻服务被外部终止的预期结果。该结果证明真实 AstrBot CLI 能启动到 Web 服务监听阶段。

## 真实消息组件 API 探针

新增测试：`tests/test_runtime_adapter_probe.py`，使用真实 `astrbot.api.message_components` 验证：

- `Plain`
- `Image.fromURL` / `Image.fromFileSystem`
- `Record.fromURL` / `Record.fromFileSystem`
- `Video.fromURL` / `Video.fromFileSystem`
- `File`

执行：

```bash
.venv_astrbot_check/bin/python astrbot_plugin_rconsole/tests/test_runtime_adapter_probe.py
```

结果：

```text
RUNTIME_ADAPTER_PROBE_OK
component_construction: Plain, Image, Record, Video, File
```

这证明插件 `_send_output()` 构造的图片、音频、视频、文件消息链使用真实 AstrBot API 签名是有效的。

## 适配器强耦合能力诊断

新增插件命令：

```text
/rcap
#R能力诊断
#R运行诊断
```

新增服务：`services/capabilities.py`，可检测：

- AstrBot 富媒体组件是否可用；
- 当前消息适配器名称；
- B站 SESSDATA 是否配置；
- 网易云 Cookie / 云盘 Cookie / 云盘 API 是否配置；
- `ffmpeg`、`BBDown`、`tdl`、`aria2c` 是否安装；
- Record/Video/File 等组件是否存在。

这让“扫码登录、群文件/群语音、网易云云盘上传”等原 R 插件强耦合能力不再只是泛泛说明，而是有可执行诊断入口。真实发送仍需用户的 AstrBot 适配器账号和平台授权。

## 仍不能在沙箱中伪造成功的项目

以下能力必须依赖真实平台账号、Cookie、群聊上下文或适配器接口：

- B站扫码登录二维码确认、SESSDATA 写入；
- 网易云扫码登录、云盘列表、云盘上传；
- QQ 群文件上传、群语音发送；
- Telegram 私有频道下载；
- 需 Cookie 的微博/小红书/B站高画质/会员内容。

本轮已提供最强可用证据：真实 CLI 扫描、真实 Web 服务启动、真实消息组件构造、stub 端到端发送降级和能力诊断命令。上述账号/适配器能力不在沙箱中伪造成功。
