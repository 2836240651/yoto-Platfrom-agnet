"""Chanmama (蝉妈妈) personal-edition collector via Playwright persistent profile.

Auth: DOUYIN_CHROME_USER_DATA_DIR (or default .local/chanmama-chrome).
Never log cookie values.
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROFILE = PROJECT_ROOT / ".local" / "chanmama-chrome"
API_HOST = "https://api-service.chanmama.com"
SITE = "https://www.chanmama.com"

# hotSearchRank works with 服装 leaf; 运动户外 top may return empty on personal edition.
CATEGORY_CLOTHING = "1000003282"
CATEGORY_SPORTS = "1117922455"

_PRODUCT_HINT = re.compile(
    r"(竿|钩|箱|线|饵|轮|组|漂|坠|假饵|路亚|渔具|钓具|鱼护|抄网|支架|报警)"
)

# Niche seeds often unindexed in 视频热搜分析; bridge to indexed parent terms.
_BRIDGE_MAP: dict[str, list[str]] = {
    "欧鲤钓": ["鲤鱼", "钓鱼", "线组", "海竿", "鲤钓", "欧鲤"],
    "欧鲤": ["鲤鱼", "钓鱼", "线组", "海竿"],
    "反底钓": ["线组", "钓鱼", "鲤鱼", "子线", "钩组", "反底"],
    "反底": ["线组", "钓鱼", "鲤鱼", "子线", "钩组"],
    "罗尼": ["线组", "钓鱼", "鲤鱼", "钩组"],
    "路亚": ["路亚", "钓鱼", "假饵", "路亚竿"],
}


def bridge_seeds(seed: str) -> list[str]:
    """Build searchable parent/variant seeds when the exact seed is unindexed."""
    s = (seed or "").strip()
    out: list[str] = []
    if s in _BRIDGE_MAP:
        out.extend(_BRIDGE_MAP[s])
    for suffix in ("钓法", "教程", "技巧", "钓", "法"):
        if s.endswith(suffix) and len(s) > len(suffix) + 1:
            base = s[: -len(suffix)]
            out.append(base)
            out.extend(_BRIDGE_MAP.get(base, []))
            break
    # Always include broad fishing anchors for 渔具 niche
    if any(k in s for k in ("钓", "鱼", "鲤", "鲈", "鲶", "饵", "竿", "路亚")):
        out.extend(["钓鱼", "渔具", "线组"])
    # de-dupe preserve order, drop exact seed (handled separately)
    seen: set[str] = set()
    final: list[str] = []
    for w in out:
        w = w.strip()
        if not w or w == s or w in seen:
            continue
        seen.add(w)
        final.append(w)
    return final[:8]


def profile_dir() -> Path:
    raw = (os.environ.get("DOUYIN_CHROME_USER_DATA_DIR") or "").strip()
    path = Path(raw) if raw else DEFAULT_PROFILE
    path.mkdir(parents=True, exist_ok=True)
    return path


def _now_ts() -> int:
    return int(time.time())


def _ymd_yesterday() -> str:
    return (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")


def _seed_related(word: str, seed: str) -> bool:
    w = (word or "").strip().lower()
    s = (seed or "").strip().lower()
    if not w or not s:
        return False
    if s in w or w in s:
        return True
    chars = [c for c in s if "\u4e00" <= c <= "\u9fff"]
    if len(chars) >= 2:
        for i in range(len(chars) - 1):
            if "".join(chars[i : i + 2]) in w:
                return True
    return False


def _looks_product(word: str) -> bool:
    return bool(_PRODUCT_HINT.search(word or ""))


def _extract_words_from_obj(obj: Any, out: list[dict[str, Any]], *, side: str, bucket: str) -> None:
    if isinstance(obj, dict):
        word = (
            obj.get("keyword")
            or obj.get("word")
            or obj.get("hot_word")
            or obj.get("query")
            or obj.get("name")
            or obj.get("title")
        )
        if isinstance(word, str) and word.strip():
            hot = (
                obj.get("search_index")
                or obj.get("hot_value")
                or obj.get("hot_level")
                or obj.get("query_hot_index")
                or obj.get("score")
                or obj.get("volume")
            )
            try:
                hot_level = int(float(hot)) if hot is not None else 0
            except (TypeError, ValueError):
                hot_level = 0
            compete = obj.get("competitive_index") or obj.get("compete_index")
            try:
                compete_f = float(compete) if compete is not None else None
            except (TypeError, ValueError):
                compete_f = None
            out.append(
                {
                    "word": word.strip(),
                    "hot_level": hot_level,
                    "compete_index": compete_f,
                    "side": side,
                    "bucket": bucket,
                }
            )
        for v in obj.values():
            _extract_words_from_obj(v, out, side=side, bucket=bucket)
    elif isinstance(obj, list):
        for item in obj:
            _extract_words_from_obj(item, out, side=side, bucket=bucket)


def _dedupe(words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for item in words:
        w = item.get("word") or ""
        key = f"{item.get('side')}:{item.get('bucket')}:{w}"
        if not w or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _split_hot_potential(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Hot = high search_index; potential = lower compete / mid search."""
    if not rows:
        return [], []
    ranked = sorted(rows, key=lambda x: (-int(x.get("hot_level") or 0), x.get("word") or ""))
    hot: list[dict[str, Any]] = []
    potential: list[dict[str, Any]] = []
    for item in ranked:
        compete = item.get("compete_index")
        # low competition with non-trivial search → potential
        if compete is not None and float(compete) <= 2.5 and int(item.get("hot_level") or 0) > 0:
            potential.append({**item, "bucket": "potential"})
        else:
            hot.append({**item, "bucket": "hot"})
    if not potential and len(hot) > 4:
        mid = max(2, len(hot) // 2)
        potential = [{**x, "bucket": "potential"} for x in hot[mid:]]
        hot = hot[:mid]
    if not hot and potential:
        hot = [{**x, "bucket": "hot"} for x in potential[:3]]
        potential = potential[3:]
    return hot[:20], potential[:20]


class ChanmamaSession:
    def __init__(self, *, headed: bool = False) -> None:
        self.headed = headed
        self._pw = None
        self._context = None
        self._page = None

    def __enter__(self) -> "ChanmamaSession":
        from playwright.sync_api import sync_playwright

        self._pw = sync_playwright().start()
        launch_kwargs: dict[str, Any] = {
            "user_data_dir": str(profile_dir()),
            "headless": not self.headed,
            "locale": "zh-CN",
            "viewport": {"width": 1440, "height": 900},
            "args": ["--disable-blink-features=AutomationControlled"],
        }
        channel = (os.environ.get("DOUYIN_PW_CHANNEL") or "").strip()
        if channel:
            launch_kwargs["channel"] = channel
        try:
            self._context = self._pw.chromium.launch_persistent_context(**launch_kwargs)
        except Exception:
            # Fallback: bundled Chromium when system Chrome channel unavailable.
            launch_kwargs.pop("channel", None)
            self._context = self._pw.chromium.launch_persistent_context(**launch_kwargs)
        self._page = self._context.pages[0] if self._context.pages else self._context.new_page()
        return self

    def __exit__(self, *exc: Any) -> None:
        try:
            if self._context:
                self._context.close()
        finally:
            if self._pw:
                self._pw.stop()

    @property
    def page(self):
        assert self._page is not None
        return self._page

    def api_get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        q = dict(params or {})
        q.setdefault("timeStamp", _now_ts())
        url = f"{API_HOST}{path}"
        if q:
            url = f"{url}?{urlencode(q, doseq=True)}"
        resp = self.page.request.get(url, headers={"Referer": f"{SITE}/"})
        try:
            data = resp.json()
        except Exception:
            return {"errCode": -1, "errMsg": f"non-json status={resp.status}", "ok": False}
        if not isinstance(data, dict):
            return {"errCode": -1, "errMsg": "unexpected payload", "data": data}
        return data

    def check_login(self) -> dict[str, Any]:
        info = self.api_get("/v1/user/info")
        err = info.get("errCode")
        if err in (0, "0", None) and info.get("data"):
            data = info.get("data") or {}
            nick = data.get("nickname") or data.get("user_name") or data.get("name") or "member"
            return {
                "ok": True,
                "logged_in": True,
                "nickname": str(nick)[:40],
                "profile": str(profile_dir()),
            }
        msg = info.get("errMsg") or "未登录"
        return {
            "ok": False,
            "logged_in": False,
            "need_login": True,
            "error": str(msg),
            "errCode": err,
            "profile": str(profile_dir()),
            "login_hint": "python scripts/chanmama_login.py",
        }

    def collect_hot_keywords(
        self,
        seed: str,
        *,
        date_range_days: int = 30,
        include_video: bool = True,
        include_product: bool = True,
    ) -> dict[str, Any]:
        auth = self.check_login()
        if not auth.get("logged_in"):
            return {
                "ok": False,
                "need_login": True,
                "error": auth.get("error") or "蝉妈妈未登录",
                "login_hint": auth.get("login_hint"),
                "profile": auth.get("profile"),
                "seed": seed,
            }

        day = _ymd_yesterday()
        traces: list[dict[str, Any]] = []
        errors: list[str] = []
        video_rows: list[dict[str, Any]] = []
        product_rows: list[dict[str, Any]] = []
        seed_mode = "direct"
        bridges_used: list[str] = []

        def _ingest_relation(query: str, *, side: str = "video") -> int:
            rel = self.api_get(
                "/v1/hot_search_analysis/relationWord",
                {
                    "keyword": query,
                    "keyword_type": 1,
                    "sort": "search_index",
                    "orderBy": 1,
                },
            )
            traces.append(
                {
                    "tool": "relationWord",
                    "query": query,
                    "errCode": rel.get("errCode"),
                    "errMsg": rel.get("errMsg"),
                }
            )
            if rel.get("errCode") not in (0, "0", None):
                errors.append(f"relationWord({query}): {rel.get('errMsg')}")
                return 0
            batch: list[dict[str, Any]] = []
            _extract_words_from_obj(
                (rel.get("data") or {}).get("aweme_keyword_relation_resp_list"),
                batch,
                side=side,
                bucket="hot",
            )
            n = 0
            for item in batch:
                if item["word"] in {seed, query}:
                    continue
                item["seed_related"] = True
                item["bridge"] = query
                video_rows.append(item)
                n += 1
            return n

        # --- Video / content: seed first, then bridge parents if unindexed ---
        if include_video:
            got = _ingest_relation(seed)
            if got == 0:
                seed_mode = "bridge"
                for b in bridge_seeds(seed):
                    n = _ingest_relation(b)
                    if n:
                        bridges_used.append(b)
                # also try search endpoint on bridges
                for b in bridges_used[:3] or bridge_seeds(seed)[:3]:
                    search = self.api_get(
                        "/v1/hot_search_analysis/search",
                        {"keyword": b, "keyword_type": 1},
                    )
                    traces.append(
                        {
                            "tool": "hot_search_analysis/search",
                            "query": b,
                            "errCode": search.get("errCode"),
                        }
                    )
                    if search.get("errCode") in (0, "0", None):
                        batch = []
                        _extract_words_from_obj(
                            (search.get("data") or {}).get("aweme_keyword_relation_resp_list"),
                            batch,
                            side="video",
                            bucket="hot",
                        )
                        for item in batch:
                            if item["word"] in {seed, b}:
                                continue
                            item["bridge"] = b
                            video_rows.append(item)
            else:
                search = self.api_get(
                    "/v1/hot_search_analysis/search",
                    {"keyword": seed, "keyword_type": 1},
                )
                traces.append(
                    {"tool": "hot_search_analysis/search", "errCode": search.get("errCode")}
                )
                if search.get("errCode") in (0, "0", None):
                    batch = []
                    _extract_words_from_obj(
                        (search.get("data") or {}).get("aweme_keyword_relation_resp_list"),
                        batch,
                        side="video",
                        bucket="hot",
                    )
                    for item in batch:
                        if item["word"] == seed:
                            continue
                        video_rows.append(item)

        # --- Product: ecommerce hot-word rank + SKU-like relation words ---
        product_queries = [seed] + (bridges_used or bridge_seeds(seed)[:4])
        if include_product:
            for cat_id, cat_name in (
                (CATEGORY_SPORTS, "运动户外"),
                (CATEGORY_CLOTHING, "服装"),
            ):
                for q in product_queries:
                    for intention, bucket in ((1, "hot"), (2, "potential"), (4, "potential")):
                        payload = self.api_get(
                            "/v1/center/field/hotSearchRank",
                            {
                                "page": 1,
                                "size": 50,
                                "intention": intention,
                                "category_id": cat_id,
                                "day_type": "day",
                                "special_type": "",
                                "start_time": day,
                                "end_time": day,
                                "keyword": q,
                                "is_new_category": "true",
                            },
                        )
                        traces.append(
                            {
                                "tool": "hotSearchRank",
                                "category": cat_name,
                                "query": q,
                                "intention": intention,
                                "errCode": payload.get("errCode"),
                                "n": len(((payload.get("data") or {}).get("list") or [])),
                            }
                        )
                        if payload.get("errCode") not in (0, "0", None):
                            continue
                        batch = []
                        _extract_words_from_obj(
                            (payload.get("data") or {}).get("list"),
                            batch,
                            side="product",
                            bucket=bucket,
                        )
                        for item in batch:
                            item["bridge"] = q
                            product_rows.append(item)
                if product_rows:
                    break

            # Fallback: treat SKU-like relation words as product keywords
            if not product_rows and video_rows:
                for item in video_rows:
                    if _looks_product(item["word"]):
                        product_rows.append(
                            {
                                **item,
                                "side": "product",
                                "bucket": "hot",
                            }
                        )

        video_rows = _dedupe(video_rows)
        product_rows = _dedupe(product_rows)
        video_hot, video_potential = _split_hot_potential(video_rows) if include_video else ([], [])
        product_hot, product_potential = (
            _split_hot_potential(product_rows) if include_product else ([], [])
        )

        keywords = [
            {
                "word": x["word"],
                "hot_level": x.get("hot_level") or 0,
                "side": x.get("side"),
                "bucket": x.get("bucket"),
                "bridge": x.get("bridge"),
            }
            for x in (video_hot + video_potential + product_hot + product_potential)
        ]
        ok = bool(keywords)
        # clear noisy bridge errors when we still got words
        if ok:
            errors = [e for e in errors if "无相关关联词" not in e and "未收录" not in e]
        return {
            "ok": ok,
            "seed": seed,
            "seed_mode": seed_mode,
            "bridges_used": bridges_used,
            "date_range_days": date_range_days,
            "keywords": keywords,
            "count": len(keywords),
            "video_hot": [{"word": x["word"], "hot_level": x.get("hot_level") or 0} for x in video_hot],
            "video_potential": [
                {"word": x["word"], "hot_level": x.get("hot_level") or 0} for x in video_potential
            ],
            "product_hot": [
                {"word": x["word"], "hot_level": x.get("hot_level") or 0} for x in product_hot
            ],
            "product_potential": [
                {"word": x["word"], "hot_level": x.get("hot_level") or 0} for x in product_potential
            ],
            "auth": {"logged_in": True, "nickname": auth.get("nickname")},
            "traces": traces,
            "errors": errors,
            "data_source": {
                "source": "mcp",
                "tool": "douyin_collect_hot_keywords",
                "provider": "chanmama",
            },
            "error": None if ok else ("采集为空：" + ("; ".join(errors[:3]) if errors else "无词")),
        }


def check_login(*, headed: bool = False) -> dict[str, Any]:
    with ChanmamaSession(headed=headed) as sess:
        sess.page.goto(SITE, wait_until="domcontentloaded", timeout=60000)
        sess.page.wait_for_timeout(1500)
        return sess.check_login()


def collect_hot_keywords(
    seed: str,
    *,
    date_range_days: int = 30,
    include_video: bool = True,
    include_product: bool = True,
    headed: bool = False,
) -> dict[str, Any]:
    with ChanmamaSession(headed=headed) as sess:
        sess.page.goto(SITE, wait_until="domcontentloaded", timeout=60000)
        sess.page.wait_for_timeout(1000)
        return sess.collect_hot_keywords(
            seed,
            date_range_days=date_range_days,
            include_video=include_video,
            include_product=include_product,
        )


def interactive_login(timeout_sec: int = 300) -> dict[str, Any]:
    """Open headed browser; poll until logged in or timeout."""
    with ChanmamaSession(headed=True) as sess:
        sess.page.goto(f"{SITE}/login.html", wait_until="domcontentloaded", timeout=60000)
        deadline = time.time() + timeout_sec
        last: dict[str, Any] = {}
        while time.time() < deadline:
            last = sess.check_login()
            if last.get("logged_in"):
                return last
            sess.page.wait_for_timeout(3000)
            if "login" not in (sess.page.url or "").lower():
                last = sess.check_login()
                if last.get("logged_in"):
                    return last
        last = last or sess.check_login()
        last["ok"] = False
        last["error"] = last.get("error") or f"登录超时（{timeout_sec}s）"
        last["need_login"] = True
        return last


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--login", action="store_true")
    ap.add_argument("--seed", default="渔具")
    ap.add_argument("--collect", action="store_true")
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()
    if args.login:
        print(json.dumps(interactive_login(), ensure_ascii=False, indent=2))
    elif args.check:
        print(json.dumps(check_login(headed=args.headed), ensure_ascii=False, indent=2))
    elif args.collect:
        print(
            json.dumps(
                collect_hot_keywords(args.seed, headed=args.headed),
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        ap.print_help()
