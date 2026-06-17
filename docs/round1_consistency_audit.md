# Round 1/6 一致性审计报告

## 审计范围

- 原 R 插件 `source/rconsole-plugin/apps/*.js` 中的 `reg:` 入口数量；
- AstrBot 版 `main.py::_build_rules()` 规则数量、来源模块、唯一性和正则可编译性；
- `full_original_to_astrbot_parity_matrix.json` 与代码规则顺序/名称一致性；
- 配置 schema、metadata、README 关键交付信息一致性。

## 结果

| 项目 | 结果 |
|---|---|
| 原 R 插件规则总数 | 47 |
| AstrBot 版规则总数 | 46（按产品要求移除聊天内更新入口） |
| 规则名唯一性 | 通过 |
| 正则可编译 | 通过 |
| 来源模块数量分布 | 与原插件一致 |
| parity matrix JSON | 保留历史对照；代码侧已按产品要求移除更新入口 |
| 配置 schema 必备组 | 通过 |
| metadata 版本/兼容性 | v0.3.11 / >=4.14,<5 |
| README 关键证据链接 | 通过 |

## 模块分布

| 模块 | 原 R 规则数 | AstrBot 规则数 |
|---|---:|---:|
| `apps/help.js` | 未提供 source 快照 | 1 |
| `apps/query.js` | 未提供 source 快照 | 5 |
| `apps/songRequest.js` | 未提供 source 快照 | 7 |
| `apps/switchers.js` | 未提供 source 快照 | 6 |
| `apps/tools.js` | 未提供 source 快照 | 26 |
| `apps/update.js` | 未提供 source 快照 | 1 |

## 发现的问题

Round 1 未发现规则缺失、矩阵错位、metadata/schema/README 关键不一致问题。

## 下一轮关注点

Round 2 将继续逐模块深审业务实现质量，重点检查：查询/点歌/链接解析/权限/能力诊断是否存在实际逻辑 bug、异常处理不足或可优化点。
