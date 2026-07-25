@echo off
REM Outbound Douyin meat worker — polls server platform_mcp, runs Playwright locally.
REM Prerequisites: python scripts\chanmama_login.py (once)
REM Secrets: reads DOUYIN_WORKER_* from repo .env (do not commit .env)
cd /d "%~dp0.."

for /f "usebackq tokens=1,* delims==" %%a in (`python scripts\load_env_keys.py DOUYIN_WORKER_URL DOUYIN_WORKER_TOKEN DOUYIN_WORKER_ID DOUYIN_WORKER_POLL_S DOUYIN_CHROME_USER_DATA_DIR`) do (
  if not "%%b"=="" set "%%a=%%b"
)

if not defined DOUYIN_WORKER_URL set DOUYIN_WORKER_URL=https://www.yoto.work/platform-mcp
if not defined DOUYIN_WORKER_ID set DOUYIN_WORKER_ID=肉机
if not defined DOUYIN_WORKER_POLL_S set DOUYIN_WORKER_POLL_S=3

if not defined DOUYIN_WORKER_TOKEN (
  echo ERROR: DOUYIN_WORKER_TOKEN missing in .env
  echo Run: python scripts\_fill_douyin_worker_env.py
  exit /b 2
)

echo Starting Douyin meat worker...
echo   URL=%DOUYIN_WORKER_URL%
echo   ID=%DOUYIN_WORKER_ID%
echo   TOKEN=set (from .env)
python scripts\douyin_meat_worker.py
