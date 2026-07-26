"""将 AliExpress API / 页面抓包结果映射为入库行。"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any


JIT_STATUS_MAP = {
    "wait_seller_send_goods": "待发货",
    "wait_seller_collect": "待揽收",
    "collected": "已揽收",
    "cancel": "已取消",
    "waitbuyeracceptgoods": "待发货",
}

WAREHOUSE_STATUS_MAP = {
    "wait_warehouse_outbound": "待出库",
    "warehouse_outbound": "已出库",
    "in_delivery": "配送中",
    "finished": "已签收",
}


def _today_text() -> str:
    return date.today().isoformat()


def _now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _pick_list(payload: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("data", "result", "model", "list", "records", "items", "orderList"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            for nested in ("list", "records", "items", "orderList", "data"):
                nested_value = value.get(nested)
                if isinstance(nested_value, list):
                    return [item for item in nested_value if isinstance(item, dict)]
    return []


def _fulfillment_type(raw: dict[str, Any]) -> str:
    text = " ".join(
        str(raw.get(key) or "")
        for key in ("fulfillmentType", "fulfillment_type", "logisticsType", "bizType", "tradeType")
    ).lower()
    if any(token in text for token in ("warehouse", "仓", "海外仓", "ae_plus")):
        return "warehouse"
    return "jit"


def _status_label(raw: dict[str, Any], fulfillment_type: str) -> str:
    code = str(
        raw.get("orderStatus")
        or raw.get("status")
        or raw.get("statusCode")
        or raw.get("order_status")
        or ""
    ).lower()
    label = str(raw.get("statusLabel") or raw.get("status_desc") or raw.get("statusDesc") or "")
    if label:
        return label
    mapping = WAREHOUSE_STATUS_MAP if fulfillment_type == "warehouse" else JIT_STATUS_MAP
    return mapping.get(code, code or "待发货")


def map_order_row(
    raw: dict[str, Any],
    *,
    tenant_id: int,
    store_id: str,
    store_name: str,
    report_day: str,
) -> dict[str, Any]:
    fulfillment_type = _fulfillment_type(raw)
    order_no = str(
        raw.get("orderNo")
        or raw.get("order_no")
        or raw.get("tradeOrderId")
        or raw.get("id")
        or uuid.uuid4().hex[:12]
    )
    sku = str(raw.get("sku") or raw.get("skuCode") or raw.get("productSku") or "")
    product_name = str(
        raw.get("productName")
        or raw.get("product_name")
        or raw.get("title")
        or raw.get("itemTitle")
        or sku
        or "未知商品"
    )
    quantity = int(raw.get("quantity") or raw.get("productCount") or raw.get("qty") or 1)
    amount = float(raw.get("amount") or raw.get("orderAmount") or raw.get("payAmount") or 0)
    currency = str(raw.get("currency") or raw.get("currencyCode") or "USD")
    country = str(raw.get("country") or raw.get("receiverCountry") or raw.get("buyerCountry") or "")
    ordered_at = str(raw.get("orderedAt") or raw.get("gmtCreate") or raw.get("createTime") or _now_text())
    ship_deadline = raw.get("shipDeadline") or raw.get("ship_deadline") or raw.get("lastShipTime")
    warehouse_name = raw.get("warehouseName") or raw.get("warehouse_name") or raw.get("warehouse")

    return {
        "id": f"ae_{order_no}",
        "tenant_id": tenant_id,
        "store_id": store_id,
        "store_name": store_name,
        "report_day": report_day,
        "order_no": order_no,
        "fulfillment_type": fulfillment_type,
        "sku": sku,
        "product_name": product_name,
        "quantity": quantity,
        "amount": amount,
        "currency": currency,
        "country": country,
        "status": _status_label(raw, fulfillment_type),
        "ordered_at": ordered_at,
        "ship_deadline": ship_deadline,
        "warehouse_name": warehouse_name,
    }


def map_violation_row(
    raw: dict[str, Any],
    *,
    tenant_id: int,
    store_id: str,
    store_name: str,
) -> dict[str, Any]:
    type_code = str(
        raw.get("typeCode")
        or raw.get("subType")
        or raw.get("violationType")
        or raw.get("punishType")
        or raw.get("type")
        or "other"
    )
    type_label = str(
        raw.get("typeLabel")
        or raw.get("subTypeName")
        or raw.get("violationTypeName")
        or raw.get("punishTypeName")
        or raw.get("typeName")
        or type_code
    )
    punish_id = str(raw.get("id") or raw.get("punishId") or raw.get("caseId") or uuid.uuid4().hex[:12])
    order_no = str(
        raw.get("orderNo")
        or raw.get("bizOrderId")
        or raw.get("orderId")
        or raw.get("tradeOrderId")
        or raw.get("relatedOrderId")
        or ""
    )
    violated_at = (
        _ms_to_text(raw.get("gmtCreate") or raw.get("punishTime"))
        or str(raw.get("gmtCreateStr") or raw.get("violatedAt") or raw.get("createTime") or _now_text())
    )
    fine_amount = float(
        raw.get("fineAmount")
        or raw.get("punishAmount")
        or raw.get("punishFee")
        or raw.get("penaltyAmount")
        or raw.get("amount")
        or 0
    )
    appeal_status, appeal_result = _map_punish_appeal(raw)
    return {
        "id": f"ae_vio_{punish_id}",
        "tenant_id": tenant_id,
        "store_id": store_id,
        "store_name": store_name,
        "type_code": type_code,
        "type_label": type_label,
        "order_no": order_no,
        "description": str(
            raw.get("description")
            or raw.get("punishReason")
            or raw.get("reasonDesc")
            or raw.get("memo")
            or raw.get("reason")
            or f"{type_label}违规记录"
        ),
        "fine_amount": fine_amount,
        "currency": str(raw.get("currency") or raw.get("punishCurrency") or "USD"),
        "violated_at": violated_at,
        "appeal_status": appeal_status,
        "appeal_result": appeal_result,
        "confirmed": 0,
        "severity": str(raw.get("severity") or "medium"),
        "owner": str(raw.get("owner") or ""),
    }


def _map_punish_appeal(raw: dict[str, Any]) -> tuple[str | None, str | None]:
    show_status = str(raw.get("showStatus") or raw.get("punishStatus") or raw.get("appealStatus") or "").upper()
    if show_status in ("WAIT_APPEAL", "WAIT_APPEALING", "NOT_APPEALED"):
        return "not_appealed", None
    if show_status in ("APPEALING", "WAIT_AUDIT", "APPEAL_PENDING"):
        return "appealed", "pending"
    if show_status in ("APPEAL_SUCCESS", "SUCCESS", "APPEAL_PASS"):
        return "appealed", "success"
    if show_status in ("APPEAL_FAIL", "FAILED", "APPEAL_REJECT"):
        return "appealed", "failed"
    appeal_status = raw.get("appealStatus")
    appeal_result = raw.get("appealResult")
    if appeal_status:
        return str(appeal_status), str(appeal_result) if appeal_result else None
    return None, None


def map_punish_list_violations(
    rows: list[dict[str, Any]],
    *,
    tenant_id: int,
    store_id: str,
    store_name: str,
) -> list[dict[str, Any]]:
    mapped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in rows:
        row = map_violation_row(
            raw,
            tenant_id=tenant_id,
            store_id=store_id,
            store_name=store_name,
        )
        if row["id"] in seen:
            continue
        seen.add(row["id"])
        mapped.append(row)
    return mapped


def map_product_from_order(order_row: dict[str, Any]) -> dict[str, Any]:
    sku = order_row.get("sku") or ""
    return {
        "tenant_id": order_row["tenant_id"],
        "store_id": order_row["store_id"],
        "store_name": order_row.get("store_name") or "",
        "sku": sku,
        "name": order_row.get("product_name") or sku,
        "category": "",
        "selling_price": float(order_row.get("amount") or 0),
        "cost_price": 0,
        "platform_fee_rate": 0.08,
        "logistics_fee": 0,
        "official_stock": 0,
        "local_stock": 0,
        "days_without_sale": 0,
        "daily_sales": int(order_row.get("quantity") or 0),
        "sales_last7_days": "[]",
        "owner": "",
        "report_day": order_row.get("report_day") or _today_text(),
    }


def map_captured_orders(
    payloads: list[dict[str, Any]],
    *,
    tenant_id: int,
    store_id: str,
    store_name: str,
    report_day: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for payload in payloads:
        for item in _pick_list(payload):
            row = map_order_row(
                item,
                tenant_id=tenant_id,
                store_id=store_id,
                store_name=store_name,
                report_day=report_day,
            )
            if row["order_no"] in seen:
                continue
            seen.add(row["order_no"])
            rows.append(row)
    return rows


def map_captured_violations(
    payloads: list[dict[str, Any]],
    *,
    tenant_id: int,
    store_id: str,
    store_name: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for payload in payloads:
        for item in _pick_list(payload):
            rows.append(
                map_violation_row(
                    item,
                    tenant_id=tenant_id,
                    store_id=store_id,
                    store_name=store_name,
                )
            )
    return rows


def _ms_to_text(value: Any) -> str:
    if value in (None, "", 0):
        return ""
    try:
        ms = int(value)
        if ms > 10_000_000_000:
            ms //= 1000
        return datetime.fromtimestamp(ms).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(value)


def _jit_status_label(raw: dict[str, Any]) -> str:
    if raw.get("actualPickupTime") or raw.get("receiveFinishTime"):
        return "已揽收"
    pickup_status = int(raw.get("pickupOrderStatus") or 0)
    purchase_status = int(raw.get("purchaseOrderStatus") or 0)
    if purchase_status <= 10:
        return "待发货"
    if pickup_status <= 10:
        return "待揽收"
    if pickup_status < 30:
        return "已揽收"
    return "待发货"


def _ms_to_date(value: Any) -> str:
    if value in (None, "", 0):
        return ""
    try:
        ms = int(value)
        if ms > 10_000_000_000:
            ms //= 1000
        return datetime.fromtimestamp(ms).strftime("%Y-%m-%d")
    except Exception:
        return ""


def _order_belongs_to_day(raw: dict[str, Any], report_day: str) -> bool:
    feature = raw.get("feature") if isinstance(raw.get("feature"), dict) else {}
    est_pickup_day = str(feature.get("estPickupDay") or "").strip()
    if est_pickup_day == report_day:
        return True
    for key in ("gmtCreate", "coGmtCreate", "gmtSupplierConfirmPo"):
        if _ms_to_date(raw.get(key)) == report_day:
            return True
    return False


def map_jit_consign_orders(
    rows: list[dict[str, Any]],
    *,
    tenant_id: int,
    store_id: str,
    store_name: str,
    report_day: str,
) -> list[dict[str, Any]]:
    mapped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in rows:
        if not _order_belongs_to_day(raw, report_day):
            continue
        order_no = str(raw.get("tradeOrderNo") or raw.get("purchaseOrderNo") or raw.get("consignOrderNo") or "")
        if not order_no:
            continue
        items = raw.get("items") if isinstance(raw.get("items"), list) else [raw]
        feature = raw.get("feature") if isinstance(raw.get("feature"), dict) else {}
        country = str(feature.get("aeReceiverCountryName") or feature.get("receiverCountry") or "")
        ordered_at = _ms_to_text(raw.get("gmtCreate") or raw.get("coGmtCreate"))
        ship_deadline = _ms_to_text(raw.get("lastPickupTime") or raw.get("estimatedPickupTime"))
        warehouse_name = str(raw.get("storeName") or "")
        status = _jit_status_label(raw)

        for index, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            sku = str(item.get("scItemCode") or item.get("skuId") or "")
            key = f"{order_no}:{sku}:{index}"
            if key in seen:
                continue
            seen.add(key)
            quantity = int(item.get("quantity") or raw.get("totalQuantity") or 1)
            mapped.append(
                {
                    "id": f"ae_{order_no}_{sku or index}",
                    "tenant_id": tenant_id,
                    "store_id": store_id,
                    "store_name": store_name,
                    "report_day": report_day,
                    "order_no": order_no,
                    "fulfillment_type": "jit",
                    "sku": sku,
                    "product_name": str(item.get("scItemTitle") or sku or "未知商品"),
                    "quantity": quantity,
                    "amount": 0.0,
                    "currency": "USD",
                    "country": country,
                    "status": status,
                    "ordered_at": ordered_at or _now_text(),
                    "ship_deadline": ship_deadline or None,
                    "warehouse_name": warehouse_name or None,
                }
            )
    return mapped


def _warehouse_status_label(raw: dict[str, Any]) -> str:
    code = str(raw.get("bizStatus") or raw.get("status") or raw.get("purchaseOrderStatus") or "")
    mapping = {
        "10": "待出库",
        "15": "待出库",
        "16": "已出库",
        "20": "配送中",
        "30": "已签收",
        "40": "已取消",
        "50": "已签收",
    }
    return mapping.get(code, code or "待出库")


def _warehouse_belongs_to_day(raw: dict[str, Any], report_day: str) -> bool:
    for key in ("gmtCreate", "createTime", "gmtModified"):
        if _ms_to_date(raw.get(key)) == report_day:
            return True
    return _ms_to_text(raw.get("gmtCreate") or raw.get("createTime")).startswith(report_day)


def map_warehouse_purchase_orders(
    rows: list[dict[str, Any]],
    *,
    tenant_id: int,
    store_id: str,
    store_name: str,
    report_day: str,
) -> list[dict[str, Any]]:
    mapped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in rows:
        if not _warehouse_belongs_to_day(raw, report_day):
            continue
        order_no = str(raw.get("purchaseOrderNo") or raw.get("poNo") or raw.get("orderNo") or "")
        if not order_no:
            continue
        items = raw.get("items") if isinstance(raw.get("items"), list) else raw.get("detailList") or [raw]
        ordered_at = _ms_to_text(raw.get("gmtCreate") or raw.get("createTime"))
        warehouse_name = str(raw.get("storeName") or raw.get("warehouseName") or "")
        status = _warehouse_status_label(raw)

        for index, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            sku = str(item.get("scItemCode") or item.get("skuCode") or item.get("skuId") or "")
            key = f"{order_no}:{sku}:{index}"
            if key in seen:
                continue
            seen.add(key)
            quantity = int(item.get("quantity") or item.get("confirmQty") or 1)
            mapped.append(
                {
                    "id": f"ae_wh_{order_no}_{sku or index}",
                    "tenant_id": tenant_id,
                    "store_id": store_id,
                    "store_name": store_name,
                    "report_day": report_day,
                    "order_no": order_no,
                    "fulfillment_type": "warehouse",
                    "sku": sku,
                    "product_name": str(item.get("scItemTitle") or item.get("title") or sku or "未知商品"),
                    "quantity": quantity,
                    "amount": float(item.get("amount") or raw.get("totalAmount") or 0),
                    "currency": "USD",
                    "country": str(raw.get("country") or ""),
                    "status": status,
                    "ordered_at": ordered_at or _now_text(),
                    "ship_deadline": None,
                    "warehouse_name": warehouse_name or None,
                }
            )
    return mapped
