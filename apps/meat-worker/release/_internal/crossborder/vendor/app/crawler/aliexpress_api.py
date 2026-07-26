"""AliExpress 卖家后台 API 客户端（SCM / dchain，携带浏览器 Cookie）。"""
from __future__ import annotations

import json
import re
from datetime import date, timedelta
from typing import Any
from urllib.parse import urlencode

from playwright.sync_api import APIResponse, Page

from app.browser.context import human_pause
from app.config import (
    AE_JIT_CONSIGN_API,
    AE_JIT_ORDER_PAGE,
    AE_JIT_PACKAGE_API,
    AE_VIOLATION_PAGE,
    AE_WAREHOUSE_ORDER_API,
    AE_WAREHOUSE_ORDER_PAGE,
)


class AliExpressApiClient:
    def __init__(self, page: Page):
        self.page = page
        self._scm_token: str | None = None

    def _headers(self, referer: str) -> dict[str, str]:
        return {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://csp.aliexpress.com",
            "Referer": referer,
            "Accept": "application/json, text/plain, */*",
        }

    def ensure_session(self) -> None:
        if self._scm_token:
            return
        self.page.goto(AE_JIT_ORDER_PAGE, wait_until="domcontentloaded", timeout=120_000)
        self.page.wait_for_timeout(8_000)
        token = self._extract_token_from_page()
        if token:
            self._scm_token = token
            return
        captured = self._capture_token_from_network()
        if captured:
            self._scm_token = captured
            return
        raise RuntimeError("无法获取 AliExpress SCM token，请重新登录卖家后台")

    def _extract_token_from_page(self) -> str | None:
        try:
            token = self.page.evaluate(
                """() => {
                  const cookie = document.cookie || '';
                  const match = cookie.match(/(?:^|;\\s*)_scm_token_=([^;]+)/);
                  if (match) return decodeURIComponent(match[1]);
                  const input = document.querySelector('input[name="_scm_token_"]');
                  return input ? input.value : null;
                }"""
            )
            if token:
                return str(token)
        except Exception:
            return None
        return None

    def _capture_token_from_network(self) -> str | None:
        token_holder: dict[str, str] = {}

        def on_request(request) -> None:
            if token_holder:
                return
            post = request.post_data or ""
            match = re.search(r"_scm_token_=([^&]+)", post)
            if match:
                token_holder["token"] = match.group(1)

        self.page.on("request", on_request)
        try:
            self.page.reload(wait_until="domcontentloaded", timeout=90_000)
            self.page.wait_for_timeout(8_000)
        finally:
            self.page.remove_listener("request", on_request)
        return token_holder.get("token")

    def _post_form(self, url: str, fields: dict[str, Any], *, referer: str) -> dict[str, Any]:
        human_pause()
        body = urlencode(fields, doseq=True)
        response: APIResponse = self.page.request.post(
            url,
            data=body,
            headers=self._headers(referer),
            timeout=60_000,
        )
        if not response.ok:
            text = response.text()[:500]
            raise RuntimeError(f"AliExpress SCM HTTP {response.status}: {text}")
        try:
            return response.json()
        except Exception as exc:
            raise RuntimeError(f"AliExpress SCM 响应非 JSON: {exc}") from exc

    def _fetch_range(self, report_day: str, *, lookback_days: int = 14) -> tuple[str, str]:
        end_day = date.fromisoformat(report_day)
        start_day = end_day - timedelta(days=lookback_days)
        return f"{start_day.isoformat()} 00:00:00", f"{end_day.isoformat()} 23:59:59"

    def fetch_jit_consign_orders(self, report_day: str, *, page_size: int = 50) -> list[dict[str, Any]]:
        self.ensure_session()
        start, end = self._fetch_range(report_day)
        rows: list[dict[str, Any]] = []
        page_index = 1
        while page_index <= 10:
            payload = self._post_form(
                AE_JIT_CONSIGN_API,
                {
                    "_scm_token_": self._scm_token,
                    "createDateStart": start,
                    "createDateEnd": end,
                    "pageIndex": page_index,
                    "pageSize": page_size,
                },
                referer=AE_JIT_ORDER_PAGE,
            )
            if not payload.get("success", True) and payload.get("errorCode") not in (None, "SCM_SUCCESS"):
                break
            batch = payload.get("data") or []
            if not isinstance(batch, list) or not batch:
                break
            rows.extend(item for item in batch if isinstance(item, dict))
            total = int(payload.get("totalCount") or 0)
            if len(rows) >= total or len(batch) < page_size:
                break
            page_index += 1
        return rows

    def fetch_warehouse_purchase_orders(self, report_day: str, *, page_size: int = 50) -> list[dict[str, Any]]:
        self.ensure_session()
        self.page.goto(AE_WAREHOUSE_ORDER_PAGE, wait_until="domcontentloaded", timeout=120_000)
        self.page.wait_for_timeout(6_000)
        start, end = self._fetch_range(report_day, lookback_days=30)
        rows: list[dict[str, Any]] = []
        page_index = 1
        while page_index <= 10:
            query = urlencode(
                [("bizStatusList", status) for status in ("10", "15", "16", "20", "25", "30", "101")]
                + [("poTypeList", po_type) for po_type in ("10", "60", "70")]
                + [
                    ("fromSource", "repListPage"),
                    ("gmtCreateLeft", start),
                    ("gmtCreateRight", end),
                    ("pageIndex", str(page_index)),
                    ("pageSize", str(page_size)),
                    ("sortByScItemId", "true"),
                ],
                doseq=True,
            )
            human_pause()
            response: APIResponse = self.page.request.get(
                f"{AE_WAREHOUSE_ORDER_API}?{query}",
                headers={
                    "Accept": "application/json, text/plain, */*",
                    "Referer": AE_WAREHOUSE_ORDER_PAGE,
                },
                timeout=60_000,
            )
            if not response.ok:
                text = response.text()[:500]
                raise RuntimeError(f"AliExpress warehouse HTTP {response.status}: {text}")
            payload = response.json()
            if not payload.get("success", True) and payload.get("errorCode") not in (None, "SCM_SUCCESS"):
                break
            batch = payload.get("data") or []
            if not isinstance(batch, list) or not batch:
                break
            rows.extend(item for item in batch if isinstance(item, dict))
            total = int(payload.get("totalCount") or 0)
            if len(rows) >= total or len(batch) < page_size:
                break
            page_index += 1
        return rows

    def fetch_violations(self, *, days: int = 90, page_size: int = 50) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        seen: set[str] = set()

        def on_response(response) -> None:
            try:
                if response.status != 200:
                    return
                if "querypunishlist" not in (response.url or "").lower():
                    return
                body = response.json()
                payload = body.get("data") or {}
                if not isinstance(payload, dict):
                    return
                for item in payload.get("data") or []:
                    if not isinstance(item, dict):
                        continue
                    key = str(item.get("id") or item.get("punishId") or item.get("caseId") or "")
                    if key:
                        if key in seen:
                            continue
                        seen.add(key)
                    rows.append(item)
            except Exception:
                return

        self.page.on("response", on_response)
        try:
            self.page.goto(AE_VIOLATION_PAGE, wait_until="domcontentloaded", timeout=120_000)
            self.page.wait_for_timeout(12_000)
            total = 0
            for item in rows:
                total = max(total, int(item.get("totalCount") or 0))
            if len(rows) < total and total > page_size:
                for page_index in range(2, 6):
                    self.page.evaluate(
                        """async ({ pageIndex, pageSize, days }) => {
                          if (!window.lib || !window.lib.mtop || !window.lib.mtop.request) return { skipped: true };
                          try {
                            return await window.lib.mtop.request({
                              api: 'mtop.ae.merchant.csp.illegal.queryPunishList',
                              v: '1.0',
                              data: {
                                currentPage: pageIndex,
                                pageSize,
                                showStatus: 'ALL',
                                subType: 'ALL',
                                days: String(days),
                                version: '1.1',
                              },
                              type: 'GET',
                              dataType: 'json',
                            });
                          } catch (error) {
                            return { error: String(error) };
                          }
                        }""",
                        {"pageIndex": page_index, "pageSize": page_size, "days": days},
                    )
                    self.page.wait_for_timeout(2_000)
        finally:
            self.page.remove_listener("response", on_response)
        return rows

    def fetch_jit_package_details(self, report_day: str, *, page_size: int = 50) -> list[dict[str, Any]]:
        self.ensure_session()
        rows: list[dict[str, Any]] = []
        page_index = 1
        while page_index <= 10:
            payload = self._post_form(
                AE_JIT_PACKAGE_API,
                {
                    "_scm_token_": self._scm_token,
                    "pageIndex": page_index,
                    "pageSize": page_size,
                },
                referer=AE_JIT_ORDER_PAGE,
            )
            if not payload.get("success", True) and payload.get("errorCode") not in (None, "SCM_SUCCESS"):
                break
            batch = payload.get("data") or []
            if not isinstance(batch, list) or not batch:
                break
            rows.extend(item for item in batch if isinstance(item, dict))
            total = int(payload.get("totalCount") or 0)
            if len(rows) >= total or len(batch) < page_size:
                break
            page_index += 1
        return rows

    def fetch_violations_page(self, page_no: int = 1, page_size: int = 50) -> dict[str, Any]:
        rows = self.fetch_violations(days=90, page_size=page_size)
        start = max(page_no - 1, 0) * page_size
        end = start + page_size
        return {"data": rows[start:end], "totalCount": len(rows)}
