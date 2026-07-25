# 肉机助手 EXE（空闲机直接用）

> 现行 · 2026-07-25 · 不并入 Commander Agent

## 服务器侧（已部署）

- MCP：`https://www.yoto.work/platform-mcp`（含 `/worker/heartbeat|claim|complete`）
- 与 EXE 共用 `DOUYIN_WORKER_TOKEN`

## 空闲机（推荐 · 无需打包）

仓库已提交预构建包：

**[`apps/meat-worker/release/`](../../apps/meat-worker/release/)**

```text
apps/meat-worker/release/
  MeatWorker.exe
  _internal/
  config.json          （填 token）
  config.example.json
  README.txt
```

步骤：

1. 从 GitHub 下载/克隆后，只拷贝 `apps/meat-worker/release/` 到空闲机（或 sparse checkout 该目录）
2. 编辑 `config.json`：
   - `worker_url`: `https://www.yoto.work/platform-mcp`
   - `worker_token`: 与服务器一致（安全渠道传递，勿把真实 Token 推回 git）
   - `worker_id`: 如 `闲置机-1`
3. 空闲机安装 **Chrome**
4. 运行 `MeatWorker.exe`
5. 托盘 → **登录蝉妈妈** → 图标变绿
6. 服务器「工具状态」显示抖音肉机在线

配置与登录态另存：`%APPDATA%\agent-platform-meat\`

## 开发者重建（可选）

```bat
scripts\build-meat-worker.bat
```

产物写入 `apps/meat-worker/release/`（再 commit 推送）。

## 托盘状态

| 颜色 | 含义 |
|------|------|
| 绿 | 心跳成功且蝉妈妈已登录 |
| 黄 | 心跳成功但未登录（need_login） |
| 红 | 心跳失败 / Token 错 / 网络不通 |
| 灰 | 已停止 |

## 明确不做

- 把 Temu / Commander 塞进本 EXE  
- 要求空闲机拉全仓再跑脚本打包（预构建包已提供）  
- Token 打进仓库
