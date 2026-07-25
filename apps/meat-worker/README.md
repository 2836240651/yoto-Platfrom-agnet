# 肉机助手（MeatWorker）

> **标识**：本目录是 Agent Platform 的 **本机出站手**。  
> **不是** Commander Temu Agent；二者同角色、不同控制面。

## 空闲机怎么用（不要再打包）

GitHub 上直接取可运行包：

**[`release/`](./release/)**（含 `MeatWorker.exe` + `_internal/`）

1. 下载/拷贝整个 `release` 文件夹到空闲机（如 `D:\meat-worker\`）
2. 编辑 `config.json`，填入 `worker_token`
3. 双击 `MeatWorker.exe` → 托盘「登录蝉妈妈」→ 图标变绿

详见同目录 [`release/README.txt`](./release/README.txt) 与 [`docs/wip/meat-worker-exe.md`](../../docs/wip/meat-worker-exe.md)。

## 开发者重建（可选）

仅在改了托盘/采集逻辑后需要：

```bat
scripts\build-meat-worker.bat
```

会刷新 `apps/meat-worker/release/`。

## 源码结构

```
apps/meat-worker/
├── release/             # ★ 预构建 EXE（给空闲机）
├── __main__.py
├── worker_core.py
├── config.py
├── handlers/
├── ui/tray_app.py
└── meat_worker.spec
```
