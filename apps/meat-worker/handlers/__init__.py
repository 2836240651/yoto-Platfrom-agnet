"""Job handlers for meat worker."""

from __future__ import annotations

from handlers.douyin_collect import handle_douyin_collect
from handlers.crossborder_sync import handle_crossborder_sync

__all__ = ["handle_crossborder_sync", "handle_douyin_collect"]
