"""Outbound meat worker core: heartbeat / claim / complete + job.type handlers."""

from __future__ import annotations

import json
import logging
import threading
import time
import traceback
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from config import MeatConfig, load_config, logs_dir

logger = logging.getLogger("meat_worker")

HandlerFn = Callable[[dict[str, Any], MeatConfig], dict[str, Any]]

_COMPLETE_RETRY_ATTEMPTS = 3


@dataclass
class WorkerState:
    running: bool = False
    claim_enabled: bool = True
    login: dict[str, Any] = field(default_factory=lambda: {"logged_in": False, "need_login": True})
    last_heartbeat_ok: bool = False
    last_heartbeat_at: str = ""
    last_error: str = ""
    current_job_id: str = ""
    current_job_type: str = ""
    jobs_done: int = 0
    jobs_failed: int = 0
    status_label: str = "stopped"  # green|yellow|red|stopped

    def tray_color(self) -> str:
        if not self.running:
            return "stopped"
        if self.last_heartbeat_ok and self.login.get("logged_in"):
            return "green"
        if self.last_heartbeat_ok:
            return "yellow"
        return "red"


def safe_err(exc: BaseException) -> str:
    import re

    text = str(exc)
    text = re.sub(r"(?i)cookie:\s*.*", "cookie: [redacted]", text)
    text = re.sub(r"(?i)authorization[^:]*:\s*\S+", "Authorization: [redacted]", text)
    text = re.sub(r"LOGIN-TOKEN-FORSNS=\S+", "LOGIN-TOKEN-FORSNS=[redacted]", text)
    return text[:500]


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class MeatWorker:
    def __init__(
        self,
        cfg: MeatConfig | None = None,
        *,
        handlers: dict[str, HandlerFn] | None = None,
        on_state: Callable[[WorkerState], None] | None = None,
    ) -> None:
        self.cfg = cfg or load_config()
        self.cfg.apply_env()
        self.handlers: dict[str, HandlerFn] = dict(handlers or {})
        self.on_state = on_state
        self.state = WorkerState(claim_enabled=self.cfg.claim_enabled)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._login_lock = threading.Lock()

    def register(self, job_type: str, fn: HandlerFn) -> None:
        self.handlers[job_type] = fn

    def _emit(self) -> None:
        self.state.status_label = self.state.tray_color()
        if self.on_state:
            try:
                self.on_state(self.state)
            except Exception:  # noqa: BLE001
                logger.exception("on_state failed")

    def _request(
        self, method: str, path: str, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        url = f"{self.cfg.worker_url.rstrip('/')}{path}"
        data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.cfg.worker_token:
            headers["Authorization"] = f"Bearer {self.cfg.worker_token}"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        timeout_s = 20
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
        except TimeoutError as exc:
            raise RuntimeError(f"timeout {timeout_s}s {path}") from exc
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code} {path}: {err_body[:400]}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"unreachable {url}: {exc}") from exc
        if not raw.strip():
            return {}
        try:
            out = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"bad JSON from {path}: {raw[:200]}") from exc
        return out if isinstance(out, dict) else {"ok": False, "raw": out}

    def heartbeat(self) -> dict[str, Any]:
        login = self.state.login or {}
        return self._request(
            "POST",
            "/worker/heartbeat",
            {
                "worker_id": self.cfg.worker_id,
                "logged_in": bool(login.get("logged_in")),
                "nickname": login.get("nickname"),
                "detail": {
                    "need_login": bool(login.get("need_login")),
                    "error": login.get("error"),
                    "job_types": sorted(self.handlers),
                    "platforms": {
                        platform: {"available": "crossborder_sync" in self.handlers}
                        for platform in ("temu", "aliexpress")
                    },
                },
            },
        )

    def claim(self) -> dict[str, Any] | None:
        job_types = sorted(self.handlers)
        if not bool((self.state.login or {}).get("logged_in")):
            job_types = [job_type for job_type in job_types if job_type != "douyin_collect_hot_keywords"]
        out = self._request(
            "POST", "/worker/claim", {"worker_id": self.cfg.worker_id, "job_types": job_types}
        )
        job = out.get("job")
        return job if isinstance(job, dict) else None

    def complete(
        self,
        *,
        job_id: str,
        ok: bool,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        body = {
            "worker_id": self.cfg.worker_id,
            "job_id": job_id,
            "ok": ok,
            "result": result,
            "error": error,
        }
        for attempt in range(1, _COMPLETE_RETRY_ATTEMPTS + 1):
            try:
                return self._request("POST", "/worker/complete", body)
            except Exception as exc:  # noqa: BLE001
                message = safe_err(exc)
                transient = (
                    "timeout" in message.lower()
                    or "unreachable" in message.lower()
                    or "http 5" in message.lower()
                )
                if not transient or attempt == _COMPLETE_RETRY_ATTEMPTS:
                    raise
                delay_s = float(attempt)
                logger.warning(
                    "complete retry %s/%s job=%s after %s",
                    attempt,
                    _COMPLETE_RETRY_ATTEMPTS,
                    job_id,
                    message,
                )
                time.sleep(delay_s)
        raise RuntimeError("worker complete retries exhausted")

    def refresh_login(self, *, headed: bool | None = None) -> dict[str, Any]:
        with self._login_lock:
            self.cfg.apply_env()
            from handlers.douyin_collect import check_login_status

            try:
                login = check_login_status(headed=False if headed is None else headed)
            except Exception as exc:  # noqa: BLE001
                login = {
                    "logged_in": False,
                    "need_login": True,
                    "error": f"login check failed: {safe_err(exc)}",
                }
            self.state.login = login
            self._emit()
            return login

    def interactive_login(self, timeout_sec: int = 420) -> dict[str, Any]:
        with self._login_lock:
            self.cfg.apply_env()
            from handlers.douyin_collect import run_interactive_login

            login = run_interactive_login(timeout_sec=timeout_sec)
            self.state.login = login
            self._emit()
            return login

    def run_job(self, job: dict[str, Any]) -> None:
        job_id = str(job.get("id") or "")
        job_type = str(job.get("type") or "douyin_collect_hot_keywords")
        self.state.current_job_id = job_id
        self.state.current_job_type = job_type
        self._emit()
        logger.info("claim %s type=%s", job_id, job_type)
        handler = self.handlers.get(job_type)
        if handler is None:
            self.complete(job_id=job_id, ok=False, error=f"unknown job type: {job_type}")
            self.state.jobs_failed += 1
            self.state.last_error = f"unknown job type: {job_type}"
            self.state.current_job_id = ""
            self._emit()
            return
        try:
            result = handler(job, self.cfg)
        except Exception as exc:  # noqa: BLE001
            logger.exception("job failed")
            self.complete(job_id=job_id, ok=False, error=f"handler exception: {safe_err(exc)}")
            self.state.jobs_failed += 1
            self.state.last_error = safe_err(exc)
            self.state.current_job_id = ""
            self._emit()
            return
        if not isinstance(result, dict):
            self.complete(job_id=job_id, ok=False, error="handler returned non-dict")
            self.state.jobs_failed += 1
            self.state.current_job_id = ""
            self._emit()
            return
        ok = result.get("ok") is not False
        if not ok:
            self.complete(
                job_id=job_id,
                ok=False,
                error=str(result.get("error") or "handler failed"),
                result=result,
            )
            self.state.jobs_failed += 1
            self.state.last_error = str(result.get("error") or "handler failed")
        else:
            ds = result.setdefault("data_source", {})
            if isinstance(ds, dict):
                ds.setdefault("source", "mcp")
                ds.setdefault("tool", job_type)
                ds["worker_id"] = self.cfg.worker_id
            self.complete(job_id=job_id, ok=True, result=result)
            self.state.jobs_done += 1
            self.state.last_error = ""
        self.state.current_job_id = ""
        self.state.current_job_type = ""
        self._emit()
        logger.info("done %s ok=%s", job_id, ok)

    def _loop(self) -> None:
        self.state.running = True
        self._emit()
        last_login_check = 0.0
        while not self._stop.is_set():
            try:
                now = time.time()
                if now - last_login_check > 60:
                    self.refresh_login()
                    last_login_check = now
                    logger.info(
                        "login logged_in=%s nick=%s",
                        self.state.login.get("logged_in"),
                        self.state.login.get("nickname"),
                    )
                try:
                    self.heartbeat()
                    self.state.last_heartbeat_ok = True
                    self.state.last_heartbeat_at = _utcnow()
                    self.state.last_error = (
                        self.state.last_error
                        if self.state.current_job_id
                        else (
                            ""
                            if self.state.login.get("logged_in")
                            else str(self.state.login.get("error") or "need_login")
                        )
                    )
                except Exception as exc:  # noqa: BLE001
                    self.state.last_heartbeat_ok = False
                    self.state.last_error = safe_err(exc)
                    logger.warning("heartbeat error: %s", exc)
                self._emit()

                if self.state.claim_enabled and self.cfg.claim_enabled and self.handlers:
                    try:
                        job = self.claim()
                        if job:
                            self.run_job(job)
                            last_login_check = 0
                            continue
                    except Exception as exc:  # noqa: BLE001
                        self.state.last_error = safe_err(exc)
                        logger.warning("claim/loop error: %s", exc)
                        self._emit()
            except Exception as exc:  # noqa: BLE001
                self.state.last_error = safe_err(exc)
                logger.exception("loop error")
                self._emit()
            self._stop.wait(max(1.0, float(self.cfg.poll_s or 3)))
        self.state.running = False
        self.state.last_heartbeat_ok = False
        self._emit()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        if not self.cfg.worker_token:
            self.state.last_error = "worker_token missing — edit config.json"
            self._emit()
            raise RuntimeError("worker_token missing")
        self.cfg.apply_env()
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="meat-worker", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        self.state.running = False
        self._emit()

    def set_claim_enabled(self, enabled: bool) -> None:
        self.state.claim_enabled = enabled
        self.cfg.claim_enabled = enabled
        self._emit()


def setup_logging() -> Path:
    log_path = logs_dir() / "meat-worker.log"
    root = logging.getLogger("meat_worker")
    if not root.handlers:
        root.setLevel(logging.INFO)
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setFormatter(fmt)
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        root.addHandler(fh)
        root.addHandler(sh)
    return log_path


def default_handlers() -> dict[str, HandlerFn]:
    from handlers.douyin_collect import handle_douyin_collect
    from handlers.crossborder_sync import handle_crossborder_sync

    return {
        "douyin_collect_hot_keywords": handle_douyin_collect,
        "crossborder_sync": handle_crossborder_sync,
    }


def run_headless() -> int:
    """CLI mode (dev / no tray)."""
    setup_logging()
    cfg = load_config()
    if not cfg.worker_token:
        logger.error("set worker_token in config.json or DOUYIN_WORKER_TOKEN")
        return 2
    w = MeatWorker(cfg, handlers=default_handlers())
    logger.info("url=%s id=%s", cfg.worker_url, cfg.worker_id)
    try:
        w.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        w.stop()
    return 0
