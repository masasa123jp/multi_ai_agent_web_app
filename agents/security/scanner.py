# agents/security/scanner.py

"""
agents.security_agent.scanner
────────────────────────────────────────────────────────────────────────────
高度拡張版 静的解析ユーティリティ。
- AST/regex による危険パターン検出
- Bandit, Radon, pip-audit 連携
- JSON と Markdown 両対応でレポート出力
- ユーザ設定ファイルでルールの ON/OFF 切り替え可能
"""

import ast
import json
import re
import subprocess
import tempfile
import toml
from radon.complexity import cc_visit
from typing import Any, Dict, List, Tuple

# -----------------------------------------------------------------------------
# 設定読み込み
# -----------------------------------------------------------------------------
DEFAULT_CONFIG = {
    "enable_ast_checks": True,
    "enable_regex_checks": True,
    "enable_bandit": True,
    "enable_complexity": True,
    "complexity_threshold": 10,
    "enable_dependency_audit": True,
    "enable_hardcoded_urls": True,
}

def load_config(path: str = "scanner_config.toml") -> Dict[str, Any]:
    try:
        cfg = toml.load(path)
        return {**DEFAULT_CONFIG, **cfg.get("scanner", {})}
    except FileNotFoundError:
        return DEFAULT_CONFIG

config = load_config()

# -----------------------------------------------------------------------------
# パターン定義
# -----------------------------------------------------------------------------
_AST_DANGEROUS_CALLS = [
    ("eval", "インジェクションリスク: eval の使用 (CWE-95)"),
    ("exec", "インジェクションリスク: exec の使用 (CWE-95)"),
    ("os.system", "コマンドインジェクション: os.system の使用 (CWE-78)"),
    ("subprocess", "コマンドインジェクション: subprocess の使用"),
    ("yaml.load", "デシリアライズ攻撃: yaml.load (safe_load推奨)"),
]

_REGEX_PATTERNS = [
    (re.compile(r"https?://", re.IGNORECASE),    "HTTP 通信: URL が HTTP/HTTPS で開始"),
    (re.compile(r"verify\s*=\s*False"),         "TLS 検証回避: verify=False が検出"),
    (re.compile(r"(AKIA|ASIA)[A-Z0-9]{16}"),     "AWSキー形式がハードコード"),
    (re.compile(r"(?:api_key|password|secret)\s*=\s*['\"].+['\"]", re.IGNORECASE),
                                               "ハードコードされたシークレット"),
    (re.compile(r"['\"].*;\s*(SELECT|INSERT|UPDATE|DELETE)\b", re.IGNORECASE),
                                               "SQL インジェクション疑い"),
    (re.compile(r"cors_allowed_origins\s*=\s*\[.*\*.*\]"), 
                                               "CORS 設定: ワイルドカード許可"),
]

# -----------------------------------------------------------------------------
# 各種スキャナ／ツール呼び出し
# -----------------------------------------------------------------------------
def run_bandit(source: str) -> str:
    """Bandit CLI を呼び出し"""
    if not config["enable_bandit"]:
        return "Bandit スキャン: 無効"
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tmp:
        tmp.write(source)
        tmp_path = tmp.name
    res = subprocess.run(
        ["bandit", "-q", "-r", tmp_path],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=30
    )
    return res.stdout.strip() or "Bandit: 問題なし"

def run_radon(source: str) -> List[Tuple[str,int,int]]:
    """radon Cyclomatic Complexity 分析"""
    if not config["enable_complexity"]:
        return []
    results = []
    try:
        for block in cc_visit(source):
            if block.complexity > config["complexity_threshold"]:
                results.append((block.name, block.lineno, block.complexity))
    except Exception:
        pass
    return results

def run_dependency_audit() -> str:
    """pip-audit を呼び出し、依存性脆弱性をチェック"""
    if not config["enable_dependency_audit"]:
        return "Dependency Audit: 無効"
    # pip-audit 呼び出し
    pip_res = subprocess.run(
        ["pip-audit", "--format", "json"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, timeout=60
    )
    return pip_res.stdout.strip() or "pip-audit: 問題なし"

# -----------------------------------------------------------------------------
# メインスキャン関数
# -----------------------------------------------------------------------------
def run_static_scans(source: str, output_json: bool = False) -> Any:
    """
    拡張静的解析を実行し、JSON か Markdown で要約結果を返す。
    """
    findings: List[Dict[str,Any]] = []

    # AST チェック
    if config["enable_ast_checks"]:
        try:
            tree = ast.parse(source)
            class Visitor(ast.NodeVisitor):
                def visit_Call(self, node):
                    name = getattr(node.func, 'id', None) or getattr(node.func, 'attr', None)
                    for rule, desc in _AST_DANGEROUS_CALLS:
                        if rule in (name or ""):
                            findings.append({"type":"AST","rule":rule,"desc":desc,"line":node.lineno})
                    self.generic_visit(node)
            Visitor().visit(tree)
        except SyntaxError as e:
            findings.append({"type":"SyntaxError","desc":str(e),"line":e.lineno or 0})

    # Regex チェック
    if config["enable_regex_checks"]:
        for lineno, line in enumerate(source.splitlines(),1):
            for patt, desc in _REGEX_PATTERNS:
                if patt.search(line):
                    findings.append({"type":"Regex","desc":desc,"line":lineno})

    # Radon 複雑度
    radon_issues = run_radon(source)
    for name, lineno, comp in radon_issues:
        findings.append({"type":"Complexity","desc":f"{name} complexity={comp}","line":lineno})

    # Bandit スキャン
    bandit_output = run_bandit(source)

    # 依存性スキャン
    dep_output = run_dependency_audit()

    # レポート整形
    if output_json:
        return {
            "findings": findings,
            "bandit": bandit_output,
            "dependencies": json.loads(dep_output) if dep_output.startswith("[") else dep_output
        }

    # Markdown レポート
    lines: List[str] = []
    if findings:
        lines.append("## 検出結果")
        for f in findings:
            lines.append(f"- [{f['type']}] (行{f['line']}) {f['desc']}")
        lines.append("")
    else:
        lines.append("## 検出結果: 問題なし")

    lines.append("## Bandit スキャン結果")
    lines.append(f"```text\n{bandit_output}\n```")
    lines.append("")
    lines.append("## Dependency Audit 結果")
    if isinstance(dep_output, str):
        lines.append(f"```text\n{dep_output}\n```")
    else:
        lines.append("```json")
        lines.append(json.dumps(dep_output, ensure_ascii=False, indent=2))
        lines.append("```")

    report = "\n".join(lines)
    return report
