# Douyin MeatWorker Collection Diagnostics Design

**Status:** implemented
**Date:** 2026-07-25

## Goal

Make `douyin_collect_hot_keywords` return and persist auditable, Cookie/Token-free diagnostics for no-data, upstream, and parsing outcomes. Disable implicit broad-term fallback and preserve lineage for operator-provided query expansions.

## Constraints

- The meat worker remains an outbound consumer of the `platform_mcp` job queue.
- Diagnostics are persisted in the completed server job and returned by MCP.
- Never persist Cookies, Tokens, Authorization headers, request headers, or full response bodies.
- Default behavior queries only the seed. `query_plan` is explicit input; `bridge_seeds` cannot create it.

## Contract

`query_plan` is optional. Each item is `{ "term": "巨物竿", "source": "operator_expansion" }`. The server normalizes terms, removes blanks and seed duplicates, and records seed queries as `query_level="seed"` and expansions as `query_level="explicit_expansion"`.

Each relationWord request writes a `diagnostics` item with `queried_term`, `query_level`, an allowlisted request-parameter summary, HTTP status, errCode, raw-item count, parsed-item count, duration, and sanitized error. The completed job keeps this result even when the task fails.

## Outcome Classification

- `no_data`: every valid exact query completed without upstream or parse errors and yielded zero parsed items.
- `upstream_error`: any relationWord request has an HTTP or non-success errCode failure.
- `parse_error`: raw items exist but parsing yields none, or extraction raises an error.

## Live Matrix

Run `大物竿`, `钓鱼`, and `渔具` with 30-day video/product parameters. All no-data points to endpoint, permission, or page-version investigation; only `大物竿` no-data is reported as exact-term unavailable; raw-but-unparsed data is a parser defect.

## Live verification (2026-07-25)

Production gateway and the rebuilt local MeatWorker were deployed. With a valid Chanmama login and identical 30-day video/product parameters, `???`, `??`, and `??` each returned `ok=false`, `status=no_data`, `err_code=55006`, `raw_item_count=0`, and `parsed_item_count=0`. Each completed job persisted a seed-level diagnostic (`query_level=seed`, `query_source=seed`).

This proves the current account/API returns no relation words for all three exact queries. It does not justify implicit broad-term fallback. Any expansion must be a new explicit query plan.
