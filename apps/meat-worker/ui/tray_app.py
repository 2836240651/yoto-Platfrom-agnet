"""System tray + status window for meat worker.

Windows: Tk must only run on the main thread. pystray menu callbacks run on a
worker thread — creating Toplevel/messagebox there crashes the process
(flash-quit on「显示状态」). Pattern: Tk mainloop on main thread; icon.run()
in a daemon thread; every UI action marshalled via root.after(0, ...).
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, scrolledtext, simpledialog
from typing import Callable

from config import ensure_sample_config, load_config, logs_dir, save_config
from worker_core import MeatWorker, WorkerState, default_handlers, setup_logging

logger = logging.getLogger("meat_worker")


def _make_icon(color: str):
    """Create a small pystray icon (Pillow)."""
    from PIL import Image, ImageDraw

    rgb = {
        "green": (34, 197, 94),
        "yellow": (234, 179, 8),
        "red": (239, 68, 68),
        "stopped": (148, 163, 184),
    }.get(color, (148, 163, 184))
    img = Image.new("RGB", (64, 64), rgb)
    draw = ImageDraw.Draw(img)
    draw.ellipse((8, 8, 56, 56), fill=(255, 255, 255), outline=(30, 30, 30), width=2)
    draw.ellipse((18, 18, 46, 46), fill=rgb)
    return img


class TrayApp:
    def __init__(self) -> None:
        setup_logging()
        ensure_sample_config()
        self.cfg = load_config()
        self._state = WorkerState()
        self._worker: MeatWorker | None = None
        self._icon = None
        self._root: tk.Tk | None = None
        self._status_win: tk.Toplevel | None = None
        self._status_vars: dict[str, tk.StringVar] = {}
        self._err_widget: scrolledtext.ScrolledText | None = None
        self._lock = threading.Lock()

    def _ui(self, fn: Callable[[], None]) -> None:
        """Marshal UI work onto the Tk main thread."""
        root = self._root
        if root is None:
            logger.error("tk root missing; drop UI call %s", getattr(fn, "__name__", fn))
            return
        try:
            root.after(0, fn)
        except Exception:  # noqa: BLE001
            logger.exception("schedule UI failed")

    def _on_state(self, state: WorkerState) -> None:
        self._state = state

        def apply() -> None:
            if self._icon is not None:
                try:
                    self._icon.icon = _make_icon(state.tray_color())
                    nick = state.login.get("nickname") or "-"
                    self._icon.title = f"肉机助手 [{state.tray_color()}] {nick}"
                except Exception:  # noqa: BLE001
                    pass
            self._refresh_status_labels()

        self._ui(apply)

    def _ensure_worker(self) -> MeatWorker:
        if self._worker is None:
            self.cfg = load_config()
            self._worker = MeatWorker(
                self.cfg, handlers=default_handlers(), on_state=self._on_state
            )
        return self._worker

    # --- pystray entrypoints (any thread) → schedule Tk work ---

    def _show_status(self, _icon=None) -> None:
        self._ui(self._show_status_ui)

    def _start_worker(self, _icon=None) -> None:
        self._ui(self._start_worker_ui)

    def _stop_worker(self, _icon=None) -> None:
        self._ui(self._stop_worker_ui)

    def _toggle_claim(self, _icon=None) -> None:
        self._ui(self._toggle_claim_ui)

    def _edit_config(self, _icon=None) -> None:
        self._ui(self._edit_config_ui)

    def _login_chanmama(self, _icon=None) -> None:
        self._ui(self._login_chanmama_ui)

    def _open_logs(self, _icon=None) -> None:
        self._ui(self._open_logs_ui)

    def _quit(self, icon=None) -> None:
        def do_quit() -> None:
            try:
                self._stop_worker_ui()
            except Exception:  # noqa: BLE001
                pass
            if icon is not None:
                try:
                    icon.stop()
                except Exception:  # noqa: BLE001
                    pass
            if self._root is not None:
                try:
                    self._root.destroy()
                except Exception:  # noqa: BLE001
                    pass

        self._ui(do_quit)

    # --- Tk-thread implementations ---

    def _start_worker_ui(self) -> None:
        try:
            self.cfg = load_config()
            if not self.cfg.worker_token:
                self._prompt_token()
                self.cfg = load_config()
            w = self._ensure_worker()
            w.cfg = self.cfg
            w.cfg.apply_env()
            w.start()
        except Exception as exc:  # noqa: BLE001
            logger.exception("start failed")
            messagebox.showerror("肉机助手", f"启动失败：{exc}")

    def _stop_worker_ui(self) -> None:
        if self._worker:
            self._worker.stop()

    def _toggle_claim_ui(self) -> None:
        w = self._ensure_worker()
        enabled = not w.state.claim_enabled
        w.set_claim_enabled(enabled)
        self.cfg.claim_enabled = enabled
        save_config(self.cfg)

    def _prompt_token(self) -> None:
        assert self._root is not None
        token = simpledialog.askstring(
            "Worker Token",
            "请输入 DOUYIN_WORKER_TOKEN（与服务器一致）：",
            parent=self._root,
            show="*",
        )
        if token:
            self.cfg.worker_token = token.strip()
            path = save_config(self.cfg)
            messagebox.showinfo("肉机助手", f"已保存到\n{path}")

    def _edit_config_ui(self) -> None:
        path = ensure_sample_config()
        # Prefer sidecar next to EXE when present
        sidecar = Path(os.environ.get("MEAT_WORKER_DIR") or ".") / "config.json"
        if sidecar.is_file():
            path = sidecar
        try:
            if sys.platform == "win32":
                os.startfile(str(path))  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("肉机助手", f"无法打开配置：{exc}")

    def _login_chanmama_ui(self) -> None:
        def run() -> None:
            try:
                w = self._ensure_worker()
                w.cfg = load_config()
                w.cfg.apply_env()
                login = w.interactive_login()
                msg = (
                    f"登录成功：{login.get('nickname')}"
                    if login.get("logged_in")
                    else f"未登录：{login.get('error') or login}"
                )
                self._ui(lambda: messagebox.showinfo("蝉妈妈登录", msg))
            except Exception as exc:  # noqa: BLE001
                logger.exception("login failed")
                err = str(exc)
                self._ui(lambda: messagebox.showerror("蝉妈妈登录", err))

        threading.Thread(target=run, name="chanmama-login", daemon=True).start()

    def _open_logs_ui(self) -> None:
        path = logs_dir()
        try:
            if sys.platform == "win32":
                os.startfile(str(path))  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("肉机助手", f"无法打开日志：{exc}")

    def _show_status_ui(self) -> None:
        assert self._root is not None
        try:
            if self._status_win is not None:
                try:
                    if self._status_win.winfo_exists():
                        self._status_win.deiconify()
                        self._status_win.lift()
                        self._refresh_status_labels()
                        return
                except tk.TclError:
                    self._status_win = None

            win = tk.Toplevel(self._root)
            win.title("肉机助手 · 状态")
            win.geometry("480x360")
            self._status_win = win
            self._status_vars = {
                "color": tk.StringVar(master=win),
                "url": tk.StringVar(master=win),
                "id": tk.StringVar(master=win),
                "login": tk.StringVar(master=win),
                "hb": tk.StringVar(master=win),
                "job": tk.StringVar(master=win),
                "stats": tk.StringVar(master=win),
                "err": tk.StringVar(master=win),
                "claim": tk.StringVar(master=win),
            }
            rows = [
                ("状态", "color"),
                ("服务器", "url"),
                ("Worker ID", "id"),
                ("蝉妈妈", "login"),
                ("心跳", "hb"),
                ("当前任务", "job"),
                ("计数", "stats"),
                ("领任务", "claim"),
                ("最近错误", "err"),
            ]
            for i, (label, key) in enumerate(rows):
                tk.Label(win, text=label, anchor="w", width=10).grid(
                    row=i, column=0, sticky="nw", padx=8, pady=4
                )
                if key == "err":
                    txt = scrolledtext.ScrolledText(win, height=4, width=48, wrap=tk.WORD)
                    txt.grid(row=i, column=1, sticky="nsew", padx=8, pady=4)
                    self._err_widget = txt
                else:
                    tk.Label(
                        win, textvariable=self._status_vars[key], anchor="w", justify="left"
                    ).grid(row=i, column=1, sticky="w", padx=8, pady=4)
            win.columnconfigure(1, weight=1)
            btns = tk.Frame(win)
            btns.grid(row=len(rows), column=0, columnspan=2, pady=8)
            tk.Button(btns, text="开始", command=self._start_worker_ui).pack(side=tk.LEFT, padx=4)
            tk.Button(btns, text="停止", command=self._stop_worker_ui).pack(side=tk.LEFT, padx=4)
            tk.Button(btns, text="登录蝉妈妈", command=self._login_chanmama_ui).pack(
                side=tk.LEFT, padx=4
            )
            tk.Button(btns, text="编辑配置", command=self._edit_config_ui).pack(
                side=tk.LEFT, padx=4
            )

            def on_close() -> None:
                self._status_win = None
                self._err_widget = None
                self._status_vars = {}
                win.destroy()

            win.protocol("WM_DELETE_WINDOW", on_close)
            self._refresh_status_labels()
        except Exception:  # noqa: BLE001
            logger.exception("show status failed")
            try:
                messagebox.showerror("肉机助手", "打开状态窗失败，详见日志目录")
            except Exception:  # noqa: BLE001
                pass

    def _refresh_status_labels(self) -> None:
        if not self._status_vars:
            return
        st = self._state
        cfg = self.cfg
        try:
            self._status_vars["color"].set(st.tray_color())
            self._status_vars["url"].set(cfg.worker_url)
            self._status_vars["id"].set(cfg.worker_id)
            nick = st.login.get("nickname") or "-"
            self._status_vars["login"].set(
                f"{'已登录' if st.login.get('logged_in') else '未登录'} · {nick}"
            )
            self._status_vars["hb"].set(
                f"{'OK' if st.last_heartbeat_ok else 'FAIL'} · {st.last_heartbeat_at or '-'}"
            )
            self._status_vars["job"].set(
                f"{st.current_job_type or '-'} / {st.current_job_id or '-'}"
            )
            self._status_vars["stats"].set(f"成功 {st.jobs_done} · 失败 {st.jobs_failed}")
            self._status_vars["claim"].set("开" if st.claim_enabled else "暂停")
            if self._err_widget is not None:
                self._err_widget.delete("1.0", tk.END)
                self._err_widget.insert(tk.END, st.last_error or "-")
        except tk.TclError:
            pass

    def run(self) -> None:
        import pystray
        from pystray import MenuItem as Item

        self._root = tk.Tk()
        self._root.withdraw()
        self._root.title("肉机助手")

        menu = pystray.Menu(
            Item("显示状态", self._show_status, default=True),
            Item("开始领任务", self._start_worker),
            Item("停止", self._stop_worker),
            Item("暂停/恢复领任务", self._toggle_claim),
            Item("登录蝉妈妈", self._login_chanmama),
            Item("编辑配置", self._edit_config),
            Item("打开日志目录", self._open_logs),
            Item("退出", self._quit),
        )
        self._icon = pystray.Icon(
            "meat_worker",
            _make_icon("stopped"),
            "肉机助手",
            menu,
        )

        # pystray blocks its own thread; Tk owns the main thread (Windows-safe).
        def run_icon() -> None:
            assert self._icon is not None
            try:
                self._icon.run()
            except Exception:  # noqa: BLE001
                logger.exception("tray icon exited")
                self._ui(lambda: self._root.destroy() if self._root else None)

        threading.Thread(target=run_icon, name="pystray", daemon=True).start()

        if self.cfg.worker_token:
            self._root.after(500, self._start_worker_ui)

        try:
            self._root.mainloop()
        finally:
            if self._icon is not None:
                try:
                    self._icon.stop()
                except Exception:  # noqa: BLE001
                    pass


def main() -> int:
    # Mark EXE dir for sidecar config.json
    if getattr(sys, "frozen", False):
        os.environ.setdefault("MEAT_WORKER_DIR", str(Path(sys.executable).resolve().parent))
    else:
        os.environ.setdefault(
            "MEAT_WORKER_DIR", str(Path(__file__).resolve().parents[1])
        )
    TrayApp().run()
    return 0
