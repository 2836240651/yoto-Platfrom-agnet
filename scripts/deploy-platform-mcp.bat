@echo off
REM Deploy platform-mcp (incl. Douyin job queue) to yoto host.
REM Reads DEPLOY_PASS / DOUYIN_WORKER_TOKEN / COMMANDER_ACCESS_TOKEN from .env
cd /d "%~dp0.."
node scripts\deploy-platform-mcp.js
