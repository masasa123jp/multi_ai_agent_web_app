// frontend/js/history.js

import { API } from './api.js';
import { UI }  from './ui.js';  // UI.showToast() など汎用UIユーティリティ

/**
 * 履歴データをテーブル形式で画面に描画する
 * @param {Array<object>} data - 履歴アイテム配列
 *    各 item のプロパティ:
 *      id         : アーカイブID
 *      filename   : ZIPファイル名
 *      created_at : 作成日時（ISO文字列）
 */
function renderHistoryTable(data) {
  // 1) 描画先コンテナ取得
  const container = document.getElementById('history-container');
  if (!container) {
    console.warn('renderHistoryTable: #history-container が見つかりません');
    return;
  }

  // 2) 既存コンテンツをクリア
  container.innerHTML = '';

  // 3) テーブル要素の生成
  const table = document.createElement('table');
  table.className = 'table table-striped';

  // 4) ヘッダー行を作成
  const thead = document.createElement('thead');
  thead.innerHTML = `
    <tr>
      <th>ID</th>
      <th>ファイル名</th>
      <th>作成日時</th>
    </tr>
  `;
  table.appendChild(thead);

  // 5) ボディ行を生成
  const tbody = document.createElement('tbody');
  data.forEach(item => {
    const tr = document.createElement('tr');
    // filename を <a> タグで囲み、download属性を付与
    const downloadUrl = API.archiveDownloadUrl(item.id);
    tr.innerHTML = `
      <td>${item.id}</td>
      <td>
        <a href="${downloadUrl}" download="${item.filename}">
          ${item.filename}
        </a>
      </td>
      <td>${new Date(item.created_at).toLocaleString()}</td>
    `;
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);

  // 6) コンテナにテーブルを追加
  container.appendChild(table);
}

/**
 * 履歴データを取得し画面に描画
 */
export async function loadHistory() {
  try {
    // 1) API 呼び出し
    const data = await API.getHistory();

    // 2) テーブル描画
    renderHistoryTable(data);

  } catch (err) {
    console.error('loadHistory Error:', err);

    // 認証エラー(HTTP 401)なら再ログインを促す
    if (err.message.startsWith('HTTP 401')) {
      UI.showToast('セッションが切れました。再ログインしてください。', 'warning');
      document.getElementById('app').style.display = 'none';
      document.getElementById('login-container').style.display = 'flex';
    } else {
      // その他のエラー
      UI.showToast('履歴取得中にエラーが発生しました。', 'error');
    }
  }
}
