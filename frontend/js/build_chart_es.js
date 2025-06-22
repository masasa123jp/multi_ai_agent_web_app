// js/build_chart_es.js

/**
 * Chart.js UMD → ESM 化ビルドスクリプト（素のJavaScript / Node.js）
 *
 * • CDN から UMD ビルドを取得
 * • window.Chart を ESM export する文を末尾に追記
 * • 出力先 (js/ChartES.js) に書き出し
 *
 * 実行:
 *   node js/build_chart_es.js
 */

import fs from 'fs/promises';       // Node.js の Promise ベースファイルAPI
import https from 'https';          // HTTPS リクエスト用
import path from 'path';            // ファイルパス操作用

// ── 1) CDN 版 UMD ビルドの URL ────────────────────────────────
const UMD_URL = 'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js';

/**
 * HTTPS GET してテキストを取得するヘルパー
 * @param {string} url
 * @returns {Promise<string>}
 */
function fetchText(url) {
  return new Promise((resolve, reject) => {
    https.get(url, res => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(data));
    }).on('error', reject);
  });
}

async function buildChartES() {
  try {
    // ── 2) UMD コードを取得 ───────────────────────────────────
    console.log(`Fetching UMD build from ${UMD_URL}…`);
    const umdCode = await fetchText(UMD_URL);

    // ── 3) ESM 用エクスポート文を追加 ─────────────────────────────
    const esmCode = umdCode + '\n\n' +
      '// ESM 用エクスポート\n' +
      'const Chart = window.Chart;\n' +
      'export { Chart };\n';

    // ── 4) 出力先パスを組み立て ─────────────────────────────────
    // process.cwd()（カレント作業ディレクトリ）を基準に js/ChartES.js へ保存
    const outDir  = path.join(process.cwd(), 'js');
    const outPath = path.join(outDir, 'ChartES.js');

    // ディレクトリが存在しなければ作成
    await fs.mkdir(outDir, { recursive: true });

    // ── 5) ファイル書き出し ───────────────────────────────────
    await fs.writeFile(outPath, esmCode, 'utf-8');
    console.log(`✅ ChartES.js written to ${outPath}`);
  } catch (err) {
    console.error('❌ build_chart_es failed:', err);
    process.exit(1);
  }
}

// スクリプト実行
buildChartES();
