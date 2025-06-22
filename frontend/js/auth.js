// frontend/js/auth.js

/**
 * auth.js
 * ──────────────────────────────────────────────────────────────
 * 認証関連ロジックモジュール
 *
 * • ログインフォームの送信処理
 * • プロフィール API のレスポンス構造に合わせてユーザ情報を正しく取得
 * • 認証成功後にログイン画面を完全に削除し、再レンダリング不要とする
 * • 送信ボタンの二重送信防止
 * • サイドバー＆メイン画面を動的構築し各種モジュールを初期化
 */

import { UI }             from './ui.js';          // UI 操作ユーティリティ
import { buildSidebar,
         buildMain }      from './main.js';        // サイドバー＆メイン構築
import { Flow }           from './flow.js';        // ワークフロー図描画
import { CostChart }      from './chart.js';       // コストチャート描画
import { initFileUpload } from './file_upload.js'; // ファイルアップロード初期化
import { loadHistory }    from './history.js';     // 履歴ロード
import { Config }         from './config.js';      // API エンドポイント定義

// ── DOM 要素参照 ────────────────────────────────────────────────────────────
const loginForm      = document.getElementById('loginForm');
const loginContainer = document.getElementById('login-container');
const appContainer   = document.getElementById('app');
const errorMessage   = document.getElementById('errorMessage');
const submitButton   = loginForm.querySelector('button[type="submit"]');

/**
 * 認証成功後にアプリケーション本体を初期化
 * @param {{ email: string, username: string }} user - パース済みユーザ情報
 */
function initApp(user) {
  // ── ガード: 既に初期化済みなら何もしない ───────────────────────────────
  if (document.getElementById('welcome-header')) return;

  // 1) ログイン画面を DOM から完全に削除
  loginContainer.remove();

  // 2) メイン画面を表示（d-none クラスを解除）
  appContainer.classList.remove('d-none');

  // 3) グローバルにユーザ情報を保持（他モジュールから参照可能）
  window.__CURRENT_USER__ = user;

  // 4) ヘッダーに「ようこそ、XXXさん」を追加
  const header = document.createElement('h2');
  header.id = 'welcome-header';
  header.textContent = `ようこそ、${user.username}さん`;
  appContainer.prepend(header);

  // 5) サイドバー／メインコンテンツ構築 & ツールチップ有効化
  buildSidebar(user);
  buildMain();
  UI.enableTooltips();

  // 6) Vueコンポーネント & その他モジュール初期化
  new CostChart(document.getElementById('costChart'));
  Flow.render(document.getElementById('flow-diagram-body'));
  initFileUpload();
  loadHistory();
}

/**
 * ログインフォーム送信ハンドラ
 * - form のデフォルト送信を抑止
 * - 二重送信防止（送信中はボタンを無効化）
 */
async function onLoginSubmit(event) {
  event.preventDefault();            // ★ ページリロードを防止
  errorMessage.textContent = '';     // 前回エラーをクリア
  submitButton.disabled = true;      // 二重送信防止

  // フォームフィールドから入力値を取得
  const formData = new FormData(loginForm);
  const username = (formData.get('username') || '').toString().trim();
  const password = (formData.get('password') || '').toString().trim();

  // 入力バリデーション
  if (!username || !password) {
    errorMessage.textContent = 'メールアドレスとパスワードを入力してください';
    submitButton.disabled = false;
    return;
  }

  try {
    // 1) ログイン API 呼び出し
    const loginRes = await fetch(Config.paths.login(), {
      method:      'POST',
      headers:     { 'Content-Type': 'application/x-www-form-urlencoded' },
      body:        new URLSearchParams({ username, password }),
      credentials: 'include',
    });
    if (!loginRes.ok) {
      errorMessage.textContent = 'ログイン失敗：認証情報を確認してください';
      return;
    }

    // 2) プロフィール API 呼び出し（data プロパティ対応）
    const profileRes = await fetch(Config.paths.profile(), {
      method:      'GET',
      credentials: 'include',
    });
    if (!profileRes.ok) {
      errorMessage.textContent = 'ユーザー情報取得エラー';
      return;
    }
    const profileJson = await profileRes.json();
    const user        = profileJson.data ?? profileJson;

    // 3) 認証成功：トースト通知＋アプリ初期化
    UI.showToast('ログインに成功しました', 'success');
    initApp(user);

    // 4) イベントリスナ解除（二重登録を防ぐ）
    loginForm.removeEventListener('submit', onLoginSubmit);

  } catch (err) {
    console.error('ログイン処理中にエラーが発生しました:', err);
    errorMessage.textContent = '通信エラーが発生しました。再度お試しください。';
  } finally {
    // 5) 送信ボタンを再度有効化
    submitButton.disabled = false;
  }
}

// 初期ロード時にフォーム送信ハンドラを登録
loginForm.addEventListener('submit', onLoginSubmit);
