"""FastAPI application entry."""

import app.bootstrap  # noqa: F401

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import boss, health, mcp, tasks, tools

app = FastAPI(
    title="抖音词分析 API",
    description="Agent Platform · 抖音关键词分析智能体",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5179",
        "http://127.0.0.1:5179",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "null",  # Electron file:// / some desktop shells
    ],
    allow_origin_regex=r"http://127\.0\.0\.1:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def model_id_allowlist_as_400(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Design: illegal model_id → HTTP 400 (not 422)."""
    for err in exc.errors():
        msg = str(err.get("msg") or "")
        if "model_id not in allowlist" in msg:
            return JSONResponse(status_code=400, content={"detail": msg})
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


app.include_router(health.router, prefix="/api")
app.include_router(mcp.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(tools.router, prefix="/api")
app.include_router(boss.router, prefix="/api")
