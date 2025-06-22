@echo off
rem ============================================================================
rem run_e2e_tests.bat
rem ----------------------------------------------------------------------------
rem Windows ローカル環境で E2E 統合テストを実行するスクリプト
rem • 仮想環境の有効化
rem • テスト用 DB の初期化 (Python スクリプト呼び出し)
rem • DB マイグレーション適用 (alembic)
rem • pytest で E2E テストのみ実行
rem ----------------------------------------------------------------------------

rem --- 1) 仮想環境を有効化 -----------------------------------------------
if exist "..\..\venv\Scripts\activate.bat" (
    call ..\..\venv\Scripts\activate.bat
) else (
    echo [ERROR] 仮想環境が見つかりません。".venv" を作成してから再実行してください。
    exit /b 1
)

rem --- 2) テスト用 DB をリセット＆初期化 --------------------------------
if exist "test.db" (
    echo [INFO] 既存の test.db を削除しています...
    del /f /q test.db
)
echo [INFO] Python スクリプトでテスト用 DB を初期化しています...
python init_test_db.py
if errorlevel 1 (
    echo [ERROR] test.db の初期化に失敗しました。
    exit /b 1
)

rem --- 3) 環境変数設定 (SQLite + JWT シークレット) ----------------------
set "DATABASE_URL=sqlite+aiosqlite:///./test.db"
set "JWT_SECRET=test-secret"

rem --- 4) DB マイグレーション適用 ---------------------------------------
echo [INFO] DB マイグレーションを適用中...
alembic upgrade head
if errorlevel 1 (
    echo [ERROR] Alembic migration failed. テストを中断します。
    exit /b 1
)

rem --- 5) E2E テスト実行 -----------------------------------------------
echo [INFO] 統合テストを実行しています: tests\integration\test_e2e_workflow.py
pytest tests/integration/test_e2e_workflow.py --disable-warnings --maxfail=1 -q
if errorlevel 1 (
    echo [ERROR] 統合テストに失敗しました。
    exit /b 1
)

echo [SUCCESS] 統合テストが成功しました！
exit /b 0
