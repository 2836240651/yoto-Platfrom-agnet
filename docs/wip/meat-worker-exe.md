# 肉机助手 EXE（空闲机拷贝）

> 现行 · 2026-07-25 · 不并入 Commander Agent

## 服务器侧（已部署）

- MCP：`https://www.yoto.work/platform-mcp`（含 `/worker/heartbeat|claim|complete`）
- 与 EXE 共用 `DOUYIN_WORKER_TOKEN`

## 本机构建

```bat
scripts\build-meat-worker.bat
```

产物目录（**整夹拷贝**到空闲机）：

```text
dist\meat-worker\
  MeatWorker.exe
  _internal\
  config.json          （填 token）
  config.example.json
```

## 空闲机步骤

1. 拷贝整个 `dist\meat-worker\` → 如 `D:\meat-worker\`
2. 编辑 `config.json`：
   - `worker_url`: `https://www.yoto.work/platform-mcp`
   - `worker_token`: 与服务器一致（安全渠道传递，勿进 git）
   - `worker_id`: 如 `闲置机-1`
3. 空闲机建议安装 **Chrome**（默认 `use_system_chrome: true`）
4. 运行 `MeatWorker.exe`
5. 托盘右键 → **登录蝉妈妈** → 扫码/密码 → 图标变绿
6. 服务器 Web「工具状态」应显示「抖音肉机（蝉妈妈）在线已登录」

配置与登录态还落在：`%APPDATA%\agent-platform-meat\`（日志、Chrome profile）。

## 托盘状态

| 颜色 | 含义 |
|------|------|
| 绿 | 心跳成功且蝉妈妈已登录 |
| 黄 | 心跳成功但未登录（need_login） |
| 红 | 心跳失败 / Token 错 / 网络不通 |
| 灰 | 已停止 |

## 开发入口（不打包）

```bat
scripts\start-douyin-meat-worker.bat
python -m apps.meat-worker --headless
```

（模块路径：在 `apps\meat-worker` 下 `python -m __main__` 或 `PYTHONPATH=apps\meat-worker python -m __main__`）

## 明确不做

- 把 Temu / Commander 塞进本 EXE  
- 单文件 onefile（Playwright 不稳定）  
- Token 打进仓库或 EXE 资源
