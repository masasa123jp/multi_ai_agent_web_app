// js/chart.js

/**
 * CostChart クラス定義モジュール
 *
 * - js/ChartES.js から import した Chart クラスでチャート描画
 * - add(), reset() でデータ操作可能
 */

import { Chart } from './ChartES.js';

export class CostChart {
  /**
   * @param {HTMLCanvasElement} canvas コスト表示用 <canvas>
   */
  constructor(canvas) {
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      throw new Error('Canvas 2D context is unavailable');
    }

    // 折れ線グラフの初期化
    this.chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: [],         // ステップラベル
        datasets: [{
          label: '累積コスト',
          data: [],         // コスト値
          fill: false,      // 塗り潰しなし
          tension: 0.4,     // 線の滑らかさ
        }],
      },
      options: {
        responsive: true,
        scales: {
          x: {
            title: { display: true, text: 'ステップ' },
          },
          y: {
            title: { display: true, text: 'USD' },
            beginAtZero: true,
          },
        },
      },
    });
  }

  /**
   * データ点を追加し、チャートを更新
   * @param {string} label ラベル (例: "#1")
   * @param {number} value 値 (USD)
   */
  add(label, value) {
    this.chart.data.labels.push(label);
    this.chart.data.datasets[0].data.push(value);
    this.chart.update();
  }

  /**
   * チャートをリセット (データ/ラベルをクリア)
   */
  reset() {
    this.chart.data.labels = [];
    this.chart.data.datasets[0].data = [];
    this.chart.update();
  }
}
