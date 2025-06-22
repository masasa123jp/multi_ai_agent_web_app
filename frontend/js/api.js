// frontend/js/api.js
// ─────────────────────────────────────────
// fetchラッパー – レスポンスがOKでない場合は例外を投げる

import { Config } from './config.js';

async function _json(res) {
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export const API = {
  /** ワークフロー開始 */
  startWorkflow: data => fetch(Config.paths.start(), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  }).then(_json),

  /** 履歴取得 */
  getHistory: () => fetch(Config.paths.history(), {
    method:      'GET',
    credentials: 'include',    // Cookie や認証ヘッダーを含める
  }).then(_json),

  /** ファイルアップロード */
  uploadFiles: fd => fetch(Config.paths.upload(), {
    method: 'POST',
    body: fd
  }).then(_json),

  /** ダウンロード用URL生成 */
  archiveDownloadUrl: id => Config.paths.dl(id)
};
