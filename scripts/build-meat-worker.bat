@echo off
REM Build MeatWorker onedir into apps\meat-worker\release\
cd /d "%~dp0.."

python -m pip install -q "pyinstaller" "pillow" "pystray" "playwright"
if errorlevel 1 exit /b 1

set "MEAT_SPEC=apps\meat-worker\meat_worker.spec"
python -m PyInstaller --noconfirm --clean "%MEAT_SPEC%"
if errorlevel 1 exit /b 1

set "REL=apps\meat-worker\release"
if exist "%REL%" rmdir /s /q "%REL%"
mkdir "%REL%"
xcopy /E /I /Y "dist\meat-worker\*" "%REL%\" >nul

REM Guarantee playwright driver exists even if a wrong hook stripped it
python scripts\_ensure_playwright_driver_in_release.py
if errorlevel 1 exit /b 1

copy /Y "apps\meat-worker\config.example.json" "%REL%\config.example.json" >nul
copy /Y "apps\meat-worker\release-README.txt" "%REL%\README.txt" >nul

REM Prefill worker_token from repo .env (idle host should just run)
python scripts\_prefill_meat_release_config.py
if errorlevel 1 exit /b 1

if not exist "%REL%\_internal\playwright\driver\node.exe" (
  echo ERROR: playwright driver missing in release
  exit /b 1
)

echo.
echo Release OK: %REL%\MeatWorker.exe
echo Driver: %REL%\_internal\playwright\driver\node.exe
