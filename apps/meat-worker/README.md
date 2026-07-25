# 肉机助手（MeatWorker）

> **标识**：本目录是 Agent Platform 的 **本机出站手**，打包为 `MeatWorker.exe`。  
> **不是** Commander Temu Agent；二者同角色、不同控制面。

## 作用

- 出站连接服务器 `platform_mcp`：`/worker/heartbeat|claim|complete`
- 执行需本机登录/浏览器的黑盒 Job（当前：`douyin_collect_hot_keywords` 蝉妈妈采集）
- 托盘显示在线/登录状态（绿 / 黄 / 红）

## 构建与拷贝

```bat
REM 在仓库根目录
scripts\build-meat-worker.bat
```

产物：`dist\meat-worker\`（**整夹**拷到空闲机）。  
说明：[`docs/wip/meat-worker-exe.md`](../../docs/wip/meat-worker-exe.md)

## 源码结构

```
apps/meat-worker/
├── __main__.py          # 入口（托盘 / --headless）
├── worker_core.py       # claim 循环 + job.type handler 注册
├── config.py            # AppData / sidecar config.json
├── handlers/            # 按 type 扩展（勿一工具一 EXE）
├── ui/tray_app.py       # 托盘 + 状态窗
├── config.example.json
└── meat_worker.spec     # PyInstaller onedir
```

## 配置

`config.json`（与 EXE 同目录或 `%APPDATA%\agent-platform-meat\`）：

- `worker_url`：默认 `https://www.yoto.work/platform-mcp`
- `worker_token`：与服务器 `DOUYIN_WORKER_TOKEN` 一致（**禁止提交 git**）
- `worker_id`：如 `闲置机-1`
