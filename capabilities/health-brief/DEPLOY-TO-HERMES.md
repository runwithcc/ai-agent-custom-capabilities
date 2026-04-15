# Deploy To Hermes

## 1. 这份文件解决什么

这份文件说明如何把“健康晨报 / 晚报能力”部署到正在运行的 Hermes 实例。

目标是：

- Hermes 每天早晨 06:00 推送身体状态晨报
- Hermes 每天晚上 21:00 推送身体状态晚报
- 数据来自群晖健康汇总接口

## 2. 先决条件

1. 群晖健康同步服务已在线  
   当前接口：
   - `http://100.98.2.78:8780/api/health/summary/latest`

2. Hermes 宿主机可以访问该接口  
   在 Hermes 宿主机先验证：

```bash
curl -s http://100.98.2.78:8780/api/health/summary/latest | head
```

3. Hermes 的目标投递聊天已经设为 home channel  
   在你希望接收定时推送的 Hermes 聊天里执行：

```text
/sethome
```

官方 cron 行为要点：

- Hermes cron 会在 fresh session 中运行
- 从 CLI 创建时可以投递到 `feishu` home channel

## 3. 需要部署的文件

推荐把 prompt 资产放到：

```bash
~/.hermes/custom/health-brief/
```

另外，Hermes 的 cron 预执行脚本必须放在：

```bash
~/.hermes/scripts/
```

需要拷贝过去的文件：

- `scripts/hermes-health-fetch.py`
- `assets/morning-health-brief-cron-prompt.md`
- `assets/evening-health-brief-cron-prompt.md`

## 4. 安装脚本

在 Hermes 宿主机执行：

```bash
mkdir -p ~/.hermes/custom/health-brief
mkdir -p ~/.hermes/scripts
```

然后把以下文件放进去：

- `~/.hermes/scripts/hermes_health_fetch.py`
- `morning-health-brief-cron-prompt.md`
- `evening-health-brief-cron-prompt.md`

再执行：

```bash
chmod +x ~/.hermes/scripts/hermes_health_fetch.py
```

## 5. 建立 cron

### 5.1 早晨 06:00

```bash
hermes cron create "0 6 * * *" "$(cat ~/.hermes/custom/health-brief/morning-health-brief-cron-prompt.md)" --name "morning-health-brief" --script hermes_health_fetch.py --deliver feishu:<chat_id>
```

### 5.2 晚上 21:00

```bash
hermes cron create "0 21 * * *" "$(cat ~/.hermes/custom/health-brief/evening-health-brief-cron-prompt.md)" --name "evening-health-brief" --script hermes_health_fetch.py --deliver feishu:<chat_id>
```

## 6. 查看当前 cron

```bash
hermes cron list
```

预期应看到两条任务：

- `morning-health-brief`
- `evening-health-brief`

## 7. 当前已知注意事项

1. 现在的健康数据还存在多来源重叠  
   特别是睡眠，可能同时来自 Apple Watch 和 AutoSleep。

2. 这不会阻止晨报/晚报上线  
   但后续最好加来源优先级规则。

3. 如果 Hermes 宿主机有代理环境，抓取脚本已经默认忽略系统代理。
