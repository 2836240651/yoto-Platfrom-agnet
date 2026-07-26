# TUODIAO · Electron 壳

成员端客户端。因线上 `/agent-platform/` 目前只有 API、没有 SPA，EXE **内置** `apps/web` 构建，本机代理 `/api` 到线上。

当前使用 Electron 默认图标；与闲置机 **MeatWorker.exe** 完全分离。

## 角色对照

| 产物 | 给谁 | 干什么 |
|------|------|--------|
| 本目录 `release/` 安装包 / portable | 每个成员本机 | 打开线上 Workspace |
| [`apps/meat-worker/release/`](../meat-worker/release/) | 一台闲置主机 | 出站领蝉妈妈采集任务 |

## 开发

```bat
cd apps\workspace-desktop
npm install
npm start
```

可选：`$env:YOTO_WORKSPACE_URL='http://127.0.0.1:5179'` 指向本地 Vite。

## 打包

```bat
scripts\build-workspace-desktop.bat
```

产出复制到 `apps/workspace-desktop/release/`：

- `YotoWorkspace-*-win-x64.exe` — NSIS 安装（桌面快捷方式）
- `YotoWorkspace-*-portable.exe` — 免安装

（构建暂存在 `%TEMP%\yoto-workspace-desktop-dist`，避免仓库目录被杀软锁文件。）

## 说明

- 不含 Playwright / 蝉妈妈 Cookie；采集登录只在肉机做。
- 外链（非 yoto.work 同源）用系统浏览器打开。
