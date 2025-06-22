// frontend/js/main.js

import { API }            from './api.js';             // サーバー API 呼び出しラッパー
import { UI }             from './ui.js';              // UI 操作ユーティリティ
import { Flow }           from './flow.js';            // ワークフロー図表示ロジック
import { CostChart }      from './chart.js';           // コスト推移チャートクラス
import { WSClient }       from './ws.js';              // WebSocket クライアント
import { initFileUpload } from './file_upload.js';     // ファイルアップロード初期化
import { loadHistory }    from './history.js';         // 過去履歴読み込み

/**
 * frontend/js/main.js
 * ──────────────────────────────────────────────────────────────
 * 画面生成 & 全体フロー制御モジュール
 *
 * • index.html の <script type="module" src="/js/main.js"></script> で読み込む
 * • Vanilla ES Modules 実装
 * • 認証後に auth.js から呼び出される initApp(user) をエントリポイントとする
 */

/**
 * サイドバーを構築する
 * - ナビゲーションリンクをリストで表示
 * - ログアウトボタンにリスナを設定
 * @param {{ email: string, username: string }} user 認証済みユーザ情報
 */
export function buildSidebar(user) {
  const sidebar = document.getElementById('sidebar');
  sidebar.innerHTML = /* html */`
    <div class="list-group mb-3">
      <a href="#control-section" class="list-group-item">操作パネル</a>
      <a href="#status-section"  class="list-group-item">実行状況</a>
      <a href="#log-section"     class="list-group-item">ステップログ</a>
      <a href="#chart-section"   class="list-group-item">コスト推移</a>
      <a href="#upload-section"  class="list-group-item">アップロード</a>
      <a href="#flow-diagram"    class="list-group-item">ワークフロー図</a>
    </div>
    <div class="list-group p-3 border rounded">
      <h6>ユーザ: ${user.username}</h6>
      <small class="text-muted">${user.email}</small>
      <button id="logout-btn" class="list-group-item text-danger mt-2">ログアウト</button>
    </div>
  `;

  // ログアウト処理: サーバーセッション破棄→クライアント状態リセット
  document.getElementById('logout-btn').addEventListener('click', async () => {
    try {
      await API.logout();  // サーバーに /api/auth/logout があれば呼び出す
    } catch (e) {
      console.warn('サーバーログアウト API がエラー:', e);
    }
    // UI.logout() で Cookie 削除 & 表示切り替え
    UI.logout();
  });
}

/**
 * メインペイン（コントロールパネル等）を構築する
 * - 各セクションの HTML テンプレートを挿入
 */
