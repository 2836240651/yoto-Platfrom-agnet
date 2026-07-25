---
name: social-media-publish
description: 多社媒发布 — 素材+账号 → automedia MCP → 肉机 login-agent（黑盒）
---

# 多社交媒体发布

契约：Skill 只做缺参确认 / 调 MCP / 人话总结。  
**禁止**本仓 Playwright；浏览器在 Temu 肉机同机 login-agent。

## 工作流

1. 确认视频路径（网关可读）、平台 type（1–5）、账号 cookie 文件名、标题
2. `social_publish_submit`（内含上传）
3. `social_publish_status` 轮询至 success/failed（在 finalize 步内完成）
4. TikTok（type=5）助手离线 → 任务失败，禁止假成功

## MCP

| 步骤 | MCP Tool |
|------|----------|
| 可选 | social_list_accounts |
| 提交 | social_publish_submit |
| 状态 | social_publish_status |

## 平台 type

1 小红书 · 2 视频号 · 3 抖音 · 4 快手 · 5 TikTok
