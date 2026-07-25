# Douyin MeatWorker Collection Diagnostics Implementation Plan

**Goal:** Persist safe relationWord diagnostics, support explicit query plans, and ensure the Skill/Agent stops inventing data or silently broadening terms.

**Architecture:** The collection client produces per-query diagnostics and lineage. The worker submits structured results on success and failure. The job queue persists and returns the result. The Skill/Agent branches on `no_data`, `upstream_error`, and `parse_error`, and only uses operator-provided query plans.

## Task 1: Tests

- Add red tests for no-data diagnostics, explicit query lineage, and failed job result persistence.
- Run focused tests to prove the current contracts fail.

## Task 2: Collection and Worker

- Normalize `query_plan` without generating bridge terms.
- Capture safe relationWord diagnostics and classify outcomes.
- Forward `query_plan` through the handler and preserve structured failures.

## Task 3: Queue and Gateway

- Persist failed `result` payloads and return their diagnostics through `wait_job`.
- Add the optional `query_plan` parameter to enqueue and gateway tool contracts.

## Task 4: Tool and Prompt Contracts

- Update registry, Skill, agent plan labels, and argument construction.
- Require diagnostic-first handling and prohibit hidden broad-term fallback.

## Task 5: Verification

- Run focused and relevant agent tests.
- Build MeatWorker from this worktree.
- Deploy the new gateway and worker package, then run `大物竿`, `钓鱼`, and `渔具` with identical parameters.
