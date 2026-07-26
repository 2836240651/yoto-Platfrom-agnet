"""Temu API 响应 → temu_sale 表行"""
from __future__ import annotations

from app.config import STATUS_TO_CODE


def _price_status(code: int | None) -> str:
    if code == 2:
        return "open"
    if code == 3:
        return "close"
    return "none"


def map_sales_batches(
    batches: list[tuple[int, dict]],
    *,
    shop_id: str,
    shop_name: str,
    report_time: str,
    tenant_id: int,
    nickname: str = "",
    username: str = "",
    enterprise: str = "",
    user_id: int = 1,
) -> list[dict]:
    rows: list[dict] = []

    for status_num, payload in batches:
        status_str = STATUS_TO_CODE.get(status_num, "0")
        sub_orders = ((payload.get("result") or {}).get("subOrderList")) or []

        for order in sub_orders:
            skus = order.get("skuQuantityDetailList") or []
            for sku in skus:
                today = int(sku.get("todaySaleVolume") or 0)
                s7 = int(sku.get("lastSevenDaysSaleVolume") or 0)
                s30 = int(sku.get("lastThirtyDaysSaleVolume") or 0)
                # 保留有销量或有近 30 日销量的 SKU；今日有单但 30 日为 0 的新品也要入库
                if s30 == 0 and today == 0 and s7 == 0:
                    continue

                inv = sku.get("inventoryNumInfo") or {}

                rows.append(
                    {
                        "platform": "temu",
                        "status": status_str,
                        "report_time": report_time,
                        "shop_name": shop_name,
                        "shop_id": shop_id,
                        "tenant_id": tenant_id,
                        "user_id": user_id,
                        "cost": 0,
                        "category_name": order.get("category") or "",
                        "img_url": order.get("productSkcPicture") or "",
                        "title": order.get("productName") or "",
                        "skc": str(order.get("productSkcId") or ""),
                        "spu": str(order.get("productId") or ""),
                        # 唯一键依赖 ext_code：优先 productSkuId，避免 skcExtCode 跨 SKU 重复覆盖销量
                        "ext_code": (
                            str(sku.get("productSkuId") or "").strip()
                            or str(sku.get("skuExtCode") or "").strip()
                            or str(order.get("skcExtCode") or "").strip()
                            or f"{order.get('productSkcId') or ''}-{sku.get('className') or ''}"
                        ),
                        "son_sku": str(sku.get("productSkuId") or ""),
                        "son_price": int(sku.get("supplierPrice") or 0),
                        "son_today_sales": today,
                        "son_sales_seven_days": s7,
                        "son_sales_thirty_days": s30,
                        "join_site_time": int(order.get("onSalesDurationOffline") or 0),
                        "warehouse_available_stock": int(inv.get("warehouseInventoryNum") or 0),
                        "nickname": nickname,
                        "username": username,
                        "enterprise": enterprise,
                    }
                )
    return rows
