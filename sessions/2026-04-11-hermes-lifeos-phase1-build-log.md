# 2026-04-11 Hermes LifeOS Phase1 Build Log

日期：2026-04-11  
参与者：hiddenwangcc / Codex  
状态：active

## 1. 这轮讨论在解决什么

这轮的核心不是“做一个记录工具”，而是逐步把 Hermes 建成你的 LifeOS 总控大脑。

其中最关键的一条主线是：

`自然表达 -> event schema -> 第一轮解释 -> 即时反馈 -> 双轨留存 -> 模块台账 -> 路由 -> 监督`

## 2. 用户的关键期待

这一轮里，你反复强调了几件事：

- 你要的不是普通记录，而是以你为中心、可持续进化的 LifeOS 总控系统
- 原始表达必须完整留存
- Hermes 必须对 raw 内容做第一轮解释
- 反馈不能只是纯文本总结，而要有被理解感，并适合飞书卡片
- 后续要有数据库、双份容灾、可迁移第二记忆体
- 所有系统模块都应该被台账化、可监督、可推进

后面你进一步提出：

- 每一次开发设定与讨论过程都要留下文档
- 所有自建脚本、能力、流程都应该进入一个属于你的专门文件夹
- 这个文件夹要用 git 管理，并持续推到 GitHub

## 3. 这轮做出的关键判断

### 3.1 先做元模块，不先铺领域模块

先做：

- Memory Contract
- Feedback Contract
- Module Ledger
- Route Registry
- Supervisor Skeleton

这是为了让 Hermes 先拥有“管理能力”，而不是只会回复。

### 3.2 用影子写入接入 Hermes

为了避免破坏 Hermes 主回复链，采用了：

- 不碰 `run_agent.py`
- 不碰模型请求主链
- 只在记录入库链上增加 Phase 1 影子写入

这样即使影子写入失败，也不会把主回复打挂。

### 3.3 用户需要自己的专属能力资产库

这不是可选项，而是长期系统建设的基础设施。

因为未来：

- 可能换 Agent
- 可能换宿主程序
- 可能换运行环境

但你的自建能力资产不应该跟着消失。

## 4. 本轮产出的关键资产

### 4.1 设计文档

- LifeOS 总体需求文档
- Hermes Phase1 详细方案
- Memory Contract V1
- Feedback Contract V1
- 全局模块方案 V1
- Module Ledger V1
- Route Registry V1
- Supervisor Skeleton V1

### 4.2 存储与实现资产

- SQLite Phase 1 表结构
- 存储映射合同
- Bitable 字段规范
- Bitable 初始化脚本
- Hermes Phase 1 影子写入运行时

### 4.3 用户专属目录

本次新建了：

`docs/hermes-user-space/ai-agent-custom-capabilities/`

它将作为你后续自建 Agent 能力的正式资产目录。

## 5. 当前未完成项

- GitHub 目标仓库 `AI 代理人自建功能` 尚未接入当前本地仓库
- 当前工作区还没有正式 commit
- 当前有大量既有脚本还分散在工作区各处，尚未逐步迁入这个专属目录

## 6. 下一步建议

最自然的下一步是：

1. 确定 GitHub 目标 repo 的创建方式与可见性
2. 把当前工作区首次提交成一个正式版本
3. 接上远端
4. 以后所有关键开发讨论都持续写入 `sessions/`

## 7. 这轮最重要的结果

现在开始，你的 Agent 自建过程不再只发生在聊天里，而是开始进入：

- 可阅读
- 可迁移
- 可版本控制
- 可被新 Agent 接手

的正式资产状态。

## 8. 追加问题定义：记录入库反馈链路修正

在真实 Hermes 上查看连续 3 条记录入库结果后，识别出以下问题：

1. 不同内容被压成同一份反馈
- 3 条 event 的 raw 内容、路由和信号并不相同
- 但 feedback title / summary / suggestion 几乎完全一致
- 根因：`record_feedback_contract.py` 对 `Agent` / `Codex` / `Hermes` 相关表达的分类过宽，导致大量内容被压进同一个 `agent strategy note` 模板

2. `record_only` 与实际反馈行为不一致
- 数据库里 `feedback_mode=record_only`
- 但前台链路仍然会构造完整反馈卡片并尝试发送
- 根因：record-ingest 前台反馈扩展逻辑与 Phase1 shadow write 的 `feedback_mode` 判定没有对齐

3. 飞书卡片链路不够稳
- 日志中出现过：`AttributeError: 'FeishuAdapter' object has no attribute 'send_card'`
- 这会导致记录入库链路在发卡片时直接报错
- 根因：前台卡片发送缺少安全降级

4. 反馈生成器没有纳入当前部署资产
- 之前部署脚本只更新 `feishu.py` 与 `lifeos_phase1_runtime.py`
- 实际控制反馈内容的 `record_feedback_contract.py` 没有一起纳管和部署

### 本轮修正动作

1. 收窄 `agent strategy note` 判定范围
2. 新增更细的子类型：
- `assetization`
- `mobile_handoff`
- `workflow_sop`
- `runtime_strategy`
3. 让 record-ingest 在“内容明显需要反馈”但原始 `output_mode=仅记录` 时自动提升为 `轻反馈`
4. 让飞书卡片发送在 `send_card` 不可用时自动降级回文本
5. 把 `record_feedback_contract.py` 纳入专属资产目录与正式部署脚本
