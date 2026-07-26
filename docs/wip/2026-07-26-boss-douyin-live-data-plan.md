# 抖音 BOSS 真实数据接入实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use `executing-plans` to implement task-by-task.

**Goal:** 将服务器 `douyin_reports` 的现有真实抖音报表安全展示在 BOSS `/boss/douyin` 页面。

**Architecture:** BOSS Web 只调用 Agent API；API 通过独立只读 MySQL 用户读取 `douyin_reports`，在 API 内完成指标映射、日期选择和 SQL 参数化查询。API compose 持久加入现有 `deploy_default` 网络，以服务名 `epay-mysql` 访问 MySQL；不增加 MCP、Skill、LLM 或新数据库表。

**Tech Stack:** FastAPI、Pydantic、PyMySQL、React 19、TypeScript、Vite、Docker Compose、MySQL 5.7。

## Global Constraints

- BOSS 前端禁止直连数据库、禁止模拟数据、禁止暴露工程术语。
- 数据查询、指标计算、排序和失败判定使用代码；不调用 LLM。
- 数据库使用 `boss_report_reader` 最小权限账号，仅有 `douyin_reports` 的 `SELECT`。
- 保持现有 5 张表和唯一键，不创建原始表、临时表或闲置表。
- 不修改肉机、Hermes Excel 或当前 Skill/MCP 行为。
- 本期只实现抖音读取闭环；Temu、Amazon、1688 继续空态。

---

### Task 1: 报表读取模型与失败测试

**Files:**
- Create: `apps/api/app/services/douyin_reports.py`
- Create: `apps/api/app/schemas/boss.py`
- Create: `tests/unit_tests/test_douyin_boss_reports.py`
- Modify: `src/agent/config/settings.py`
- Modify: `pyproject.toml`

**Interfaces:**
- Produces `DouyinBossReport` with `period`、`data_as_of`、`metrics`、`products`、`videos`。
- Produces `DouyinReportService.get_dashboard(period: str) -> DouyinBossReport`。

- [ ] Write fake-reader tests first: latest period mapping, metric mapping, product ordering, and duplicate video rows retained.
- [ ] Run `python -m pytest tests/unit_tests/test_douyin_boss_reports.py -q`; expected failure because models/service do not exist.
- [ ] Implement Pydantic output models, injectable reader protocol, parameterized PyMySQL reader, and missing-data error.
- [ ] Run the same test; expected pass.

### Task 2: BOSS API 路由

**Files:**
- Create: `apps/api/app/routers/boss.py`
- Modify: `apps/api/app/main.py`
- Test: `tests/unit_tests/test_douyin_boss_reports.py`

**Interfaces:**
- Produces `GET /api/boss/douyin?period=daily|weekly|monthly`.
- Returns 503 with business-safe detail when database is unavailable or no report exists.

- [ ] Add a router test using a patched report service for success and unavailable cases.
- [ ] Run router-focused test and observe failure before router registration.
- [ ] Register the router and map domain errors to HTTP 503 without connection details.
- [ ] Re-run tests; expected pass.

### Task 3: BOSS 抖音页面

**Files:**
- Modify: `apps/web/src/api/client.ts`
- Modify: `apps/web/src/pages/BossPlatformPage.tsx`
- Modify: `apps/web/src/styles/global.css`

**Interfaces:**
- Consumes `api.getDouyinBossReport(period)`.
- Displays latest data date, 9 store metrics, product top list, video top list, and exact source/date status.

- [ ] Implement typed API client response and request method.
- [ ] Replace only `/boss/douyin` empty state with loading, error, and real report views; leave three other platforms empty.
- [ ] Add period selection and responsive metric/table styles.
- [ ] Run `npm run build --prefix apps/web` and `npm run lint --prefix apps/web`.

### Task 4: 安全部署与远程验收

**Files:**
- Modify: `.env.example`
- Modify: `mcp/deploy/docker-compose.yml`
- Modify: `scripts/deploy-agent-api-hotpatch.js`

**Interfaces:**
- Adds `BOSS_REPORTS_DB_*` environment names only; secrets remain server-side.
- Adds external `deploy_default` network to `agent-api` compose service.

- [ ] Create `boss_report_reader` remotely with `SELECT` only on `douyin_reports.*`; do not print password.
- [ ] Set the new credentials in server compose `.env` and persist the compose network configuration.
- [ ] Install PyMySQL in the running API as the hot-patch dependency and copy only required application files; then restart API.
- [ ] Verify API health, `GET /api/boss/douyin`, 200 response, `data_as_of=20260722`, and no MySQL credential leakage.
- [ ] Run `python -m pytest tests/unit_tests/test_douyin_boss_reports.py -q`, `npm run build --prefix apps/web`, `npm run lint --prefix apps/web`, and `git diff --check`.
