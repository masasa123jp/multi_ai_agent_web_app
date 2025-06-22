:: tests\run_tests.bat
@echo off
REM ====================================================================
REM run_tests.bat – Windows 環境でのテスト一括実行スクリプト
REM tests フォルダ直下に配置し、コマンドプロンプトで実行してください
REM ====================================================================

REM Python 仮想環境がある場合はアクティベート
IF EXIST "..\venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call ..\venv\Scripts\activate.bat
) ELSE (
    echo No virtual environment detected, continuing with system Python
)

REM テスト実行
echo Running pytest...
pytest --maxfail=1 --disable-warnings -q

REM 終了コードをキャプチャ
set TEST_RETVAL=%ERRORLEVEL%

REM 終了コード出力
if %TEST_RETVAL% equ 0 (
    echo All tests passed.
) else (
    echo Some tests failed. Exit code: %TEST_RETVAL%
)

exit /b %TEST_RETVAL%
