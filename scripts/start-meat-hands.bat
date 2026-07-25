@echo off
REM Dual meat hands launcher (same PC): Douyin Playwright worker + optional Commander Agent.
REM Architecture: same ROLE, different control planes — do NOT merge into commander-agent.
REM Docs: docs\wip\douyin-meat-machine-mcp.md · docs\wip\douyin-meat-ops-runbook.md
cd /d "%~dp0.."

for /f "usebackq tokens=1,* delims==" %%a in (`python scripts\load_env_keys.py DOUYIN_WORKER_URL DOUYIN_WORKER_TOKEN DOUYIN_WORKER_ID COMMANDER_AGENT_EXE COMMANDER_ACCESS_TOKEN COMMANDER_API_BASE COMMANDER_DEFAULT_AGENT_ID`) do (
  if not "%%b"=="" set "%%a=%%b"
)

if not defined DOUYIN_WORKER_TOKEN (
  echo ERROR: DOUYIN_WORKER_TOKEN missing in .env
  echo Run: python scripts\_fill_douyin_worker_env.py
  exit /b 2
)

echo === Meat hands (dual process) ===
echo [1/2] Douyin worker  -^> platform_mcp /worker/*
start "douyin-meat-worker" "%~dp0start-douyin-meat-worker.bat"

if defined COMMANDER_AGENT_EXE (
  if exist "%COMMANDER_AGENT_EXE%" (
    echo [2/2] Commander Agent -^> %COMMANDER_AGENT_EXE%
    start "commander-agent" "%COMMANDER_AGENT_EXE%"
  ) else (
    echo [2/2] COMMANDER_AGENT_EXE set but file missing: %COMMANDER_AGENT_EXE%
    echo       Skip Temu hand; Douyin worker still started.
  )
) else (
  echo [2/2] COMMANDER_AGENT_EXE not set — skip Temu Agent launch
  echo       Set in .env if Agent.exe lives on this PC.
)

echo.
echo Waiting 5s then probing status...
timeout /t 5 /nobreak >nul
python scripts\meat_hands_status.py
echo.
echo Ops runbook: docs\wip\douyin-meat-ops-runbook.md
