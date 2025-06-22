/* WebSocket クライアント – 実行状況をリアルタイム受信 */
import { Config } from "./config.js";
import { UI     } from "./ui.js";
import { Flow   } from "./flow.js";

export class WSClient {
  constructor(workflowId, chartRef) {
    this.url = `${Config.wsBase}/projects/workflow/ws/${workflowId}`;
    this.chart = chartRef;
    this._connect();
  }

  _connect(retry = 0) {
    this.ws = new WebSocket(this.url);

    this.ws.onopen    = () => UI.toggleSpinner(false);
    this.ws.onmessage = (ev) => this._handle(JSON.parse(ev.data));
    this.ws.onclose   = () => {
      if (retry < 5) setTimeout(() => this._connect(retry + 1), 2 ** retry * 1000);
      else UI.toast("WebSocket 再接続失敗","warning");
    };
  }

  _handle(msg) {
    /* ダウンロードリンク生成 */
    if (msg.archive_id) {
      document.getElementById("downloadLink").href =
        `${Config.apiBase}/logs/download/${msg.archive_id}`;
      document.getElementById("download-section").hidden = false;
      return;
    }

    /* Active Agent & Phase 表示 */
    if (msg.current_agent) {
      document.getElementById("currentAgent").textContent = msg.current_agent;
      Flow.highlight(msg.current_agent);
    }
    if (msg.step_name) {
      document.getElementById("currentPhase").textContent = msg.step_name;
    }

    /* ログ表示 */
    if (msg.step_name) {
      UI.appendUL("logList",
        `<strong>${msg.step_name}</strong><pre class="mb-0">${JSON.stringify(msg.output_data,null,2)}</pre>`
      );
    }

    /* Agent interaction */
    if (msg.from_agent) {
      UI.appendUL("agentInteractionList", `${msg.from_agent} → ${msg.to_agent}`);
    }

    /* コスト推移 */
    try {
      const cost = Number(msg.output_data?.cost_used || msg.output_data?.cost);
      if (cost) this.chart.push(msg.step_name, cost);
    } catch {}
  }
}
