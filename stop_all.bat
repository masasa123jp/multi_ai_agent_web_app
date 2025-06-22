@echo off
REM ===================================================================
REM  stop_all.bat – 全サービスの強制停止
REM ===================================================================

chcp 65001 >nul
echo Stopping services...

for %%P in (8081 5000 4010 8001 8002 8003 8004 8005 8006 8007 8008 8009) do (
  for /f "tokens=5" %%I in ('netstat -aon ^| findstr /R /C:":%%P .*LISTENING"') do (
    if not "%%I"=="4" (
      taskkill /F /PID %%I >nul 2>&1
      echo   Stopped PID %%I on port %%P
    ) else (
      echo   Skipped SYSTEM PID 4 on port %%P
    )
  )
)

echo All services stopped.
pause
