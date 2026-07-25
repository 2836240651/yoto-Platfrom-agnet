# BOSS 平台视角实施计划

## 目标

以最小前端改动增加“运营｜BOSS｜开发”三视角切换，并提供仅包含抖音、1688、Temu、Amazon 的 BOSS 平台数据空态界面。

## 范围与约束

- 仅修改 `apps/web` 前端路由、布局、样式与页面组件。
- 不请求 API，不修改 Runtime、Skill、MCP、registry 或 schema。
- BOSS 侧栏不展示任务、对话、工具、项目、MCP 或工程术语。
- 项目没有既有前端测试框架；遵循现有验证方式，使用 `npm run build --prefix apps/web` 进行 TypeScript 和生产构建校验。

## 实施步骤

1. 在 `apps/web/src/pages/BossPlatformPage.tsx` 定义四个平台的前端常量、BOSS 总览与单平台空态页面。
2. 在 `apps/web/src/App.tsx` 注册 `/boss` 和 `/boss/:platform` 路由。
3. 在 `apps/web/src/components/Layout.tsx` 按当前路由切换运营、BOSS、开发侧栏；将底部单链接替换为三段式视角按钮。
4. 在 `apps/web/src/styles/global.css` 添加视角切换与平台空态的响应式样式，复用现有颜色变量。
5. 执行 `npm run build --prefix apps/web`，检查路由导入、类型与生产构建输出。

## 验收

- 运营、BOSS、开发三种视角均有可点击且带当前态的切换按钮。
- `/boss` 的左栏只有抖音、1688、Temu、Amazon 四个平台入口。
- `/boss/douyin`、`/boss/1688`、`/boss/temu`、`/boss/amazon` 均显示非数据化空态。
- 运营与开发既有导航保持可用。
