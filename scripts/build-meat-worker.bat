@echo off
REM Build MeatWorker onedir into apps\meat-worker\release\ (committed for idle-host download)
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
copy /Y "apps\meat-worker\config.example.json" "%REL%\config.example.json" >nul
if not exist "%REL%\config.json" copy /Y "apps\meat-worker\config.example.json" "%REL%\config.json" >nul
copy /Y "apps\meat-worker\release-README.txt" "%REL%\README.txt" >nul 2>nul

echo.
echo Release folder: %REL%\MeatWorker.exe
echo Commit apps\meat-worker\release\ for idle hosts (no local rebuild needed).
