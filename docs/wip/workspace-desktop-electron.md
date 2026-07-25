# TUODIAO Workspace 桌面客户端

> 状态：现行 · 2026-07-25  
> 与 [`meat-worker-exe.md`](./meat-worker-exe.md) **分离**。

## 为何不是纯线上薄壳

探测：`https://www.yoto.work/agent-platform/` 目前 **只反代 FastAPI**，根路径返回 JSON 404，**没有**部署 `apps/web` SPA。  
因此成员端 EXE 改为：

1. 内置 `web-dist`（Vite 构建）
2. 本机 `127.0.0.1` 静态服务 + `/api` 代理到 `https://www.yoto.work/agent-platform/api`

等线上挂上前端静态资源后，可用环境变量 `YOTO_WORKSPACE_URL` 切回纯远程 SPA。

## 谁装什么

```
成员笔记本 ──► TUODIAO.exe（内置 UI）──► 代理 API ──► yoto.work/agent-platform
闲置主机   ──► MeatWorker.exe ──► 出站 claim
```

## 打包

```bat
scripts\build-workspace-desktop.bat
```

产物：`apps/workspace-desktop/release/TUODIAO-*-portable.exe` / `*-win-x64.exe`
