# backend/api_usage_service.py
import os
import psycopg2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 環境変数から DB 接続文字列を取得。例: "postgresql://username:password@host:port/dbname"
DB_URI = os.environ.get("DB_URI", "postgresql://mydbuser:mypassword@localhost:5432/agentbased")

def log_api_usage(api_name: str, tokens_used: int, cost: float, details: str) -> None:
    """
    API 利用ログを api_usage_logs テーブルに記録する関数。
    
    Parameters:
      api_name: 呼び出し対象のAPI名称（例: "gpt-4o-mini", "o3-mini-high" など）
      tokens_used: 利用したトークン数
      cost: 利用したトークンに基づくコスト（数値）
      details: API 呼び出しの詳細なログ情報
    """
    query = """
    INSERT INTO api_usage_logs (api_name, tokens_used, cost, details)
    VALUES (%s, %s, %s, %s)
    """
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(DB_URI)
        cursor = conn.cursor()
        cursor.execute(query, (api_name, tokens_used, cost, details))
        conn.commit()
        logger.info(f"Logged API usage for {api_name} successfully.")
    except Exception as e:
        logger.error(f"Error logging API usage: {e}")
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# テスト実行用のコード
if __name__ == "__main__":
    try:
        log_api_usage("gpt-4o-mini", 150, 0.000090, "Sample API call for code generation")
        print("API usage log entry created successfully.")
    except Exception as e:
        print(f"Failed to create API usage log entry: {e}")
