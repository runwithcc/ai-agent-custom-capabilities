# GitHub 认证与 macmini-ts 连通性恢复指南

## 当前诊断结论

截至 2026-04-11，本机的状态是：

- `gh auth status` 显示账号 `runwithcc` 仍然存在，但钥匙串里的 GitHub token 已失效。
- `ssh macmini-ts` 超时，说明通过 Tailscale 的 `macmini-clawpool.tailc25dfe.ts.net:22` 目前没有打通。
- `ssh macmini-lan 'echo ok'` 已经成功，说明：
  - Mac mini 的 SSH 服务是正常的。
  - 本机私钥 `~/.ssh/id_ed25519_macmini_codex` 可以正常登录该机器。
  - 当前可用的连通方式是局域网别名 `macmini-lan`。

## 一、恢复 GitHub 认证

在本机终端执行：

```bash
gh auth logout -h github.com -u runwithcc
gh auth login -h github.com -p https -w -s repo
gh auth status
```

预期结果：

- 浏览器会打开 GitHub 授权页。
- 完成授权后，`gh auth status` 不再出现 `The token in keyring is invalid`。

如果授权成功，后续就可以直接创建并推送仓库：

```bash
gh repo create runwithcc/ai-agent-custom-capabilities \
  --public \
  --source /Users/hiddenwangcc/Documents/Playground/docs/hermes-user-space/ai-agent-custom-capabilities \
  --remote origin \
  --push
```

## 二、恢复到 Mac mini 的可用连接

### 方案 A：先用已经可用的局域网连接

当前已经验证成功：

```bash
ssh macmini-lan 'echo ok'
```

如果你现在只是想先把 Hermes 部署跑起来，可以先直接把目标主机从 `macmini-ts` 换成 `macmini-lan`。

### 方案 B：恢复 `macmini-ts` 的 Tailscale 通道

当前现象不是密钥错误，而是 `22` 端口超时。这通常意味着下面几种情况之一：

- Mac mini 上的 Tailscale 在线，但 SSH 不走 Tailscale 路径。
- macOS 防火墙拦截了来自 Tailscale 接口的 SSH。
- Tailscale 节点名对应的入口没有把 `22` 暴露出来。

请在 Mac mini 上检查以下内容。

#### 1. 确认 Tailscale 在线

在 Mac mini 上执行：

```bash
tailscale status
tailscale ip -4
```

确认它显示在线，并记住它的 Tailscale IPv4。

#### 2. 确认系统 SSH 已开启

在 Mac mini 上执行：

```bash
sudo systemsetup -getremotelogin
sudo lsof -nP -iTCP:22 -sTCP:LISTEN
```

预期：

- `Remote Login: On`
- 有进程在监听 `*:22` 或 `0.0.0.0:22`

#### 3. 检查防火墙

在 Mac mini 上打开：

- 系统设置
- 网络
- 防火墙

确认：

- 防火墙没有拦截 `sshd-keygen-wrapper` / `sshd`
- 或者临时关闭防火墙后再测试一次 `ssh macmini-ts 'echo ok'`

#### 4. 直接测试 Tailscale IP 的 22 端口

在当前这台机器上执行：

```bash
nc -vz -G 5 <macmini_tailscale_ip> 22
ssh -o ConnectTimeout=5 clawpool@<macmini_tailscale_ip> 'echo ok'
```

如果 IP 可以通而主机名不通，说明是 `~/.ssh/config` 里 `HostName` 该改成 Tailscale IP。

## 三、推荐的稳定做法

为了不耽误 Hermes 当前部署，建议采用双通道策略：

- `macmini-lan`：同一局域网内优先使用，已经验证可用。
- `macmini-ts`：继续保留给远程场景，等 Tailscale SSH 路径修复后再切回。

## 四、我建议你现在就按这个顺序操作

1. 先执行 GitHub 重新登录命令，修复 `gh`。
2. 先用 `ssh macmini-lan 'echo ok'` 验证你本地到 Mac mini 仍然可用。
3. 如果你现在要部署 Hermes，先暂时使用 `macmini-lan`。
4. 等你能操作到 Mac mini 本机时，再按上面的 Tailscale 检查步骤修复 `macmini-ts`。

## 五、修复完成后的验收标准

以下四条都满足，就说明恢复完成了：

```bash
gh auth status
ssh macmini-lan 'echo ok'
ssh macmini-ts 'echo ok'
git -C /Users/hiddenwangcc/Documents/Playground/docs/hermes-user-space/ai-agent-custom-capabilities remote -v
```

预期：

- GitHub 认证成功
- `macmini-lan` 成功
- `macmini-ts` 成功
- Git 仓库已经有 `origin`
