@echo off
cd /d "%~dp0.."
pip install -e . -q
cd apps\api
pip install -r requirements.txt -q
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
