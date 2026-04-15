# Hermes 健康晨报 / 晚报能力

状态：in_progress  
日期：2026-04-15

## 1. 能力说明

这组能力让 Hermes 不只是“知道你有健康数据”，而是开始承担固定频率的健康管理工作：

- 早晨 06:00 推送一份身体状态晨报
- 晚上 21:00 推送一份身体状态晚报
- 读取群晖上的健康汇总结果
- 用同一套风格给出可执行建议

它服务的是“个人健康闭环”，训练只是其中一个维度。

## 2. 当前已经落下的资产

Hermes 读取脚本：

- [scripts/hermes-health-fetch.py](/Users/hiddenwangcc/Documents/Playground/docs/hermes-user-space/ai-agent-custom-capabilities/scripts/hermes-health-fetch.py)
- 工作区运行副本：[scripts/hermes_health_fetch.py](/Users/hiddenwangcc/Documents/Playground/scripts/hermes_health_fetch.py)

群晖健康同步服务：

- [services/health-sync/src/server.js](/Users/hiddenwangcc/Documents/Playground/services/health-sync/src/server.js)
- [services/health-sync/src/lib/summary.js](/Users/hiddenwangcc/Documents/Playground/services/health-sync/src/lib/summary.js)
- [deploy/synology/health-sync/docker-compose.yml](/Users/hiddenwangcc/Documents/Playground/deploy/synology/health-sync/docker-compose.yml)
- 留存镜像：
  [assets/synology-health-sync/README.md](/Users/hiddenwangcc/Documents/Playground/docs/hermes-user-space/ai-agent-custom-capabilities/capabilities/health-brief/assets/synology-health-sync/README.md)

设计与说明：

- [Hermes Personal Health Loop on Synology](/Users/hiddenwangcc/Documents/Playground/docs/plans/2026-04-15-hermes-health-loop-design.md)
- [Hermes Daily Health Brief Prompt](/Users/hiddenwangcc/Documents/Playground/docs/plans/2026-04-15-hermes-health-daily-brief-prompt.md)
- [DEPLOY-TO-HERMES.md](/Users/hiddenwangcc/Documents/Playground/docs/hermes-user-space/ai-agent-custom-capabilities/capabilities/health-brief/DEPLOY-TO-HERMES.md)

Prompt 资产：

- [assets/morning-health-brief-prompt.md](/Users/hiddenwangcc/Documents/Playground/docs/hermes-user-space/ai-agent-custom-capabilities/capabilities/health-brief/assets/morning-health-brief-prompt.md)
- [assets/evening-health-brief-prompt.md](/Users/hiddenwangcc/Documents/Playground/docs/hermes-user-space/ai-agent-custom-capabilities/capabilities/health-brief/assets/evening-health-brief-prompt.md)
- [assets/morning-health-brief-cron-prompt.md](/Users/hiddenwangcc/Documents/Playground/docs/hermes-user-space/ai-agent-custom-capabilities/capabilities/health-brief/assets/morning-health-brief-cron-prompt.md)
- [assets/evening-health-brief-cron-prompt.md](/Users/hiddenwangcc/Documents/Playground/docs/hermes-user-space/ai-agent-custom-capabilities/capabilities/health-brief/assets/evening-health-brief-cron-prompt.md)
- [assets/runtime-file-index.md](/Users/hiddenwangcc/Documents/Playground/docs/hermes-user-space/ai-agent-custom-capabilities/capabilities/health-brief/assets/runtime-file-index.md)

效果示例：

- [assets/example-output-2026-04-15.md](/Users/hiddenwangcc/Documents/Playground/docs/hermes-user-space/ai-agent-custom-capabilities/capabilities/health-brief/assets/example-output-2026-04-15.md)

## 3. 当前实现状态

已完成：

- iPhone -> 群晖 -> 健康汇总接口跑通
- 群晖保留 raw + daily + latest summary
- Hermes 外部读取脚本就绪
- 晨报 / 晚报 prompt 就绪
- 真实数据样本已导入并重建

未完成：

- 把两条 cron 真正创建到 Hermes 运行实例
- 处理健康数据多来源冲突，例如睡眠同时来自 Apple Watch 与 AutoSleep
- 根据你实际阅读感受继续收紧文风和建议密度

## 4. 设计边界

- 不做医疗诊断
- 只根据实际健康汇总给建议
- 风险提醒只做“值得关注的信号”
- 当数据不全时，优先提醒数据边界，不硬编结论

## 5. 下一步

1. 在 Hermes 主实例上安装抓取脚本
2. 设定 06:00 与 21:00 两条 cron
3. 观察 3 到 5 天的真实推送效果
4. 再决定要不要加“来源优先级”和“周报/月报”
