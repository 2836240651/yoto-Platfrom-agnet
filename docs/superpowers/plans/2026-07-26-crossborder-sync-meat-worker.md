# Cross-Border Sync Meat Worker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the existing Temu listing meat worker into the single execution node for read-only Temu, AliExpress, and Amazon synchronization.

**Architecture:** Platform MCP persists one `crossborder_sync` worker job. The existing meat worker claims it and invokes a platform adapter. SaaS-HZ Vue, Java, SQLite, and its own agent queue are not runtime dependencies.

**Tech Stack:** Python 3.10+, FastMCP, existing worker queue, Playwright/Chrome, Ziniu WebDriver, pytest.

## Constraints
- Keep one existing meat worker and queue; preserve Douyin behavior.
- Reuse only SaaS-HZ Python synchronization/parsing code, never its services or database.
- Never persist or return cookies, tokens, `browser_oauth`, or raw responses.
- First release is read-only; no Amazon write actions.

### Task 1: Generic job contract
**Files:** Modify `mcp/servers/douyin_job_queue.py`, `mcp/servers/platform_mcp_gateway.py`; create `tests/unit_tests/test_crossborder_job_queue.py`.
- [ ] Write failing submit, invalid-platform, persisted-result, and redaction tests.
- [ ] Implement `enqueue_crossborder_sync`, status/wait helpers, and MCP submit/status/auth tools.
- [ ] Verify queue tests and existing Douyin queue tests.

### Task 2: Single meat-worker dispatch
**Files:** Modify `apps/meat-worker/worker_core.py`, `apps/meat-worker/handlers/__init__.py`; create `apps/meat-worker/handlers/crossborder_sync.py`.
- [ ] Write failing registry and unsupported-platform tests.
- [ ] Implement allowlisted dispatcher and credential-free platform heartbeat details.
- [ ] Verify existing worker tests remain green.

### Task 3: Temu and AliExpress adapters
**Files:** Create `apps/meat-worker/crossborder/{contract,temu_sync,aliexpress_sync}.py` and tests.
- [ ] Port only read-only SaaS-HZ browser/crawler code; replace tenant/database coupling with `account_ref` profile paths.
- [ ] Return normalized summaries and `need_login`, never raw sessions.

### Task 4: Amazon Ziniu adapter
**Files:** Create `apps/meat-worker/crossborder/{amazon_sync,ziniao}.py` and tests.
- [ ] Port only Ziniu + Amazon read crawler/parser code; exclude `write_actions.py`.
- [ ] Support account health, inventory, orders, business report, and ads summaries.

### Task 5: Registration and verification
**Files:** Modify MCP registration/documentation and tool-status tests.
- [ ] Register read-only tools, document local account mapping/login, and run `python -m pytest tests/unit_tests -q`.
