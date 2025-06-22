-- 現在のクライアントエンコーディングの確認
SELECT current_setting('client_encoding');

-- クライアントエンコーディングを UTF8 に設定
SET client_encoding TO 'utf8';

-- データベース "web_ledger" を、DBユーザー "mydbuser" をオーナーとして作成
CREATE DATABASE agentbased OWNER mydbuser;

-- 以下のコマンドは psql シェルで実行してください
\c agentbased mydbuser

-- 必要な拡張機能の有効化
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 専用スキーマ "web_ledger" の作成（必要に応じて）
CREATE SCHEMA IF NOT EXISTS agentbased;
