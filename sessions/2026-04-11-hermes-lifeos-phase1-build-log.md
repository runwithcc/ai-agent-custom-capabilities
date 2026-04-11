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