export function buildMain() {
  const mainPane = document.getElementById('main-pane');
  mainPane.innerHTML = /* html */`
    <!-- 操作パネル -->
    <section id="control-section" class="card">
      <div class="card-header">ワークフロー開始</div>
      <div class="card-body">
        <input id="project" type="text" class="form-control mb-2" placeholder="プロジェクト名"/>
        <textarea id="requirement" class="form-control mb-2" rows="4" placeholder="要件を入力"></textarea>
        <button id="startBtn" type="button" class="btn btn-success">開始</button>
      </div>
    </section>

    <!-- 実行状況 & ログ -->
    <div class="row">
      <div class="col-md-6">
        <section id="status-section" class="card mt-3">
          <div class="card-header">実行状況</div>
          <div class="card-body">
            <div>Active Agent: <span id="currentAgent" class="badge bg-warning text-dark">-</span></div>
            <div>Phase: <span id="currentPhase" class="badge bg-secondary text-white">-</span></div>
            <h6 class="mt-2">Agent Interaction</h6>
            <ul id="agentInteractionList" class="list-group interaction-list"></ul>
          </div>
        </section>
      </div>
      <div class="col-md-6">
        <section id="log-section" class="card mt-3">
          <div class="card-header">
            ステップログ
            <span id="loading-indicator" class="badge bg-info ms-2" hidden>実行中…</span>
          </div>
          <div class="card-body">
            <input id="logFilter" type="text" class="form-control mb-2" placeholder="フィルター…"/>
            <ul id="logList" class="list-group log-list"></ul>
          </div>
        </section>
      </div>
    </div>

    <!-- ワークフロー図 -->
    <section id="flow-diagram" class="card mt-3">
      <div class="card-header">ワークフロー図</div>
      <div class="card-body"><div id="flow-diagram-body"></div></div>
    </section>

    <!-- コスト & ファイル管理 -->
    <div id="resource-panels" class="d-flex flex-wrap gap-3 mt-3">
      <section id="chart-section" class="card flex-fill" style="min-width:320px">
        <div class="card-header">コスト推移 (Cost vs Step)</div>
        <div class="card-body p-0" style="height:350px">
          <canvas id="costChart"></canvas>
        </div>
      </section>
      <div id="file-panels" class="d-flex flex-column flex-fill gap-3" style="min-width:320px">
        <section id="upload-section" class="card flex-fill">
          <div class="card-header">アップロードファイル管理</div>
          <div class="card-body">
            <form id="uploadForm" class="d-flex mb-2">
              <input type="file" id="fileInput" class="form-control me-2" accept=".zip,.docx,.xlsx" multiple/>
              <button type="button" id="clearFilesBtn" class="btn btn-outline-secondary">削除</button>
              <button type="submit" class="btn btn-primary ms-2">アップロード</button>
            </form>
            <ul id="uploadList" class="list-group"></ul>
          </div>
        </section>
        <section id="download-section" class="card" hidden>
          <div class="card-header">出力ZIPダウンロード</div>
          <div class="card-body">
            <a id="downloadLink" href="#" class="btn btn-success" download>
              <i class="bi bi-download"></i> ダウンロード
            </a>
          </div>
        </section>
      </div>
    </div>

    <!-- 過去履歴 -->
    <section id="history-section" class="card mt-3">
      <div class="card-header">
        過去のダウンロード履歴
        <button id="refreshHistoryBtn" class="btn btn-sm btn-secondary ms-2">更新</button>
      </div>
      <div class="card-body">
        <div id="history-container"></div>
      </div>
    </section>
  `;
}

/**
 * アプリ初期化処理。ログイン成功後に実行される。
 * - ログインフォームを隠し、メイン画面を表示
 * - サイドバー＆メイン構築、各種モジュール初期化
 * @param {{ email: string, username: string }} user 認証済みユーザ情報
 */
export async function initApp(user) {
  // (既存) ログインフォームを非表示、メイン画面を表示
  const login = document.getElementById('login-container');
  const app   = document.getElementById('app');
  if (login) login.classList.add('d-none');
  if (app)   app.classList.remove('d-none');

  // (既存) サイドバー＆メイン構築
  buildSidebar(user);
  buildMain();

  // (既存) Bootstrap Tooltip 初期化
  UI.enableTooltips();

  // (既存) コストチャート初期化
  const chartEl = document.getElementById('costChart');
  if (chartEl) window.costChart = new CostChart(chartEl);

  // (既存) ファイルアップロード & 履歴読み込み
  initFileUpload();
  loadHistory();

  // (既存) ワークフロー図描画
  const flowBody = document.getElementById('flow-diagram-body');
  if (flowBody) Flow.render(flowBody);

  // (既存) ワークフロー開始ボタン設定
  const startBtn = document.getElementById('startBtn');
  if (startBtn) {
    startBtn.addEventListener('click', async () => {
      const payload = {
        project_name: document.getElementById('project')?.value.trim() || '',
        requirement : document.getElementById('requirement')?.value.trim() || '',
      };
      try {
        const res = await API.startWorkflow(payload);
        const ws = new WSClient(res.workflow_id);
        ws.on(msg => {
          // ここでログ更新やチャート更新を行う
        });
      } catch (err) {
        console.error('ワークフロー開始エラー:', err);
        UI.showToast('ワークフロー開始に失敗しました', 'error');
      }
    });
  }

  // (既存) 履歴更新ボタン設定
  const refreshBtn = document.getElementById('refreshHistoryBtn');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
      loadHistory();
      UI.showToast('履歴を更新しました', 'info');
    });
  }
}
