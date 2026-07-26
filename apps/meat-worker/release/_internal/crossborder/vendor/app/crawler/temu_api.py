"""Temu 卖家后台 API 客户端（通过浏览器上下文发请求，携带真实 Cookie + mallid）"""

from __future__ import annotations



import json

from typing import Any



from playwright.sync_api import Page



from app.browser.context import ensure_logged_in, human_pause, set_mall_id

from app.config import MALL_STORAGE_KEY, TEMU_SALES_API, TEMU_SALES_PAGE, TEMU_USER_INFO_API





class TemuMappingError(RuntimeError):

    """Temu 平台货品映射异常（errorCode=2000000）。"""





def _raise_business_error(data: dict[str, Any]) -> None:

    error_code = data.get("errorCode")

    error_msg = str(data.get("errorMsg") or data.get("error_msg") or "")

    if str(error_code) == "2000000" or "映射关系" in error_msg:

        raise TemuMappingError(

            "Temu 平台返回「货品商品映射关系异常」。请在本机 CrossHub 浏览器中打开「销售管理」页，"

            "确认当前店铺已在左上角选中，并在「商品管理」中补全 SKU 货号后重试。"

            f"（errorCode={error_code}）"

        )

    raise RuntimeError(f"Temu API 业务失败: {json.dumps(data, ensure_ascii=False)[:500]}")





class TemuApiClient:

    def __init__(self, page: Page):

        self.page = page

        self.mall_id = ensure_logged_in(page)



    def _headers(self) -> dict[str, str]:

        return {

            "Content-Type": "application/json",

            "mallid": self.mall_id,

            "Origin": "https://agentseller.temu.com",

            "Referer": "https://agentseller.temu.com/",

        }



    def ensure_sales_context(self) -> None:

        """进入销售管理页，让 Temu 前端完成店铺上下文与映射初始化。"""

        current = (self.page.url or "").lower()

        if "sales-management" not in current and "sale-manage" not in current:

            self.page.goto(TEMU_SALES_PAGE, wait_until="domcontentloaded", timeout=120_000)

            human_pause()

        try:

            self.page.wait_for_load_state("networkidle", timeout=15_000)

        except Exception:

            pass

        stored = self.page.evaluate(

            "(key) => localStorage.getItem(key) || ''",

            MALL_STORAGE_KEY,

        )

        if str(stored).strip() != str(self.mall_id).strip():

            set_mall_id(self.page, self.mall_id)

            self.page.reload(wait_until="domcontentloaded", timeout=120_000)

            human_pause()



    def _post(self, url: str, body: dict[str, Any]) -> dict[str, Any]:

        human_pause()

        # 在页面上下文内 fetch，与卖家后台 SPA 一致（Cookie / 风控上下文更完整）

        result = self.page.evaluate(

            """

            async ({ url, body, mallId }) => {

              const resp = await fetch(url, {

                method: 'POST',

                headers: {

                  'Content-Type': 'application/json',

                  'mallid': mallId,

                },

                body: JSON.stringify(body),

                credentials: 'include',

              });

              const text = await resp.text();

              return { status: resp.status, text };

            }

            """,

            {"url": url, "body": body, "mallId": self.mall_id},

        )

        status = int(result.get("status") or 0)

        text = str(result.get("text") or "")

        if status < 200 or status >= 300:

            raise RuntimeError(f"Temu API HTTP {status}: {text[:500]}")

        data = json.loads(text) if text else {}

        if not data.get("success"):

            _raise_business_error(data)

        return data



    def get_shop_info(self) -> tuple[str, str]:

        data = self._post(TEMU_USER_INFO_API, {})

        mall_list = (data.get("result") or {}).get("mallList") or []

        for mall in mall_list:

            if str(mall.get("mallId")) == self.mall_id:

                return mall.get("mallName") or "", str(mall.get("mallId"))

        raise RuntimeError(f"店铺 ID {self.mall_id} 不在账号店铺列表中")



    def switch_mall(self, mall_id: str) -> None:

        mall_id = str(mall_id or "").strip()

        if not mall_id:

            raise RuntimeError("店铺 ID 为空，无法切换")

        set_mall_id(self.page, mall_id)

        self.mall_id = mall_id

        self.ensure_sales_context()



    def list_malls(self) -> list[dict[str, Any]]:

        data = self._post(TEMU_USER_INFO_API, {})

        return (data.get("result") or {}).get("mallList") or []



    def fetch_sales_page(self, status_code: int, page_no: int, page_size: int = 100) -> dict[str, Any]:

        body = {

            "pageNo": page_no,

            "pageSize": page_size,

            "isLack": 0,

            "selectStatusList": [status_code],

        }

        return self._post(TEMU_SALES_API, body)



    def fetch_all_sales(self) -> list[tuple[int, dict[str, Any]]]:

        """返回 [(status_number, response_json), ...]"""

        self.ensure_sales_context()

        status_map = {100: 10, 200: 11, 300: 12}

        batches: list[tuple[int, dict[str, Any]]] = []



        for status_str, status_num in status_map.items():

            page_no = 1

            while True:

                try:

                    data = self.fetch_sales_page(status_num, page_no)

                except TemuMappingError:

                    # 单个状态 tab 映射异常时跳过，尽量同步其它状态数据

                    break

                sub_orders = ((data.get("result") or {}).get("subOrderList")) or []

                if not sub_orders:

                    break

                batches.append((status_num, data))

                page_no += 1

        if not batches:

            raise TemuMappingError(

                "未能从 Temu 销售管理接口拉取到任何 SKU 数据（货品映射异常或店铺无在售商品）。"

                "请在本机浏览器打开「销售管理」并确认店铺、SKU 货号已维护。"

            )

        return batches


