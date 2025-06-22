-- ===================================================================
-- Schema: public
-- ===================================================================

-- 1. ユーザー情報テーブル
CREATE TABLE agentbased.users (
  email          VARCHAR(255)    PRIMARY KEY,
  username       VARCHAR(100)    NOT NULL,
  password_hash  VARCHAR(255)    NOT NULL,
  role           VARCHAR(50),
  created_at     TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at     TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX  agentbased.idx_users_username ON users(username);

-- 2. プロジェクトテーブル
CREATE TABLE agentbased.projects (
  user_email   VARCHAR(255)    NOT NULL,
  name         VARCHAR(255)    NOT NULL,
  description  TEXT,
  created_at   TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at   TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_email, name),
  FOREIGN KEY (user_email) REFERENCES users(email) ON DELETE CASCADE
);
CREATE INDEX  agentbased.idx_projects_name ON projects(name);

-- 3. エージェントタスク実行履歴
CREATE TABLE agentbased.agent_tasks (
  agent_task_key     BIGSERIAL     PRIMARY KEY,
  project_user_email VARCHAR(255)  NOT NULL,
  project_name       VARCHAR(255)  NOT NULL,
  agent_type         VARCHAR(50)   NOT NULL,
  status             VARCHAR(50)   NOT NULL,
  result             TEXT,
  started_at         TIMESTAMP,
  finished_at        TIMESTAMP,
  created_at         TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (project_user_email, project_name)
    REFERENCES projects(user_email, name)
    ON DELETE CASCADE
);
CREATE INDEX  agentbased.idx_agent_tasks_agent_type ON agent_tasks(agent_type);
CREATE INDEX  agentbased.idx_agent_tasks_status     ON agent_tasks(status);

-- 4. 成果物テーブル
CREATE TABLE agentbased.artifacts (
  artifact_key       BIGSERIAL     PRIMARY KEY,
  project_user_email VARCHAR(255)  NOT NULL,
  project_name       VARCHAR(255)  NOT NULL,
  artifact_type      VARCHAR(50)   NOT NULL,
  content            TEXT,
  created_at         TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (project_user_email, project_name)
    REFERENCES projects(user_email, name)
    ON DELETE CASCADE
);
CREATE INDEX  agentbased.idx_artifacts_artifact_type ON artifacts(artifact_type);

-- 5. ステークホルダーフィードバックテーブル
CREATE TABLE agentbased.stakeholder_feedback (
  feedback_key       BIGSERIAL     PRIMARY KEY,
  project_user_email VARCHAR(255)  NOT NULL,
  project_name       VARCHAR(255)  NOT NULL,
  stakeholder        VARCHAR(255),
  feedback           TEXT,
  created_at         TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (project_user_email, project_name)
    REFERENCES projects(user_email, name)
    ON DELETE CASCADE
);

-- 6. 品質テスト結果テーブル
CREATE TABLE agentbased.test_results (
  test_result_key    BIGSERIAL     PRIMARY KEY,
  project_user_email VARCHAR(255)  NOT NULL,
  project_name       VARCHAR(255)  NOT NULL,
  qa_report          TEXT,
  test_coverage      DECIMAL(5,2),
  created_at         TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (project_user_email, project_name)
    REFERENCES projects(user_email, name)
    ON DELETE CASCADE
);

-- 7. セキュリティレポートテーブル
CREATE TABLE agentbased.security_reports (
  security_report_key BIGSERIAL    PRIMARY KEY,
  project_user_email  VARCHAR(255) NOT NULL,
  project_name        VARCHAR(255) NOT NULL,
  report              TEXT,
  vulnerability_count INTEGER,
  created_at          TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (project_user_email, project_name)
    REFERENCES projects(user_email, name)
    ON DELETE CASCADE
);

-- 8. ITコンサルティングレポートテーブル
CREATE TABLE agentbased.it_consulting_reports (
  it_consult_report_key BIGSERIAL  PRIMARY KEY,
  project_user_email     VARCHAR(255) NOT NULL,
  project_name           VARCHAR(255) NOT NULL,
  recommendation         TEXT,
  created_at             TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (project_user_email, project_name)
    REFERENCES projects(user_email, name)
    ON DELETE CASCADE
);

-- 9. DBAデザインテーブル
CREATE TABLE agentbased.dba_designs (
  dba_design_key     BIGSERIAL     PRIMARY KEY,
  project_user_email VARCHAR(255)  NOT NULL,
  project_name       VARCHAR(255)  NOT NULL,
  design_schema      TEXT,
  created_at         TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (project_user_email, project_name)
    REFERENCES projects(user_email, name)
    ON DELETE CASCADE
);

