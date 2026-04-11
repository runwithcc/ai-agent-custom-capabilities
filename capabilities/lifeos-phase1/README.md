# LifeOS Phase1 / Hermes 总控能力骨架

状态：in_progress  
日期：2026-04-11

## 1. 能力说明

这是当前最重要的一组自建能力之一。

它的目标是让 Hermes 不只是记录，而是逐步具备：

- 统一接入
- 第一轮解释
- 即时反馈
- 双轨留存
- 模块台账
- 路由分发
- 监督推进

## 2. 当前已经形成的关键资产

讨论与设计：

- [LifeOS 总体需求 V1](/Users/hiddenwangcc/Documents/Playground/docs/plans/2026-04-11-lifeos-overall-requirements-v1.md)
- [Hermes Phase1 详细方案](/Users/hiddenwangcc/Documents/Playground/docs/plans/2026-04-11-hermes-phase1-detailed-plan.md)
- [Hermes Memory Contract V1](/Users/hiddenwangcc/Documents/Playground/docs/plans/2026-04-11-hermes-memory-contract-v1.md)
- [Hermes Feedback Contract V1](/Users/hiddenwangcc/Documents/Playground/docs/plans/2026-04-11-hermes-feedback-contract-v1.md)
- [Hermes 全局模块方案 V1](/Users/hiddenwangcc/Documents/Playground/docs/plans/2026-04-11-hermes-global-module-plan-v1.md)
- [LifeOS Module Ledger V1](/Users/hiddenwangcc/Documents/Playground/docs/plans/2026-04-11-lifeos-module-ledger-v1.md)
- [Route Registry V1](/Users/hiddenwangcc/Documents/Playground/docs/plans/2026-04-11-route-registry-v1.md)
- [Supervisor Skeleton V1](/Users/hiddenwangcc/Documents/Playground/docs/plans/2026-04-11-supervisor-skeleton-v1.md)

存储与执行：

- [Phase 1 SQLite 表结构](/Users/hiddenwangcc/Documents/Playground/db/lifeos_phase1_schema.sql)
- [Phase 1 存储映射合同](/Users/hiddenwangcc/Documents/Playground/lifeos_canon/phase1-storage-map-v1.yaml)
- [Feishu 多维表字段规范](/Users/hiddenwangcc/Documents/Playground/lifeos_canon/bitable-schema-v1.yaml)
- [Feishu 初始化脚本](/Users/hiddenwangcc/Documents/Playground/scripts/setup_lifeos_bitable_phase1.js)
- [Hermes 影子写入运行时](/Users/hiddenwangcc/Documents/Playground/migration/hermes-20260409/remote-repo/lifeos_phase1_runtime.py)

专属目录自带副本：

- [assets/lifeos_phase1_schema.sql](/Users/hiddenwangcc/Documents/Playground/docs/hermes-user-space/ai-agent-custom-capabilities/capabilities/lifeos-phase1/assets/lifeos_phase1_schema.sql)
- [assets/phase1-storage-map-v1.yaml](/Users/hiddenwangcc/Documents/Playground/docs/hermes-user-space/ai-agent-custom-capabilities/capabilities/lifeos-phase1/assets/phase1-storage-map-v1.yaml)
- [assets/bitable-schema-v1.yaml](/Users/hiddenwangcc/Documents/Playground/docs/hermes-user-space/ai-agent-custom-capabilities/capabilities/lifeos-phase1/assets/bitable-schema-v1.yaml)
- [assets/setup_lifeos_bitable_phase1.js](/Users/hiddenwangcc/Documents/Playground/docs/hermes-user-space/ai-agent-custom-capabilities/capabilities/lifeos-phase1/assets/setup_lifeos_bitable_phase1.js)
- [assets/lifeos_phase1_runtime.py](/Users/hiddenwangcc/Documents/Playground/docs/hermes-user-space/ai-agent-custom-capabilities/capabilities/lifeos-phase1/assets/lifeos_phase1_runtime.py)
- [assets/runtime-host-overrides/feishu.py](/Users/hiddenwangcc/Documents/Playground/docs/hermes-user-space/ai-agent-custom-capabilities/capabilities/lifeos-phase1/assets/runtime-host-overrides/feishu.py)

## 3. 当前实现状态

已完成：

- Phase 1 合同层
- 存储结构层
- Feishu 字段规范层
- Hermes 记录入库链路的影子写入接入
- 专属能力目录的可迁移副本建设

未完成：

- 接 GitHub 远端自动发布流程
- 把本目录变成每次变更的强制落点
- 把更多已有脚本逐步迁到这个专属目录下
- 把当前版本真正部署到正在运行的 Hermes 宿主机

## 4. 相关讨论记录

- [2026-04-11 Hermes LifeOS Phase1 Build Log](/Users/hiddenwangcc/Documents/Playground/docs/hermes-user-space/ai-agent-custom-capabilities/sessions/2026-04-11-hermes-lifeos-phase1-build-log.md)

## 5. 部署说明

- [DEPLOY-TO-HERMES.md](/Users/hiddenwangcc/Documents/Playground/docs/hermes-user-space/ai-agent-custom-capabilities/capabilities/lifeos-phase1/DEPLOY-TO-HERMES.md)
