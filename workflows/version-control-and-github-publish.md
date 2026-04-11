# 版本控制与 GitHub 发布流程

## 1. 目标

这份流程定义：

- 如何让 Agent 自建功能目录保持 git 可追踪
- 如何把每次更新同步到 GitHub
- 如何避免“做了很多，但没有沉淀、没有版本、没有远端”

## 2. 本地规则

每次完成以下任一类内容后，都应进入一次 git 变更周期：

- 新增能力设计
- 更新流程文档
- 新增关键讨论记录
- 新增脚本或脚本索引
- 重要结构或字段调整

## 3. Git 提交最小单位

一次提交应尽量对应一个清晰变化，例如：

- 新增一个能力骨架
- 完成一次字段设计升级
- 补一轮讨论记录与总结
- 接入一个新流程

不要把完全无关的内容混在一个提交里。

## 4. GitHub 远端策略

目标远端仓库名称：

`AI 代理人自建功能`

推荐设置：

- GitHub 用户：`runwithcc`
- 可见性：推荐 `private`

推荐 repo slug：

`ai-agent-custom-capabilities`

推荐远端地址格式：

`git@github.com:runwithcc/<repo-name>.git`

或

`https://github.com/runwithcc/<repo-name>.git`

## 5. 当前实施状态

当前工作区现实状态：

- 本地 git 已初始化
- 但 아직没有 commit
- 也没有 remote

所以应按这个顺序推进：

1. 先建立本地标准目录与文件
2. 形成第一批正式提交
3. 创建或确定 GitHub 目标仓库
4. 添加 remote
5. push 到远端

## 6. 以后每次更新的固定动作

每次重要更新后，Agent 应优先做：

1. 补写 `sessions/` 记录
2. 更新对应 `capabilities/` 文档
3. 更新 `REGISTRY.yaml` 中的状态
4. git 提交
5. push 到 GitHub

## 7. 如果未来更换主 Agent

新的 Agent 必须先读取：

- `README.md`
- `AGENT-ONBOARDING.md`
- `REGISTRY.yaml`
- 最近的 session 记录

然后继续沿用这里的版本控制流程。
