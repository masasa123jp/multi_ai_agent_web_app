# Agent‑Based WebApp

生成 AI とマルチエージェント・アーキテクチャで **要件入力 → 自動コード生成 → 品質保証 → ZIP 出力** までを一気通貫で行う OSS プラットフォームです。  
本 README では **構成 / インストール / 起動 / 監視 / 開発フロー** を網羅的に説明します。

---

## 1. アーキテクチャ概要

```mermaid
┌─────────┐    WebSocket    ┌───────────┐
│ Frontend│  ←───────────── │ FastAPI WS│
│  Vue3   │                 │  Router   │
└───┬─────┘                 └─────┬─────┘
    │ REST / JSON                │
    ▼                            ▼
┌────────────┐   LangGraph   ┌──────────────┐
│  Backend   │  Orchestrator │  Agents (*)  │
│  FastAPI   │──────────────▶│ code / ui ...│
└────────────┘               └──────────────┘
```
```mermaid
flowchart LR
  FE[Frontend<br>(Bootstrap + ESModules)]
  BE[FastAPI Backend<br>(Async / SQLAlchemy 2)]
  LG[LangGraph<br>Orchestrator]
  SUB((Agents))
  DB[(PostgreSQL)]
  FE -->|REST / WS| BE
  BE -->|async call| LG
  LG --> SUB
  BE -- SQLAlchemy --> DB
  BE <-- OTLP --> TEMPO[(Grafana Tempo)]
  BE <-- OTLP --> LOKI[(Grafana Loki)]

* **Frontend** – Bootstrap + Vanilla ESM。`CostProgress.vue` がリアルタイムコストを描画  
* **Backend** – FastAPI + SQLAlchemy 2 (Async)。OpenTelemetry によりトレース自動収集  
* **Agents**  – 独立 FastAPI サービス。各専門タスクを担当  
* **DB**      – PostgreSQL。DDL は `alembic` で管理  
* **Observability** – Grafana Tempo/Loki に OTLP Export  
```

---

## 2. 必要条件

* Python 3.12+
* Node.js 18+ (フロントビルド時のみ)  
* PostgreSQL 14+
* (任意) Grafana 10 + Tempo + Loki

---

## 3. セットアップ

```bash
git clone https://github.com/your-org/agent-based-webapp.git
cd agent-based-webapp
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp setting.env .env           # 環境変数を調整
alembic upgrade head          # DB マイグレーション
```

---

## 4. 起動方法

### 一括起動 (Windows)

```bat
run_all.bat    :: Frontend 8081 / Backend 5000 / Agents 8001-8009
```

### 個別起動 (例: backend)

```bash
uvicorn backend.server:app --reload --port 5000
```

ブラウザで <http://localhost:8081> を開き、要件を入力して **Start** を押下します。

---

## 5. 主要フォルダ

| パス | 説明 |
|-----|------|
| `backend/`      | API + Orchestrator + Models |
| `frontend/`     | 静的 HTML+JS (`index.html`, `js/*`) |
| `agents/`       | 各 AI エージェント (FastAPI) |
| `common/`       | 汎用ライブラリ (`agent_http.py` など) |
| `migrations/`   | Alembic DDL 管理 |
| `scripts/`      | 運用スクリプト (`run_all.bat` 等) |

---

## 6. 監視・ロギング

* `backend/telemetry.py` で `init_otel()` を呼び出すだけで  
  * **HTTPx/FastAPI/SQLAlchemy/Logging** が自動計装
* `.env` の `OTEL_EXPORTER_OTLP_ENDPOINT` に Collector URL を設定
* Grafana ダッシュボード: `dashboards/tempo.json`, `dashboards/loki.json`

---

## 7. 開発 Tips

* **ホットリロード**: `uvicorn --reload`, `vite --watch`
* **DB Shell**: `pgcli $DATABASE_URL`
* **テスト**: `pytest -q`

---

## 8. ライセンス

Apache-2.0

---

_© 2025 Agent‑Based WebApp Contributors_
