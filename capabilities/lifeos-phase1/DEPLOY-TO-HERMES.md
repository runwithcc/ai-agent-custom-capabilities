# Deploy To Hermes

## 1. 这份文件解决什么

这份文件说明如何把 `LifeOS Phase1` 的当前最小接入版本部署到正在运行的 Hermes。

当前部署目标是：

- 在不触碰模型主调用链的前提下
- 只给 `记录入库` 链路增加 Phase 1 影子写入

## 2. 当前需要部署的文件

远端目标目录：

`/Users/hermes-svc/Agents/hermes-agent/gateway/platforms/`

需要更新的文件：

- `feishu.py`
- `lifeos_phase1_runtime.py`

其中：

- `feishu.py` 负责把影子写入挂到记录入库链路
- `lifeos_phase1_runtime.py` 负责 SQLite + Markdown 影子写入

## 3. 对主逻辑的影响边界

这次部署的设计原则是：

- 不改 `run_agent.py`
- 不改模型请求主链
- 不改普通对话回复逻辑
- 只在记录入库成功路径后追加一段旁路写入

所以即便影子写入失败，也只应记录 warning，不应影响主卡片/主回复继续返回。

## 4. 当前阻塞

本轮实际部署没有完成，原因不是代码问题，而是外部环境问题：

- 当前机器访问 `macmini-ts` 超时
- 所以无法真正把文件发到正在运行的 Hermes 宿主机上

## 5. 已准备好的部署脚本

- [deploy-lifeos-phase1-shadow-to-hermes.sh](/Users/hiddenwangcc/Documents/Playground/docs/hermes-user-space/ai-agent-custom-capabilities/scripts/deploy-lifeos-phase1-shadow-to-hermes.sh)

等网络恢复后，可直接用它执行部署。
