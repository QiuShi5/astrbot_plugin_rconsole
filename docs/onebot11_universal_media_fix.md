# 统一富媒体发送模块报告

## 用户反馈

Matrix 已经没有问题；OneBot11 是 QQ 渠道，用户确认支持合并消息，并要求图片和文字作为一条消息发送，同时保持插件通用兼容。

## 根因判断

AstrBot 的 OneBot11 适配器平台名通常为 `aiocqhttp`，发送时会把 AstrBot 消息组件链转换成 OneBot JSON。

上一轮为规避 OneBot11 混合消息段差异，把 OneBot11 做成了全量分段发送。但用户确认当前 QQ/OneBot11 渠道支持合并图文，因此全分段会降低体验：

- 图片和文字不应拆成两条；
- QQ/OneBot11 可以把 `Plain + Image` 作为一条消息发送；
- 视频、音频、文件仍建议单独发送，避免部分 OneBot11 实现对 `Plain + Image + Video` 超复杂混合链处理不稳定；
- 插件需要兼顾 QQ 图文合并体验和跨协议失败兜底，同时避免解析器或插件入口直接调用某个适配器的私有发送 API。

## 修复内容

将富媒体发送层抽到 `services/output_sender.py`，所有解析器统一产出 `ROutput`，再交给 `OutputSender.prepare()` 和 `OutputSender.send()`：

- `main.py` 只负责规则分发、权限和解析器调用，不再持有媒体发送细节；
- `OutputSender` 从 `event.get_platform_name()`、`message_obj.platform_name`、`unified_msg_origin` 多来源识别平台能力；
- `OutputSender` 识别 `aiocqhttp`、`onebot`、`onebot11`、`cqhttp`、`napcat`、`lagrange`、`llonebot` 等保守实现；
- Matrix、Telegram 等非 QQ 平台：仍优先使用原链式发送，保持 Matrix 当前已验证体验；
- QQ/OneBot11：采用“图文合并 + 大媒体独立”的策略：
  1. 文本 + 图片合并为一条 chain 消息；
  2. 音频单独发送；
  3. 视频单独按 AstrBot Video 组件发送；
  4. 文件单独发送；
- 图文合并失败时，自动退回逐段文本/图片发送；
- 视频等媒体组件失败时，降级为可见文本提示 `[视频] /path/or/url`，避免静默失败。
- 远程视频统一在发送模块中按 `media_localize` 策略稳定化，默认下载为本地 `.mp4` 后按 AstrBot Video 组件发送。

## 验证

新增/更新 `tests/test_astrbot_stub_e2e.py`：

- `platform_name="matrix"`：验证仍把文本、图片、视频放入同一条 chain，保持 Matrix 原行为；
- `platform_name="aiocqhttp"`：验证 OneBot11/QQ 发送序列为：

```text
chain(text + image) → chain(video)
```

- 模拟 AstrBot 视频组件被事件拒绝：验证插件发送可见文本兜底，且不会直接调用适配器私有 bot API：

```text
[视频] /tmp/reject.mp4
```

这证明 QQ/OneBot11 下图片和文字会作为一条消息发送；视频先走 AstrBot Video 组件，失败后才文本兜底。

## 结果

当前版本保持为 `v0.3.3`，重新打包交付。

通用策略总结：

- Matrix：继续链式富媒体；
- QQ/OneBot11：文字+图片合并，视频/音频/文件独立；
- 其他平台：默认链式，失败自动逐段；
- 所有平台：最终至少有文本降级，不静默失败。
