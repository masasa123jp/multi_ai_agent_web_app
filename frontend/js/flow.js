/* frontend/js/flow.js
   ─────────────────────────────────────────
   Mermaid フロー図描画 & ノードハイライト
   • アンカー要素と、そのダミーエッジを非表示化
*/

const FLOW_DEF = `
flowchart LR

  %% Input and Output
  In(["画面入力"]):::defaultNode
  Out(["ソフトウェア<br/>(ZIP)"]):::defaultNode

  %% Stakeholders (Top-Left)
  subgraph Stakeholders["ステークホルダー"]
    direction TB
    U["Biz<br/>(要件詳細化)"]
    ITC["ITコンサル<br/>(要件調整)"]
    PM["PM<br/>(進捗管理)"]
    U --> ITC --> PM
    U --> PM
  end

  %% Agents (Bottom-Right)
  subgraph Agents["エージェント"]
    direction TB
    DBD["DB Design<br/>(スキーマ設計)"]:::agent
    UI["UI Gen<br/>(画面設計)"]:::agent
    CODE["Code Gen<br/>(コード生成)"]:::agent
    QA["QA<br/>(テスト実行)"]:::agent
    SEC["Security<br/>(脆弱性検査)"]:::agent
    PATCH["Patch<br/>(更新適用)"]:::agent
    DBD --> CODE
    UI --> CODE
    CODE --> QA --> SEC --> PATCH
  end

  %% Workflow
  In --> U
  PM --> DBD
  PM --> UI
  PATCH --> U
  Agents --> Out

  %% Style definitions
  classDef stakeholder fill:#ffe0b2,stroke:#fb8c00,stroke-width:1px,padding:20px,text-align:center;
  classDef agent fill:#e3f2fd,stroke:#2196f3,stroke-width:1px,padding:20px,text-align:center;
  classDef defaultNode fill:#f9f9f9,stroke:#999,stroke-width:1px,padding:20px,text-align:center;
  classDef invisible fill:none,stroke:none;

  %% Class application
  class U,PM,ITC stakeholder
  class DBD,UI,CODE,QA,SEC,PATCH agent
  class In,Out defaultNode
`;

const AGENT_NODE_MAP = {
  'DB Design'      :'DBD',
  'UI Generation'  :'UI',
  'Code Generation':'CODE',
  'QA'             :'QA',
  'Security'       :'SEC',
  'Patch'          :'PATCH'
};

export const Flow = {
  /**
   * フロー図を描画する
   * @param {HTMLElement} target マウント先要素
   */
  render(target) {
    if (!window.mermaid) return;

    // 1) 描画領域をクリア
    target.innerHTML = '';

    // 2) Mermaid 定義を埋め込む div を生成
    const div = document.createElement('div');
    div.className   = 'mermaid';
    div.textContent = FLOW_DEF;
    target.appendChild(div);

    // 3) Mermaid 初期化 ＆ 描画
    mermaid.initialize({
      startOnLoad: false,
      theme: 'default',
      flowchart: { nodeSpacing: 50, rankSpacing: 50 }
    });
    mermaid.init(undefined, div);

    // 4) 描画完了後にアンカー要素＆ダミーエッジを非表示化
    //    SVG 内の <g id="AnchorTopLeft">, <g id="AnchorBottomRight"> と
    //    それらに接続する <g class="edge" id="edge-..."> を見つけて display:none
    setTimeout(() => {
      const svg = target.querySelector('svg');
      if (!svg) return;

      // 非表示化対象のアンカーIDリスト
      const anchorIds = ['AnchorTopLeft', 'AnchorBottomRight'];

      // 4-1) アンカー要素を非表示
      anchorIds.forEach(aid => {
        const node = svg.querySelector(`g#${aid}`);
        if (node) node.style.display = 'none';
      });

      // 4-2) ダミーエッジを非表示
      svg.querySelectorAll('g.edge').forEach(edgeG => {
        const eid = edgeG.id || '';
        // Mermaid のエッジIDは "edge-<from>-<to>" 形式なので、
        // 名前にアンカーIDが含まれるものを消す
        if (anchorIds.some(aid => eid.includes(aid))) {
          edgeG.style.display = 'none';
        }
      });
    }, 0);
  },

  /**
   * 実行中のエージェントノードをハイライト
   * @param {string} agent 実行中エージェント名
   */
  highlight(agent) {
    const id = AGENT_NODE_MAP[agent];
    if (!id) return;
    const svg = document.querySelector('#flow-diagram-body svg');
    if (!svg) return;
    // 以前のハイライトを外す
    if (window._prevAgentNode) {
      window._prevAgentNode.classList.remove('activeAgent');
    }
    // 新たに対象ノードを取得してハイライト
    const node = svg.querySelector(`#${id}`);
    if (node) {
      node.classList.add('activeAgent');
      window._prevAgentNode = node;
    }
  }
};
