@echo off
REM init_db.bat : DB初期化を順に実行する完全版

REM --- パスワード設定 ---
REM PostgreSQLのスーパーユーザー（postgres）のパスワード
REM set PGPASSWORD=admin
REM agentbased用ユーザーのパスワード
set WEB_LEDGER_PGPASSWORD=mypassword

echo === Creating Database and User ===
psql -U postgres -f .\create_db.sql >> 20250417_01.txt 2>> 20250417_01_error.txt

echo === Creating Tables for agentbased ===
REM agentbased用ユーザーのパスワードを環境変数 PGPASSWORD に一時設定
set PGPASSWORD=%WEB_LEDGER_PGPASSWORD%
psql -U mydbuser -d agentbased -c "SET search_path TO agentbased, public;" -f .\ini_ddl.sql >> 20250417_02.txt 2>> 20250417_02_error.txt

echo === Inserting Sample Data ===
psql -U mydbuser -d agentbased -c "SET search_path TO agentbased, public;" -f .\ini_data.sql >> 20250417_03.txt 2>> 20250417_03_error.txt

echo All done.
pause
