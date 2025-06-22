// frontend/js/ui.js

/**
 * ui.js
 *
 * UI 操作ユーティリティ群。
 * • ツールチップ有効化
 * • ローディングスピナーの表示／非表示
 * • コストチャート更新
 * • 汎用トースト表示・非表示
 * • ログアウト処理（クライアント側のみ）
 */

////////////////////////////////////////////////////////////////////////////////
// 外部ライブラリの ESM インポート
////////////////////////////////////////////////////////////////////////////////
// Bootstrap の ESM ビルドから Tooltip コンポーネントのみを取り込む
// CDN URL はバージョンに合わせて調整してください
import { Tooltip } from 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.esm.min.js';

export const UI = {
  /**
   * data-bs-toggle="tooltip" を持つ要素に対して
   * Bootstrap のツールチップを有効化
   */
  enableTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipTriggerList.forEach(el => new Tooltip(el));
  },

  /**
   * コンテナ要素にローディングスピナーを挿入
   * @param {HTMLElement} container
   */
  showSpinner(container) {
    container.insertAdjacentHTML(
      'afterbegin',
      '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>'
    );
  },

  /**
   * ローディングスピナーを削除
   * @param {HTMLElement} container
   */
  hideSpinner(container) {
    const spinner = container.querySelector('.spinner-border');
    if (spinner) spinner.remove();
  },

  /**
   * コストチャートを更新（外部の CostChart インスタンスを呼び出し）
   * @param {number[]} dataPoints
   */
  updateCostChart(dataPoints) {
    if (window.costChart) window.costChart.update(dataPoints);
  },

  /**
   * 汎用トーストを表示
   * @param {string} message - トースト本文
   * @param {"success"|"error"|"info"} type - 背景色クラス
   */
  showToast(message, type = 'info') {
    // 表示中のトーストをクリアして重複を防止
    this.clearToasts();

    const toastHtml = `
      <div class="toast align-items-center text-bg-${type}" role="alert" aria-live="assertive" aria-atomic="true">
        <div class="d-flex">
          <div class="toast-body">${message}</div>
          <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
      </div>`;
    document.body.insertAdjacentHTML('beforeend', toastHtml);
    const toastEl = document.body.lastElementChild;
    if (window.bootstrap?.Toast) {
      const bsToast = new window.bootstrap.Toast(toastEl, { delay: 3000 });
      bsToast.show();
    }
  },

  /**
   * 表示中のトーストを全て削除
   */
  clearToasts() {
    document.querySelectorAll('.toast').forEach(toast => toast.remove());
  },

  /**
   * ログアウト処理
   * - access_token Cookie を削除
   * - サーバーセッション破棄APIがあれば呼び出し
   * - 最終的にルートURLへリダイレクト
   * - （オプション）ログアウト完了時にトースト
   */
  async logout() {
    // 1) JWT Cookie をクリア
    document.cookie = 'access_token=; path=/; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT;';

    // 2) サーバー側でセッション破棄 API があれば呼び出し
    try {
      await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' });
    } catch (e) {
      console.warn('サーバーログアウト API エラー:', e);
    }

    // 3) トップページへリダイレクト
    window.location.href = '/';

    // 4) （リダイレクト前に短時間でも表示したい場合）
    // this.showToast('ログアウトしました', 'info');
  }
};
