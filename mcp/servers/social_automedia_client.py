"""Automedia (social-auto-upload) HTTP helpers for platform MCP gateway."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx

DEFAULT_API_BASE = "https://automedia.yoto.work"
ALLOWED_PLATFORM_TYPES = frozenset({1, 2, 3, 4, 5})


def _api_base() -> str:
    return (os.environ.get("SOCIAL_UPLOAD_API_BASE") or DEFAULT_API_BASE).rstrip("/")


def _token() -> str:
    return (os.environ.get("SOCIAL_UPLOAD_TOKEN") or "").strip()


def _headers(*, json_body: bool = True) -> dict[str, str]:
    token = _token()
    if not token:
        raise RuntimeError(
            "SOCIAL_UPLOAD_TOKEN 未配置：请在 MCP 网关环境写入 automedia Bearer JWT"
        )
    headers = {"Authorization": f"Bearer {token}"}
    if json_body:
        headers["Content-Type"] = "application/json"
    return headers


def _unwrap(payload: Any) -> Any:
    if isinstance(payload, dict) and "code" in payload:
        code = payload.get("code")
        if code not in (200, "200", 0, "0"):
            msg = payload.get("msg") or payload.get("message") or str(payload)
            raise RuntimeError(f"automedia 业务失败 code={code}: {msg}")
        return payload.get("data")
    return payload


def social_list_accounts() -> dict[str, Any]:
    if not _token():
        return {"ok": False, "error": "SOCIAL_UPLOAD_TOKEN 未配置", "accounts": []}
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.get(f"{_api_base()}/getAccounts", headers=_headers(json_body=False))
            resp.raise_for_status()
            data = _unwrap(resp.json())
            agent = client.get(
                f"{_api_base()}/login-agent/status",
                headers=_headers(json_body=False),
            )
            agent.raise_for_status()
            agent_data = _unwrap(agent.json()) or {}
        accounts = data if isinstance(data, list) else list((data or {}).get("list") or data or [])
        return {
            "ok": True,
            "accounts": accounts,
            "login_agent": agent_data,
            "agent_online": bool(
                isinstance(agent_data, dict)
                and (agent_data.get("online") or agent_data.get("active"))
            ),
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "accounts": []}


def social_upload_file(file_path: str) -> dict[str, Any]:
    """Upload local file to automedia /upload; returns stored filename for postVideo."""
    if not _token():
        return {"ok": False, "error": "SOCIAL_UPLOAD_TOKEN 未配置"}
    path = Path(file_path)
    if not path.is_file():
        return {"ok": False, "error": f"文件不存在或网关不可读: {file_path}"}
    try:
        with path.open("rb") as fh, httpx.Client(timeout=300.0) as client:
            files = {"file": (path.name, fh, "application/octet-stream")}
            resp = client.post(
                f"{_api_base()}/upload",
                headers={"Authorization": f"Bearer {_token()}"},
                files=files,
            )
            resp.raise_for_status()
            body = resp.json()
            data = _unwrap(body)
        filename = data if isinstance(data, str) else (data or {}).get("filepath") or (data or {}).get("filename")
        if not filename:
            return {"ok": False, "error": f"upload 未返回文件名: {body}"}
        return {"ok": True, "filename": str(filename)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


def social_publish_submit(
    *,
    file_path: str = "",
    file_list: list[str] | None = None,
    account_list: list[str] | None = None,
    platform_type: int = 3,
    title: str = "",
    tags: list[str] | str | None = None,
    agent_id: str = "",
) -> dict[str, Any]:
    """Upload (if file_path) + postVideo. Never treats local_queued as terminal success."""
    if not _token():
        return {"ok": False, "error": "SOCIAL_UPLOAD_TOKEN 未配置"}

    try:
        ptype = int(platform_type)
    except (TypeError, ValueError):
        return {"ok": False, "error": f"非法 platform_type: {platform_type}"}
    if ptype not in ALLOWED_PLATFORM_TYPES:
        return {"ok": False, "error": f"首批仅支持 type 1–5，收到 {ptype}"}

    accounts = [str(a).strip() for a in (account_list or []) if str(a).strip()]
    if not accounts:
        return {"ok": False, "error": "account_list 必填"}
    title = (title or "").strip()
    if not title:
        return {"ok": False, "error": "title 必填"}

    files = [str(f).strip() for f in (file_list or []) if str(f).strip()]
    if file_path and not files:
        uploaded = social_upload_file(file_path)
        if not uploaded.get("ok"):
            return uploaded
        files = [str(uploaded["filename"])]
    if not files:
        return {"ok": False, "error": "需要 file_path 或 file_list"}

    if isinstance(tags, str):
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    else:
        tag_list = [str(t).strip() for t in (tags or []) if str(t).strip()]

    payload = {
        "fileList": files,
        "accountList": accounts,
        "type": ptype,
        "title": title,
        "tags": tag_list,
        "enableTimer": False,
    }
    if agent_id.strip():
        payload["agentId"] = agent_id.strip()

    try:
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(
                f"{_api_base()}/postVideo",
                headers=_headers(),
                content=json.dumps(payload, ensure_ascii=False),
            )
            body = resp.json() if resp.content else {}
            # agent_required → HTTP 400 with structured data
            if resp.status_code == 400:
                data = body.get("data") if isinstance(body, dict) else None
                runtime = (data or {}).get("publish_runtime") if isinstance(data, dict) else None
                job_id = (data or {}).get("job_id") if isinstance(data, dict) else None
                return {
                    "ok": False,
                    "submitted": False,
                    "error": body.get("msg") if isinstance(body, dict) else str(body),
                    "publish_runtime": runtime,
                    "job_id": job_id,
                    "platform_type": ptype,
                    "file_list": files,
                    "account_list": accounts,
                }
            resp.raise_for_status()
            data = _unwrap(body) or {}
        runtime = data.get("publish_runtime") if isinstance(data, dict) else None
        job_id = data.get("job_id") if isinstance(data, dict) else None
        if not job_id:
            return {
                "ok": False,
                "submitted": True,
                "error": "上游未返回 job_id，禁止将已派发当作成功（需 automedia Task 0）",
                "publish_runtime": runtime,
                "platform_type": ptype,
                "file_list": files,
                "account_list": accounts,
            }
        return {
            "ok": True,
            "submitted": True,
            "job_id": job_id,
            "publish_runtime": runtime,
            "platform_type": ptype,
            "title": title,
            "file_list": files,
            "account_list": accounts,
            "hint": "用 social_publish_status 轮询至 success/failed",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": str(exc),
            "platform_type": ptype,
            "file_list": files,
            "account_list": accounts,
        }


def social_publish_status(*, job_id: str) -> dict[str, Any]:
    if not _token():
        return {"ok": False, "error": "SOCIAL_UPLOAD_TOKEN 未配置"}
    job_id = (job_id or "").strip()
    if not job_id:
        return {"ok": False, "error": "job_id 必填"}
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.get(
                f"{_api_base()}/publish/jobs/{job_id}",
                headers=_headers(json_body=False),
            )
            if resp.status_code == 404:
                return {"ok": False, "error": "任务不存在", "job_id": job_id, "status": "unknown"}
            resp.raise_for_status()
            data = _unwrap(resp.json()) or {}
        status = str(data.get("status") or "unknown").lower()
        return {
            "ok": True,
            "job_id": data.get("job_id") or job_id,
            "status": status,
            "runtime": data.get("runtime"),
            "error": data.get("error"),
            "platform_type": data.get("platform_type"),
            "detail": data.get("detail") or {},
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "job_id": job_id}
