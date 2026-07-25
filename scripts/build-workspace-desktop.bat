@echo off
REM Build TUODIAO desktop: Vite web + Electron shell -> release\*.exe
cd /d "%~dp0.."

echo [1/3] Build apps\web ...
pushd apps\web
call npm install
if errorlevel 1 exit /b 1
call npm run build
if errorlevel 1 exit /b 1
popd

echo [2/3] Copy web-dist into workspace-desktop ...
pushd apps\workspace-desktop
call npm install
if errorlevel 1 exit /b 1
call node scripts\copy-web-dist.cjs
if errorlevel 1 exit /b 1

echo [3/3] electron-builder (stage in %%TEMP%%) ...
set "STAGE=%TEMP%\yoto-workspace-desktop-dist"
if exist "%STAGE%" rmdir /s /q "%STAGE%"
mkdir "%STAGE%" 2>nul
call npx electron-builder --win --config.directories.output="%STAGE%"
if errorlevel 1 exit /b 1
popd

set "REL=%cd%\apps\workspace-desktop\release"
if not exist "%REL%" mkdir "%REL%"
del /q "%REL%\*.exe" 2>nul
copy /Y "%STAGE%\TUODIAO-*-win-x64.exe" "%REL%\" >nul
copy /Y "%STAGE%\TUODIAO-*-portable.exe" "%REL%\" >nul

echo.
echo Release OK: %REL%
dir /b "%REL%\*.exe"
