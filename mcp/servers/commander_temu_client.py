"""Commander Temu product_issue HTTP helpers for platform MCP gateway."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx

DEFAULT_API_BASE = "https://www.yoto.work/api/v1"
DEFAULT_AGENT_ID = "肉机"
DEFAULT_PLATFORM = "temu"


def _api_base() -> str:
    return (os.environ.get("COMMANDER_API_BASE") or DEFAULT_API_BASE).rstrip("/")


def _token() -> str:
    return (os.environ.get("COMMANDER_ACCESS_TOKEN") or "").strip()


def _agent_id(explicit: str | None = None) -> str:
    return (
        (explicit or "").strip()
        or (os.environ.get("COMMANDER_DEFAULT_AGENT_ID") or DEFAULT_AGENT_ID).strip()
    )


def _headers() -> dict[str, str]:
    token = _token()
    if not token:
        raise RuntimeError(
            "COMMANDER_ACCESS_TOKEN 未配置：请在 MCP 网关环境写入 Bearer token"
        )
    return {"Authorization": f"Bearer {token}"}


def _unwrap(payload: Any) -> Any:
    if isinstance(payload, dict) and "code" in payload:
        code = payload.get("code")
        if code not in (0, "0", None):
            msg = payload.get("msg") or payload.get("message") or str(payload)
            raise RuntimeError(f"Commander 业务失败 code={code}: {msg}")
        return payload.get("data")
    return payload


def commander_precheck(
    *,
    shop_id: str,
    agent_id: str | None = None,
    platform: str = DEFAULT_PLATFORM,
) -> dict[str, Any]:
    agent = _agent_id(agent_id)
    with httpx.Client(timeout=60.0) as client:
        resp = client.post(
            f"{_api_base()}/agent/product_issue_precheck",
            headers=_headers(),
            json={
                "agent_id": agent,
                "shop_id": shop_id,
                "platform": platform,
            },
        )
        resp.raise_for_status()
        data = _unwrap(resp.json())
    return {"ok": True, "agent_id": agent, "shop_id": shop_id, "precheck": data}


def commander_product_issue_submit(
    *,
    file_path: str,
    shop_id: str,
    agent_id: str | None = None,
    platform: str = DEFAULT_PLATFORM,
    precheck: bool = True,
) -> dict[str, Any]:
    path = Path(file_path)
    if not path.is_file():
        return {
            "ok": False,
            "error": f"Excel 不存在或网关不可读: {file_path}",
        }
    agent = _agent_id(agent_id)
    shop_id = shop_id.strip()
    if not shop_id:
        return {"ok": False, "error": "shop_id 必填"}

    try:
        if precheck:
            commander_precheck(shop_id=shop_id, agent_id=agent, platform=platform)

        with path.open("rb") as fh, httpx.Client(timeout=180.0) as client:
            files = {
                "file": (
                    path.name,
                    fh,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            }
            data = {
                "shop_id": shop_id,
                "platform": platform,
                "agent": agent,
            }
            resp = client.post(
                f"{_api_base()}/agent/product_issue",
                headers=_headers(),
                data=data,
                files=files,
            )
            resp.raise_for_status()
            submit_data = _unwrap(resp.json())

        # Snapshot task list for correlation (submit does not return taskId).
        status = commander_product_issue_status(
            agent_id=agent,
            platform=platform,
            list_scope="active",
            page_size=20,
        )
        candidates = [
            t.get("taskId")
            for t in (status.get("tasks") or [])
            if t.get("taskId")
            and t.get("protocol") in (None, "product_issue", "")
        ]
        return {
            "ok": True,
            "submitted": True,
            "message": submit_data if isinstance(submit_data, str) else "submitted",
            "agent_id": agent,
            "shop_id": shop_id,
            "platform": platform,
            "candidate_task_ids": [c for c in candidates if c][:10],
            "hint": "用 temu_product_issue_status 轮询；无 taskId 时按 agent+platform 最近任务判断",
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "agent_id": agent, "shop_id": shop_id}


def commander_product_issue_status(
    *,
    agent_id: str | None = None,
    platform: str = DEFAULT_PLATFORM,
    task_id: str | None = None,
    list_scope: str = "all",
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    agent = _agent_id(agent_id)
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                f"{_api_base()}/agent/task_list",
                headers=_headers(),
                json={
                    "agent_id": agent,
                    "platform": platform,
                    "page": page,
                    "page_size": page_size,
                    "list_scope": list_scope,
                },
            )
            resp.raise_for_status()
            data = _unwrap(resp.json()) or {}

        tasks = list(data.get("list") or [])
        if task_id:
            tasks = [t for t in tasks if str(t.get("taskId") or "") == str(task_id)]

        # Prefer product_issue protocol when present
        pi = [t for t in tasks if t.get("protocol") == "product_issue"]
        focus = pi or tasks
        top = focus[0] if focus else None
        return {
            "ok": True,
            "agent_id": agent,
            "platform": platform,
            "total": data.get("total", len(tasks)),
            "status": (top or {}).get("status"),
            "message": (top or {}).get("message"),
            "task_id": (top or {}).get("taskId"),
            "tasks_ahead": (top or {}).get("tasksAhead"),
            "tasks": [
                {
                    "taskId": t.get("taskId"),
                    "status": t.get("status"),
                    "message": t.get("message"),
                    "protocol": t.get("protocol"),
                    "tasksAhead": t.get("tasksAhead"),
                    "createAt": t.get("createAt"),
                }
                for t in focus[:15]
            ],
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "agent_id": agent, "platform": platform}


def commander_agent_list() -> dict[str, Any]:
    """List Commander agents (online flag for 肉机 probe)."""
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                f"{_api_base()}/agent/list",
                headers=_headers(),
                json={},
            )
            resp.raise_for_status()
            data = _unwrap(resp.json())
        # data may be list or {list: [...]}
        items = data if isinstance(data, list) else list((data or {}).get("list") or [])
        agents = []
        for a in items:
            if not isinstance(a, dict):
                continue
            name = str(a.get("name") or a.get("agentId") or a.get("id") or "")
            online = a.get("status")
            if isinstance(online, bool):
                is_online = online
            else:
                is_online = str(online).lower() in ("true", "1", "online", "on")
            agents.append(
                {
                    "id": str(a.get("agentId") or a.get("id") or name),
                    "name": name,
                    "online": is_online,
                    "raw_status": online,
                }
            )
        default_id = _agent_id(None)
        match = next(
            (x for x in agents if x["name"] == default_id or x["id"] == default_id),
            None,
        )
        return {
            "ok": True,
            "default_agent_id": default_id,
            "default_online": bool(match and match["online"]),
            "agents": agents,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": str(exc),
            "default_agent_id": _agent_id(None),
            "default_online": False,
            "agents": [],
        }
