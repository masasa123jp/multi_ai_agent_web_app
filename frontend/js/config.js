// frontend/js/config.js
// ─────────────────────────────────────────
// エンドポイント＆固定設定

export const Config = {
  paths: {
    // ワークフロー開始
    start:  () => `${location.protocol}//${location.hostname}:5000/api/workflow/async`,
    // 履歴取得
    history:() => `${location.protocol}//${location.hostname}:5000/api/logs/history`,
    // WebSocket (省略)
    ws:     id => `ws://${location.hostname}:5000/api/projects/workflow/ws/${id}`,
    // ダウンロード URL
    dl:     id => `${location.protocol}//${location.hostname}:5000/api/logs/download/${id}`,
    // ファイルアップロード
    upload: () => `${location.protocol}//${location.hostname}:5000/api/files/upload`,

    // ■ 追加部分 ■
    // ログイン
    login:  () => `${location.protocol}//${location.hostname}:5000/api/auth/login`,
    // ログアウト
    logout: () => `${location.protocol}//${location.hostname}:5000/api/auth/logout`,
    // プロフィール取得
    profile:() => `${location.protocol}//${location.hostname}:5000/api/profile/`
  }
};