# Round 4/6 真实 AstrBot / 适配器 / 外部工具链验证增强报告

## 验证范围

- 真实 AstrBot CLI 插件扫描；
- 真实 AstrBot Web 服务短时启动；
- 真实 AstrBot 消息组件 API 构造；
- 沙箱外部工具链存在性；
- `#R能力诊断` 输出可用性。

## 执行结果

### 1. 外部工具链探测

```json
{
  "ffmpeg": null,
  "yt-dlp": "/usr/local/bin/yt-dlp",
  "BBDown": null,
  "tdl": null,
  "aria2c": null
}
```

结论：当前沙箱有 `yt-dlp`，无 `ffmpeg/BBDown/tdl/aria2c`。因此通用媒体解析链可用；群语音转码、B站专用下载、Telegram 专用下载、aria2 下载链不能在沙箱真实执行。

### 2. 真实 AstrBot CLI 插件扫描

```bash
astrbot plug list
```

结果：真实 CLI 识别插件：

```text
astrbot_plugin_rconsole v0.3.0 PluginStatus.NOT_PUBLISHED ported-by-ai
```

### 3. 真实 AstrBot Web 服务短时启动

```bash
timeout 18 astrbot run -p 6201
```

结果：

```text
[INFO] Running on http://0.0.0.0:6201 (CTRL + C to quit)
```

退出码 124 来自 `timeout` 主动终止长驻服务，属于预期。

### 4. 真实消息组件 API 探针

```bash
.venv_astrbot_check/bin/python astrbot_plugin_rconsole/tests/test_runtime_adapter_probe.py
```

结果：`RUNTIME_ADAPTER_PROBE_OK`。

验证真实 AstrBot API 可构造：

- `Plain`
- `Image.fromURL/fromFileSystem`
- `Record.fromURL/fromFileSystem`
- `Video.fromURL/fromFileSystem`
- `File`

### 5. 能力诊断输出

`CapabilityService.probe()` 能输出：

- AstrBot 富媒体组件是否存在；
- 当前适配器名；
- B站 SESSDATA；
- 网易云 Cookie / 云盘 Cookie / 云盘 API；
- ffmpeg / BBDown / tdl / aria2c。

## 发现的问题与处理

未发现新的代码缺陷。确认当前沙箱无法真实执行的能力均为环境缺失：

- `ffmpeg` 缺失 → 群语音/音频转码不可执行；
- `BBDown` 缺失 → B站专用下载链不可执行；
- `tdl` 缺失 → Telegram 专用下载链不可执行；
- `aria2c` 缺失 → aria2 下载链不可执行；
- 未配置真实 Cookie/账号 → 扫码登录、云盘上传等不可执行。

这些均已通过 `#R能力诊断` 变成可执行前置检查，而非隐藏缺口。

## 100% 信心循环

已用真实 AstrBot CLI 和真实消息组件 API 获取最强可用运行证据；账号/适配器/外部二进制缺失项已明确，不伪造成功。
