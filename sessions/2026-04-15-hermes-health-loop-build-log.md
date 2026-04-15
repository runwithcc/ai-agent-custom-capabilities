# 2026-04-15 Hermes Health Loop Build Log

## 1. 这次推进解决了什么

这次推进把“iPhone 健康数据 -> 群晖 -> Hermes 健康简报”从一个想法推进成了可运行链路。

核心结果：

- 健康数据已经可以从 Health Auto Export 进到群晖
- 群晖会保留 raw、daily、daily-summary 三层数据
- Hermes 在别处运行时，也能通过 HTTP 拉取 summary
- 晨报 / 晚报 prompt 已经成型
- 已经写出一份基于真实快照的效果示例

## 2. 群晖侧当前状态

群晖服务：

- `hermes-health-sync`

当前接口：

- `http://100.98.2.78:8780/api/health/summary/latest`

当前落盘：

- raw uploads
- daily per-date JSON
- latest `daily-summary.json`

## 3. 当前确认过的真实数据

已经确认写入并被重建的指标包括：

- 睡眠
- 静息心率
- HRV
- 心率
- 步数
- 活动能量
- 血氧
- 呼吸频率
- VO2 max
- 锻炼记录

## 4. 当前尚未完全解决的点

- 睡眠仍可能存在多来源重叠
- `首选来源` 现在没有强制限制
- 还没有把两条 cron 真正落到 Hermes 主实例

## 5. 新增留存资产

能力目录：

- `capabilities/health-brief/`

新增内容包括：

- 能力 README
- 部署说明
- 晨报 prompt
- 晚报 prompt
- 抓取脚本副本
- 示例输出

## 6. 下一步建议

1. 在 Hermes 主实例部署 `hermes-health-fetch.py`
2. 创建 06:00 与 21:00 两条 cron
3. 看 3 到 5 天真实推送
4. 再处理数据源优先级
