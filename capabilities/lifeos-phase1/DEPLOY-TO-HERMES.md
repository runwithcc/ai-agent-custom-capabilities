# Deploy To Hermes

## 1. 这份文件解决什么

这份文件说明如何把 `LifeOS Phase1` 的当前最小接入版本部署到正在运行的 Hermes。

当前部署目标是：

- 在不触碰模型主调用链的前提下
- 只给 `记录入库` 链路增加 Phase 1 影子写入

## 2. 当前需要部署的文件

当前真实运行实例：

- 用户：`NewBornHermes`
- 服务：`com.newbornhermes.gateway`
- 工作目录：`/Users/NewBornHermes/.hermes/hermes-agent`

远端目标目录：

`/Users/NewBornHermes/.hermes/hermes-agent/gateway/platforms/`

需要更新的文件：

- `feishu.py`
- `lifeos_phase1_runtime.py`
- `record_feedback_contract.py`

其中：

- `feishu.py` 负责把影子写入挂到记录入库链路
- `lifeos_phase1_runtime.py` 负责 SQLite + Markdown 影子写入
- `record_feedback_contract.py` 负责把 event schema 翻译成更贴近你的即时反馈文案与卡片内容

## 3. 对主逻辑的影响边界

这次部署的设计原则是：

- 不改 `run_agent.py`
- 不改模型请求主链
- 不改普通对话回复逻辑
- 只在记录入库成功路径后追加一段旁路写入

所以即便影子写入失败，也只应记录 warning，不应影响主卡片/主回复继续返回。

## 4. 当前阻塞

本轮排查后确认，旧阻塞判断需要更新。

当前事实是：

- `macmini-ts` 仍然不通
- 但 `macmini-lan` 已可用
- 真正运行中的 Hermes 也不是 `hermes-svc`，而是 `NewBornHermes`
- 当前 SSH 登录用户 `clawpool` 对目标运行目录没有直接写权限

所以剩余阻塞已经收敛为：

- 需要通过 `sudo` 把文件写入 `NewBornHermes` 的 Hermes 目录
- 需要通过 `sudo launchctl kickstart -k system/com.newbornhermes.gateway` 重启服务

## 5. 已准备好的部署脚本

- [deploy-lifeos-phase1-shadow-to-hermes.sh](/Users/hiddenwangcc/Documents/Playground/docs/hermes-user-space/ai-agent-custom-capabilities/scripts/deploy-lifeos-phase1-shadow-to-hermes.sh)

当前脚本已经更新为：

- 默认走 `macmini-lan`
- 默认目标为 `NewBornHermes`
- 会先上传到远端临时目录
- 再通过 `sudo` 写入真实运行目录
- 会同时更新 `record_feedback_contract.py`
- 最后重启 `com.newbornhermes.gateway`

执行脚本时，需要在远端 `sudo` 提示出现后输入 Mac mini 上 `clawpool` 的管理员密码。
