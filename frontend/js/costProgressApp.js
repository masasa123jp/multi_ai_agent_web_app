// costProgressApp.js
// 
// Vue 3 を利用してワークフローの累積コスト進捗を
// ARIA対応プログレスバーでリアルタイム表示するコンポーネント。
//
// Props:
//   - workflowId: WebSocket 接続に使用するワークフローID (Number, required)
//   - maxCost   : プログレスバーの最大値 (USD, Number, required)
//
// WebSocket メッセージ:
//   { type: 'cost_update', total_cost: <number> }
// を受信すると currentCost を更新します。

// Vue グローバルビルド (vue.global.prod.js) を前提に関数を取得
const {
  createApp,
  defineComponent,
  ref,
  computed,
  onMounted,
  onBeforeUnmount
} = Vue;

// 通貨フォーマット用ユーティリティ
function formatCurrencyUSD(value) {
  return value.toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
  });
}

// --- CostProgress コンポーネント定義 ---
const CostProgress = defineComponent({
  name: 'CostProgress',

  props: {
    workflowId: { type: Number, required: true },
    maxCost:    { type: Number, required: true },
  },

  setup(props) {
    // 現在の累積コスト
    const currentCost = ref(0);

    // プログレスバーの幅（%）
    const fillPercentage = computed(() => {
      return props.maxCost > 0
        ? Math.min(100, (currentCost.value / props.maxCost) * 100)
        : 0;
    });

    // ラベル表示用文字列
    const labelCost    = computed(() => formatCurrencyUSD(Math.floor(currentCost.value)));
    const labelMaxCost = computed(() => formatCurrencyUSD(Math.floor(props.maxCost)));

    let socket = null;

    onMounted(() => {
      // workflowId が無効または 0 以下なら WebSocket を起動せずログ出力して終了
      if (!Number.isFinite(props.workflowId) || props.workflowId <= 0) {
        console.warn('CostProgress: Invalid workflowId, skipping WebSocket', props.workflowId);
        return;
      }

      // 1) WebSocket URL 組み立て
      const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
      const wsUrl = `${protocol}://${location.host}/api/cost/ws/${props.workflowId}`;

      // 2) ソケット接続
      socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        console.log('CostProgress WS connected:', wsUrl);
      };

      socket.onmessage = ({ data }) => {
        try {
          const msg = JSON.parse(data);
          if (msg.type === 'cost_update' && typeof msg.total_cost === 'number') {
            currentCost.value = msg.total_cost;
          }
        } catch (e) {
          console.warn('CostProgress: invalid message', data);
        }
      };

      // エラー時のハンドリング: デフォルトログを抑制し、必要に応じACTIONを追加可能
      socket.onerror = (err) => {
        // silent or custom handling
      };

      socket.onclose = (event) => {
        console.warn('CostProgress WS closed', event);
      };
    });

    onBeforeUnmount(() => {
      if (socket) {
        socket.close();
        socket = null;
      }
    });

    return {
      currentCost,
      fillPercentage,
      labelCost,
      labelMaxCost,
    };
  },

  template: `
    <div class="cost-progress">
      <div
        role="progressbar"
        class="progress"
        :aria-valuemin="0"
        :aria-valuemax="maxCost"
        :aria-valuenow="currentCost"
      >
        <div
          class="progress-bar"
          :style="{ width: fillPercentage + '%' }"
        ></div>
      </div>
      <div class="mt-2 text-center">
        累積コスト: {{ labelCost }} / {{ labelMaxCost }}
      </div>
    </div>
  `,
});

// --- マウント処理 ---
// HTML に <div id="cost-progress-app" data-workflow-id="..." data-max-cost="..."></div> がある想定

document.addEventListener('DOMContentLoaded', () => {
  const mountEl = document.getElementById('cost-progress-app');
  if (!mountEl) {
    console.warn('CostProgressApp: mount element "#cost-progress-app" not found.');
    return;
  }

  // 1) data-* 属性からワークフローID／最大コストを取得
  const dataWid = mountEl.dataset.workflowId;
  const dataMc  = mountEl.dataset.maxCost;

  // 2) data-* が不正なら window グローバル変数をフォールバック
  let workflowId = Number(dataWid);
  let maxCost    = Number(dataMc);
  if (!Number.isFinite(workflowId)) {
    workflowId = Number(window.__CURRENT_WORKFLOW_ID__);
  }
  if (!Number.isFinite(maxCost)) {
    maxCost = Number(window.__CURRENT_MAX_COST__);
  }

  // 3) マウント前チェック: 無効値 or 0 以下はスキップ
  if (
    !Number.isFinite(workflowId) || workflowId <= 0 ||
    !Number.isFinite(maxCost)    || maxCost    <= 0
  ) {
    console.warn(
      'CostProgressApp: invalid workflowId or maxCost, skipping mount',
      { workflowId, maxCost }
    );
    return;
  }

  // 4) 数値チェック合格後、Vue アプリ起動
  createApp(CostProgress, { workflowId, maxCost }).mount(mountEl);
});