-- 10. システムログテーブル
CREATE TABLE agentbased.system_logs (
  log_key     BIGSERIAL    PRIMARY KEY,
  log_level   VARCHAR(50),
  message     TEXT,
  created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX  agentbased.idx_system_logs_level      ON system_logs(log_level);
CREATE INDEX  agentbased.idx_system_logs_created_at ON system_logs(created_at);

-- 11. ファイル添付テーブル
CREATE TABLE agentbased.file_attachments (
  file_attachment_key BIGSERIAL    PRIMARY KEY,
  project_user_email  VARCHAR(255),
  project_name        VARCHAR(255),
  filename            VARCHAR(255) NOT NULL,
  file_type           VARCHAR(100),
  file_size           INTEGER,
  file_data           BYTEA,
  upload_time         TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (project_user_email, project_name)
    REFERENCES projects(user_email, name)
    ON DELETE CASCADE
);
CREATE INDEX  agentbased.idx_file_attachments_filename ON file_attachments(filename);

-- 12. ワークフロー実行テーブル
CREATE TABLE agentbased.workflow_executions (
  wf_exec_key         BIGSERIAL    PRIMARY KEY,
  project_user_email  VARCHAR(255),
  project_name        VARCHAR(255),
  status              VARCHAR(50) NOT NULL,
  start_time          TIMESTAMP   NOT NULL,
  end_time            TIMESTAMP   NOT NULL,
  summary             TEXT,
  created_at          TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (project_user_email, project_name)
    REFERENCES projects(user_email, name)
    ON DELETE CASCADE
);
CREATE INDEX  agentbased.idx_workflow_executions_status ON workflow_executions(status);

-- 13. API利用ログテーブル
CREATE TABLE agentbased.api_usage_logs (
  api_usage_key  BIGSERIAL    PRIMARY KEY,
  api_name       VARCHAR(100) NOT NULL,
  request_time   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  tokens_used    INTEGER,
  cost           NUMERIC(10,6),
  details        TEXT
);
CREATE INDEX  agentbased.idx_api_usage_logs_api_name    ON api_usage_logs(api_name);
CREATE INDEX  agentbased.idx_api_usage_logs_request_time ON api_usage_logs(request_time);


-- ===================================================================
-- Schema: agentbased
-- ===================================================================
CREATE SCHEMA IF NOT EXISTS agentbased;

-- ログファイル ZIP 保管用テーブル
CREATE TABLE agentbased.agentbased.log_file_archives (
  log_archive_id     SERIAL      PRIMARY KEY,
  project_user_email VARCHAR(255) NOT NULL,
  project_name       VARCHAR(255) NOT NULL,
  filename           VARCHAR(255) NOT NULL,
  zip_data           BYTEA        NOT NULL,
  created_at         TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_log_archives_project FOREIGN KEY (project_user_email, project_name)
    REFERENCES projects(user_email, name)
    ON DELETE CASCADE
);
CREATE INDEX  agentbased.idx_log_file_archives_created_at
  ON agentbased.log_file_archives(created_at);

-- ワークフロー実行ログ
CREATE TABLE agentbased.agentbased.workflow_logs (
  id            SERIAL       PRIMARY KEY,
  project_name  VARCHAR(256) NOT NULL,
  requirement   TEXT         NOT NULL,
  zip_data      BYTEA,
  model         VARCHAR(50),
  max_cost      DOUBLE PRECISION,
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- ワークフロー実行ステップ詳細ログ
CREATE TABLE agentbased.agentbased.workflow_log_steps (
  id              SERIAL       PRIMARY KEY,
  workflow_log_id INTEGER      NOT NULL,
  step_name       VARCHAR(128) NOT NULL,
  result_text     JSON         NOT NULL,
  seconds_elapsed DOUBLE PRECISION,
  error_message   TEXT,
  created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
  CONSTRAINT fk_workflow_log_steps_log
    FOREIGN KEY (workflow_log_id)
    REFERENCES agentbased.workflow_logs(id)
    ON DELETE CASCADE
);

-- アーカイブリンクテーブル
CREATE TABLE agentbased.agentbased.log_archives (
  id              SERIAL       PRIMARY KEY,
  workflow_log_id INTEGER      NOT NULL,
  user_email      VARCHAR(255),
  project_name    VARCHAR(255),
  filename        VARCHAR(255),
  zip_data        BYTEA,
  created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
  CONSTRAINT fk_log_archives_workflow_log
    FOREIGN KEY (workflow_log_id)
    REFERENCES agentbased.workflow_logs(id)
    ON DELETE CASCADE
);
CREATE INDEX  agentbased.idx_log_archives_workflow_log_id
  ON agentbased.log_archives(workflow_log_id);

ALTER TABLE agentbased.it_consulting_reports
  ADD COLUMN consultant VARCHAR(100) NOT NULL DEFAULT '';

-- 1. updated_at カラムを追加（NOT NULL・デフォルト CURRENT_TIMESTAMP）
ALTER TABLE agentbased.it_consulting_reports
ADD COLUMN updated_at TIMESTAMP WITHOUT TIME ZONE
    NOT NULL
    DEFAULT CURRENT_TIMESTAMP;

-- 2. 既存レコードのバックフィル（念のため NULL チェック）
UPDATE agentbased.it_consulting_reports
SET updated_at = created_at
WHERE updated_at IS NULL;

ALTER TABLE agentbased.stakeholder_feedback
  ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

-- 最大ループ回数カラムの追加
ALTER TABLE agentbased.workflow_logs
ADD COLUMN IF NOT EXISTS max_loops INTEGER NOT NULL DEFAULT 3;