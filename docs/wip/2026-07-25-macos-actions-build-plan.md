# macOS 桌面端 Actions 打包计划

## 目标

使用 GitHub-hosted `macos-latest` runner 手动构建 TUODIAO 的 universal macOS 安装包，并将 `.dmg` 与 `.zip` 作为 Actions artifact 上传下载。

## 范围与约束

- 工作流仅通过 `workflow_dispatch` 手动执行，避免每次 push 消耗 macOS runner 分钟。
- 构建未签名包；不读取、保存或要求 Apple 签名/公证密钥。
- 复用 `apps/workspace-desktop` 的 `build:web` 脚本和 Electron Builder，不修改业务前端或 API。
- 产物为 universal（Apple Silicon 与 Intel）`.dmg` 和 `.zip`，不产生 macOS `.exe`。

## 实施步骤

1. 新增 `.github/workflows/build-macos-desktop.yml`，声明 `workflow_dispatch` 与 `macos-latest`。
2. 安装 Web 和桌面端锁定依赖，运行 `npm run build:web --prefix apps/workspace-desktop`。
3. 使用 Electron Builder 的 `--mac dmg zip --universal`，关闭自动发布及签名发现。
4. 使用 `actions/upload-artifact` 上传 `apps/workspace-desktop/release-macos` 下的 `.dmg` 与 `.zip`。
5. 检查工作流 YAML、差异及 Git 状态；仅提交计划与新工作流。

## 验收

- GitHub Actions 页面出现 “Build macOS Desktop” 的手动触发入口。
- 任务在 macOS runner 上生成 `.dmg` 和 `.zip` artifact。
- 本次提交不包含现有 Windows 安装包、MeatWorker 产物或临时文件。
