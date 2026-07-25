@echo off
REM Build MeatWorker onedir package to dist\meat-worker\
cd /d "%~dp0.."

python -m pip install -q "pyinstaller" "pillow" "pystray" "playwright"
if errorlevel 1 exit /b 1

python -m playwright install chromium
if errorlevel 1 echo WARN: playwright chromium install failed, will try system Chrome

set "MEAT_SPEC=apps\meat-worker\meat_worker.spec"
python -m PyInstaller --noconfirm --clean "%MEAT_SPEC%"
if errorlevel 1 exit /b 1

copy /Y "apps\meat-worker\config.example.json" "dist\meat-worker\config.example.json" >nul
if not exist "dist\meat-worker\config.json" (
  copy /Y "apps\meat-worker\config.example.json" "dist\meat-worker\config.json" >nul
)

echo.
echo Built: dist\meat-worker\MeatWorker.exe
echo Copy the whole folder dist\meat-worker\ to the idle host.
echo Edit config.json worker_token, then run MeatWorker.exe
echo Docs: docs\wip\meat-worker-exe.md
