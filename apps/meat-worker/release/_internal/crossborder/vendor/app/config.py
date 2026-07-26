"""爬虫运行配置（可通过环境变量或 .env 覆盖）"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=False)

PROFILE_ROOT = Path(os.getenv("TEMU_PROFILE_ROOT", str(ROOT / ".temu-browser-profile")))


def resolve_profile_dir(tenant_id: int) -> Path:
    return PROFILE_ROOT / f"tenant-{tenant_id}"


def resolve_tenant_id(cli_value: int | None = None) -> int:
    if cli_value is not None and cli_value > 0:
        return cli_value
    env_value = os.getenv("TENANT_ID", "").strip()
    if env_value.isdigit() and int(env_value) > 0:
        return int(env_value)
    raise ValueError("缺少租户 ID：请传入 --tenant-id 或设置环境变量 TENANT_ID")


# 默认有头 + 本机 Chrome，降低 Temu 风控识别概率
TEMU_SELLER_HOME = os.getenv("TEMU_SELLER_HOME", "https://agentseller.temu.com/")
TEMU_SALES_API = os.getenv(
    "TEMU_SALES_API",
    "https://agentseller.temu.com/mms/venom/api/supplier/sales/management/listOverall",
)
TEMU_USER_INFO_API = os.getenv(
    "TEMU_USER_INFO_API",
    "https://agentseller.temu.com/api/seller/auth/userInfo",
)
TEMU_SALES_PAGE = os.getenv(
    "TEMU_SALES_PAGE",
    "https://agentseller.temu.com/mmsos/sales-stock-management/sales-management",
)
MALL_STORAGE_KEY = os.getenv("TEMU_MALL_STORAGE_KEY", "agentseller-mall-info-id")

# 默认有头 + 本机 Chrome，降低 Temu 风控识别概率
def is_headless() -> bool:
    return os.getenv("TEMU_HEADLESS", "0").strip().lower() in ("1", "true", "yes")


HEADLESS = is_headless()
BROWSER_CHANNEL = os.getenv("TEMU_BROWSER_CHANNEL", "chrome").strip() or None

MIN_ACTION_DELAY_MS = int(os.getenv("TEMU_MIN_DELAY_MS", "800"))
MAX_ACTION_DELAY_MS = int(os.getenv("TEMU_MAX_DELAY_MS", "2200"))
TEMU_LOGIN_WAIT_SECONDS = int(os.getenv("TEMU_LOGIN_WAIT_SECONDS", "240"))
TEMU_LOGIN_POLL_SECONDS = int(os.getenv("TEMU_LOGIN_POLL_SECONDS", "3"))

STATUS_TO_CODE = {10: "100", 11: "200", 12: "300", 13: "400"}

# AliExpress 卖家后台
AE_PROFILE_ROOT = Path(os.getenv("AE_PROFILE_ROOT", str(ROOT / ".aliexpress-browser-profile")))


def resolve_aliexpress_profile_dir(tenant_id: int) -> Path:
    return AE_PROFILE_ROOT / f"tenant-{tenant_id}"


AE_CSP_HOME = os.getenv("AE_CSP_HOME", "https://csp.aliexpress.com/")
AE_JIT_ORDER_PAGE = os.getenv(
    "AE_JIT_ORDER_PAGE",
    "https://gsp.aliexpress.com/m_apps/ascp/aechoice.purchase_jit_order_list",
)
AE_WAREHOUSE_ORDER_PAGE = os.getenv(
    "AE_WAREHOUSE_ORDER_PAGE",
    "https://gsp.aliexpress.com/m_apps/ascp/aechoice.purchase_stockup_for_aechoice",
)
AE_JIT_CONSIGN_API = os.getenv(
    "AE_JIT_CONSIGN_API",
    "https://scm-supplier.aliexpress.com/aidc-ib-web-f/purchase/supplier/queryJitConsignOrders",
)
AE_WAREHOUSE_ORDER_API = os.getenv(
    "AE_WAREHOUSE_ORDER_API",
    "https://scm-supplier.aliexpress.com/aidc-procurement/webapi/purchase/queryPurchaseOrders",
)
AE_ORDER_PAGE = os.getenv(
    "AE_ORDER_PAGE",
    "https://csp.aliexpress.com/m_apps/order-manage/orderList",
)
AE_VIOLATION_PAGE = os.getenv(
    "AE_VIOLATION_PAGE",
    "https://gsp.aliexpress.com/m_apps/violation/violist",
)
AE_JIT_PACKAGE_API = os.getenv(
    "AE_JIT_PACKAGE_API",
    "https://scm-supplier.aliexpress.com/dchain-seller-portal-ae/popChoicePackage/queryListV2",
)
AE_ORDER_API = os.getenv(
    "AE_ORDER_API",
    "https://csp.aliexpress.com/api/order/list",
)
AE_VIOLATION_API = os.getenv(
    "AE_VIOLATION_API",
    "https://csp.aliexpress.com/api/violation/list",
)


def is_ae_headless() -> bool:
    return os.getenv("AE_HEADLESS", os.getenv("TEMU_HEADLESS", "0")).strip().lower() in (
        "1",
        "true",
        "yes",
    )


AE_LOGIN_WAIT_SECONDS = int(os.getenv("AE_LOGIN_WAIT_SECONDS", "240"))
AE_LOGIN_POLL_SECONDS = int(os.getenv("AE_LOGIN_POLL_SECONDS", "3"))

# 紫鸟 WebDriver（本地 127.0.0.1，见 open.ziniao.com docId=98）
ZINIAO_COMPANY = os.getenv("ZINIAO_COMPANY", "").strip()
ZINIAO_USERNAME = os.getenv("ZINIAO_USERNAME", "").strip()
ZINIAO_PASSWORD = os.getenv("ZINIAO_PASSWORD", "").strip()
ZINIAO_CLIENT_PATH = os.getenv("ZINIAO_CLIENT_PATH", r"C:\Program Files\ziniao\ziniao.exe").strip()
ZINIAO_SOCKET_PORT = int(os.getenv("ZINIAO_SOCKET_PORT", "16851"))
