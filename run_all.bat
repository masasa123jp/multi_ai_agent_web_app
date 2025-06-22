@echo off
:: ===============================================================
:: run_all.bat – 開発環境フル起動スクリプト (Windows 専用)
:: 1) 既存ポートを解放 → 2) Frontend HTTP → 3) Backend FastAPI
:: 4) 8 つの AI エージェントを順次起動 → 5) ポート監視ダンプ
:: ===============================================================

chcp 65001 > nul
setlocal enabledelayedexpansion
pushd "%~dp0"

REM ---------- 1. ポート退避 / 強制終了 ----------
for %%P in (8081 5000 8001 8002 8003 8004 8005 8006 8007 8008 8009) do (
for /f "tokens=5" %%I in ('netstat -ano ^| findstr /R /C:":%%P .*LISTENING"') do (
if not "%%I"=="4" (
echo Killing %%I on port %%P
taskkill /F /PID %%I > nul 2>&1
)
)
)

REM ---------- 2. Frontend (静的) ----------
if exist "frontend\index.html" (
start "Frontend 8081" cmd /k python -m http.server 8081 --bind 127.0.0.1 --directory frontend
) else (
echo [ERROR] frontend\index.html not found
)

REM ---------- 3. Backend (FastAPI) ----------
if exist "backend\server.py" (
start "Backend 5000" cmd /k python -m uvicorn backend.server:app --host 127.0.0.1 --port 5000 --reload --log-level debug
) else (
echo [ERROR] backend\server.py not found
)

REM ---------- 4. Agents (FastAPI Microservices) ----------
set AGENT_LIST=stakeholder:8008 project_manager:8007 it_consulting:8005 dba:8006 ui_generation:8002 code_generation:8001 qa:8003 security:8004 code_patch:8009

for %%A in (%AGENT_LIST%) do (
for /f "tokens=1,2 delims=:" %%B in ("%%A") do (
set NAME=%%B
set PORT=%%C
start "!NAME! !PORT!" cmd /k python -m uvicorn agents.!NAME!.app:app --host 127.0.0.1 --port !PORT! --reload
)
)

REM ---------- 5. 起動確認 ----------
echo Waiting 25 seconds for services to initialize ...
timeout /t 25 /nobreak > nul

echo ==== Listening ports ====
for %%P in (8081 5000 8001 8002 8003 8004 8005 8006 8007 8008 8009) do (
netstat -ano | find "LISTENING" | find ":%P " > nul
if errorlevel 1 (
echo [ERROR] Port %%P not listening
) else (
echo [ OK ] Port %%P ready
)
)

popd
pause