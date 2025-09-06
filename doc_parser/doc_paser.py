from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import json
import os
import sys
import argparse
from typing import Dict, List, Any, Union, TypedDict
from langgraph.graph import StateGraph, END

# ===== 定数定義 =====
class Config:
    """設定定数クラス"""
    # ファイルパス
    DEFAULT_API_DOC_PATH = "data/src/api 1.txt"
    DEFAULT_API_ARG_PATH = "data/src/api_arg 1.txt"
    DEFAULT_OUTPUT_PATH = "doc_paser/parsed_api_result.json"
    DEFAULT_ENCODING = "utf-8"
    
    # モデル設定
    MODEL_CONFIG = {
        "model": "gpt-5-mini",  # "gpt-5-nano", "gpt-5-mini", "gpt-5"
        "output_version": "responses/v1",
        "reasoning_effort": "high",  # "minimal", 'low', 'medium', 'high'
        "verbosity": "high"  # 'low', 'medium', 'high'
    }
    
    # 自己修正設定
    DEFAULT_MAX_CORRECTIONS = 3
    DEFAULT_QUALITY_THRESHOLD = 90.0
    QUALITY_PENALTY_PER_ISSUE = 20

# ===== 状態定義 =====
class SelfCorrectionState(TypedDict):
    """自己修正エージェントの状態"""
    messages: List[Dict[str, Any]]
    current_code: str
    errors: List[Dict[str, Any]]
    corrections_made: int
    max_corrections: int
    correction_history: List[Dict[str, Any]]
    quality_score: float

# ===== 初期化 =====
load_dotenv()

# ===== ユーティリティ関数 =====
def safe_file_operation(operation, *args, **kwargs):
    """ファイル操作の安全な実行"""
    try:
        return operation(*args, **kwargs)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"ファイルが見つかりません: {e}")
    except UnicodeDecodeError as e:
        raise UnicodeDecodeError(f"ファイルのエンコーディングが不正です: {e}")
    except PermissionError as e:
        raise PermissionError(f"ファイルへのアクセス権限がありません: {e}")
    except IOError as e:
        raise IOError(f"ファイル操作エラー: {e}")

def read_file_safely(file_path: str, encoding: str = Config.DEFAULT_ENCODING) -> str:
    """ファイルを安全に読み込む"""
    def read_operation():
        with open(file_path, "r", encoding=encoding) as file:
            return file.read()
    
    return safe_file_operation(read_operation)

def write_file_safely(file_path: str, content: str, encoding: str = Config.DEFAULT_ENCODING) -> None:
    """ファイルを安全に書き込む"""
    def write_operation():
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding=encoding) as file:
            file.write(content)
    
    safe_file_operation(write_operation)

# ===== ファイル操作関数 =====
def load_api_document(api_doc_path: str = None, api_arg_path: str = None) -> str:
    """APIドキュメントと引数情報を連結して読み込む"""
    api_doc_path = api_doc_path or Config.DEFAULT_API_DOC_PATH
    api_arg_path = api_arg_path or Config.DEFAULT_API_ARG_PATH
    
    try:
        api_doc_content = read_file_safely(api_doc_path)
        api_arg_content = read_file_safely(api_arg_path)
        
        return f"""
# APIドキュメント

{api_doc_content}

---

# 引数の型と書式

{api_arg_content}
"""
    except Exception as e:
        print(f"ドキュメントの読み込みに失敗しました: {e}")
        raise

def save_parsed_result(parsed_result: Union[Dict, List], output_file_path: str = None) -> None:
    """解析結果をJSONファイルとして保存"""
    output_file_path = output_file_path or Config.DEFAULT_OUTPUT_PATH
    
    try:
        json_content = json.dumps(parsed_result, ensure_ascii=False, indent=2)
        write_file_safely(output_file_path, json_content)
        print(f"解析結果を保存しました: {output_file_path}")
    except Exception as e:
        print(f"解析結果の保存に失敗しました: {e}")
        raise

# ===== プロンプト管理 =====
class PromptManager:
    """プロンプトの管理クラス"""
    
    @staticmethod
    def get_system_prompt() -> str:
        """システムプロンプトを取得"""
        return """
<prompt>
    <developer>
        <specialty>EVO.SHIP APIドキュメントの正確な解析</specialty>
        <role>
            あなたは「EVO.SHIP API」ドキュメントの解析に特化した、非常に優秀なソフトウェアエンジニアです。提供されたAPIドキュメントを厳密に解析し、指定されたJSON形式の単一オブジェクトとして出力します。
        </role>
        <workflow>
            <step>これから行うべきサブタスクの簡潔なチェックリスト（3〜7項目）を提示する。</step>
            <step>提供されたAPIドキュメントを厳密に解析する。</step>
            <step>解析結果を指定されたJSON形式の単一オブジェクトで出力する。</step>
            <note>チェックリストは最終出力JSONのトップレベルフィールド <code>checklist</code> として含めること。</note>
        </workflow>
        <guidelines>
            <general>
                <item>出力は有効なJSONオブジェクトのみとし、Markdownやその他のテキストは一切含めないこと。</item>
                <item>ドキュメントに明記されていない情報の推測や補完は行わないこと。</item>
                <item>解析対象は「APIドキュメント」セクションと「引数の型と書式」セクションから構成される。</item>
            </general>
            <analysis_points>
                <type_definitions>
                    <item>「引数の型と書式」セクションから<strong>すべての</strong>データ型を漏れなく抽出する。</item>
                    <item>基本データ型（文字列、浮動小数点、整数、bool）も含める。</item>
                    <item>特殊文字列型（長さ、角度、数値、範囲、点、方向、平面、変数単位、要素グループ、注記スタイル、材料、スイープ方向、厚み付けタイプ、モールド位置、オペレーションタイプ、関連設定、形状タイプ、形状パラメータ、要素）も含める。</item>
                    <item>各型は name と description を格納し、descriptionには型の詳細な仕様と書式を含める。</item>
                    <item>例や書式の説明も description に含める。</item>
                </type_definitions>
                <api_entries>
                    <item>「APIドキュメント」を解析し、関数や独立オブジェクト定義を抽出する。</item>
                    <kinds>
                        <function>entry_type = "function"</function>
                        <object_definition>entry_type = "object_definition"</object_definition>
                    </kinds>
                    <fields>
                        <item>name / description / category</item>
                        <item>params: name, position(0始まり), type, description, is_required, default_value</item>
                        <item>properties: name, type, description</item>
                        <item>returns: type, description, is_array（戻り値が無い場合 type は "void"）</item>
                        <item>is_required は説明に「空文字不可」「必須」があれば true、明記が無ければ false</item>
                        <item>implementation_status は「未実装、使用しない」なら 'unimplemented'、それ以外は 'implemented'</item>
                    </fields>
                </api_entries>
            </analysis_points>
        </guidelines>
        <format>{json_format}</format>
    </developer>
</prompt>
"""

    @staticmethod
    def get_user_prompt() -> str:
        """ユーザープロンプトを取得"""
        return """
以下のドキュメントを上記方針に従って解析し、単一のJSONオブジェクトのみを出力してください。

# 重要: データ型の抽出について
- 「引数の型と書式」セクションから<strong>すべての</strong>データ型を漏れなく抽出してください
- 基本データ型（文字列、浮動小数点、整数、bool）も含めてください
- 特殊文字列型（長さ、角度、数値、範囲、点、方向、平面、変数単位、要素グループ、注記スタイル、材料、スイープ方向、厚み付けタイプ、モールド位置、オペレーションタイプ、関連設定、形状タイプ、形状パラメータ、要素）も含めてください
- 各データ型の詳細な仕様、書式、例も description に含めてください

# 解析対象ドキュメント
---
{document}
---
"""

    @staticmethod
    def get_json_format() -> str:
        """JSONフォーマット例を取得"""
        return """
{
  "type_definitions": [
    {
      "name": "文字列",
      "description": "通常の文字列"
    },
    {
      "name": "浮動小数点",
      "description": "通常の数値"
    },
    {
      "name": "整数",
      "description": "通常の数値"
    },
    {
      "name": "bool",
      "description": "通常の真偽値 True False"
    },
    {
      "name": "長さ",
      "description": "mm単位の数値、変数要素名、式文字列。例: \"100.0\", \"L1\", \"L1 / 2.0\""
    },
    {
      "name": "角度",
      "description": "度(°)単位の数値、変数要素名、式文字列。例: \"30.0\", \"Angle1\", \"Angle1 * 0.2\""
    },
    {
      "name": "点",
      "description": "コンマで区切って各コンポーネントをX,Y,Z（3Dの場合）を長さ（変数も可）で指定。例: \"100.0,50,0,0.0\""
    },
    {
      "name": "平面",
      "description": "コンマで区切られた文字列で指定。最初のカラムは必ず \"PL\"。例: \"PL,Z\" グローバルXY平面"
    }
  ],
  "api_entries": [
    {
      "entry_type": "'function' or 'object_definition'",
      "name": "string (function or object name)",
      "description": "string",
      "category": "string",
      "params": [
        {
          "name": "string",
          "position": "number (0-based index of the parameter)",
          "type": "string (normalized type name)",
          "description": "string",
          "is_required": "boolean",
          "default_value": "string | null"
        }
      ],
      "properties": [
        {
          "name": "string",
          "type": "string (normalized type name)",
          "description": "string"
        }
      ],
      "returns": {
        "type": "string (normalized type name)",
        "description": "string",
        "is_array": "boolean"
      },
      "notes": "string | null",
      "implementation_status": "string ('implemented', 'unimplemented', or 'deprecated')"
    }
  ]
}
"""

# ===== データ処理関数 =====
class DataProcessor:
    """データ処理クラス"""
    
    @staticmethod
    def normalize_type_name(type_name: str) -> str:
        """型名を正規化"""
        if not isinstance(type_name, str):
            return type_name
        
        name = type_name.strip()
        mapping = {
            "string": "文字列", "str": "文字列",
            "float": "浮動小数点", "double": "浮動小数点", "number": "浮動小数点",
            "int": "整数", "integer": "整数",
            "boolean": "bool", "bool": "bool",
            "length": "長さ", "angle": "角度",
            "direction": "方向", "direction2d": "方向(2D)",
            "plane": "平面", "point": "点", "point2d": "点(2D)",
            "element": "要素", "elementid": "要素ID",
            "element group": "要素グループ", "material": "材料",
            "style": "注記スタイル", "bstr": "BSTR",
            "配列": "配列", "浮動小数点(配列)": "浮動小数点(配列)"
        }
        
        key = name.lower().replace(" ", "")
        return mapping.get(key, name)
    
    @staticmethod
    def enrich_array_object_info(param: Dict[str, Any]) -> None:
        """配列オブジェクト情報を充実させる"""
        t = param.get("type_name")
        if not isinstance(t, str):
            return
        
        is_array = "(配列)" in t or t.endswith("配列") or t.endswith("(array)")
        if is_array:
            base = t.replace("(配列)", "").replace("配列", "").strip("：: ")
            element_type = base if base and base != "要素" else None
            param["array_info"] = {
                "is_array": True,
                "element_type": element_type,
                "min_length": None,
                "max_length": None,
            }
        else:
            param["array_info"] = None
    
    @staticmethod
    def infer_is_required(param: Dict[str, Any]) -> None:
        """必須性を推論"""
        cons = param.get("constraints") or []
        desc = param.get("description_raw") or ""
        text = " ".join(cons) + " " + desc
        
        required = ("空文字不可" in text) or ("必須" in text)
        if "空文字可" in text:
            required = False
        
        param["is_required"] = bool(required)
    
    @staticmethod
    def postprocess_parsed_result(parsed_result: Union[Dict, List]) -> Union[Dict, List]:
        """解析結果の後処理を実行"""
        if not isinstance(parsed_result, list):
            return parsed_result
        
        for fn in parsed_result:
            # 戻り値の正規化
            if isinstance(fn.get("returns"), dict):
                r_t = fn["returns"].get("type_name")
                if r_t is not None:
                    fn["returns"]["type_name"] = DataProcessor.normalize_type_name(r_t)
            
            # パラメータの処理
            params = fn.get("params") or []
            for idx, p in enumerate(params):
                t = p.get("type_name")
                if t is not None:
                    p["type_name"] = DataProcessor.normalize_type_name(t)
                DataProcessor.enrich_array_object_info(p)
                DataProcessor.infer_is_required(p)
                p["position"] = idx
            fn["params"] = params
        
        return parsed_result

# ===== LLM処理関数 =====
class LLMProcessor:
    """LLM処理クラス"""
    
    @staticmethod
    def create_llm() -> ChatOpenAI:
        """LLMインスタンスを作成"""
        return ChatOpenAI(**Config.MODEL_CONFIG).bind(
            response_format={"type": "json_object"}
        )
    
    @staticmethod
    def parse_response(response: Any) -> Union[Dict, List]:
        """LLMの応答をパース"""
        print(f"Response type: {type(response.content)}")
        print(f"Response content preview: {str(response.content)[:200]}...")
        
        try:
            if isinstance(response.content, str):
                parsed_result = json.loads(response.content)
            elif isinstance(response.content, (dict, list)):
                parsed_result = response.content
            else:
                parsed_result = json.loads(str(response.content))
            print("✅ パース成功")
            return parsed_result
        except json.JSONDecodeError as e:
            print(f"❌ JSONパースエラー: {e}")
            print("LLM出力:", response.content)
            if isinstance(response.content, (dict, list)):
                return response.content
            raise
        except Exception as e:
            print(f"❌ 予期しないエラー: {e}")
            print("LLM出力:", response.content)
            raise
    
    @staticmethod
    def extract_from_responses_api(parsed_result: Union[Dict, List]) -> Union[Dict, List]:
        """Responses API v1形式から実際のコンテンツを抽出"""
        if not isinstance(parsed_result, list) or len(parsed_result) == 0:
            return parsed_result
        
        print("🔍 Responses API v1形式を検出、テキスト要素を抽出中...")
        
        # テキスト要素を探す
        text_element = next(
            (item for item in parsed_result 
             if isinstance(item, dict) and item.get("type") == "text"), 
            None
        )
        
        if text_element and "text" in text_element:
            try:
                actual_content = json.loads(text_element["text"])
                print("✅ Responses API v1形式から正しく抽出")
                return actual_content
            except json.JSONDecodeError as e:
                print(f"❌ textフィールド内のJSONパースエラー: {e}")
                print("text内容:", text_element["text"][:200])
                return parsed_result
        else:
            print("⚠️ テキスト要素が見つかりませんでした")
            return parsed_result

# ===== 自己修正機能 =====
class CodeQualityAnalyzer:
    """コード品質分析クラス"""
    
    @staticmethod
    def analyze_code_quality(state: SelfCorrectionState, args: argparse.Namespace) -> SelfCorrectionState:
        """コードの品質を分析"""
        print("🔍 コード品質の分析中...")
        
        quality_issues = []
        
        # 品質チェック項目
        checks = [
            ("def " in state["current_code"] and "->" not in state["current_code"],
             "missing_type_hints", "medium", "関数に型ヒントが不足しています"),
            ('"""' not in state["current_code"] and "'''" not in state["current_code"],
             "missing_docstrings", "low", "関数にドキュメント文字列が不足しています"),
            ("try:" in state["current_code"] and "except" not in state["current_code"],
             "incomplete_error_handling", "high", "try文に対応するexcept句が不足しています"),
            ("import " in state["current_code"] and "from typing import" not in state["current_code"],
             "missing_type_imports", "medium", "typingモジュールからのインポートが不足しています")
        ]
        
        for condition, issue_type, severity, description in checks:
            if condition:
                quality_issues.append({
                    "type": issue_type,
                    "severity": severity,
                    "description": description
                })
        
        state["errors"] = quality_issues
        state["quality_score"] = max(0, 100 - len(quality_issues) * Config.QUALITY_PENALTY_PER_ISSUE)
        
        print(f"品質スコア: {state['quality_score']}/100")
        print(f"検出された問題: {len(quality_issues)}件")
        
        if args.verbose:
            for i, issue in enumerate(quality_issues, 1):
                print(f"  {i}. [{issue['severity'].upper()}] {issue['description']}")
        
        return state

class CodeCorrector:
    """コード修正クラス"""
    
    @staticmethod
    def generate_corrections(state: SelfCorrectionState, args: argparse.Namespace) -> SelfCorrectionState:
        """検出された問題に対する修正を生成"""
        if not state["errors"]:
            print("✅ 修正が必要な問題はありません")
            return state
        
        if args.dry_run:
            print("🔍 ドライランモード: 修正は生成されません")
            return state
        
        print("🔧 修正の生成中...")
        
        # LLMを使用して修正を生成
        llm = LLMProcessor.create_llm()
        correction_prompt = ChatPromptTemplate.from_messages([
            ("system", "あなたは優秀なPython開発者です。コードの問題を修正してください。"),
            ("user", f"""
以下のPythonコードの問題を修正してください：

問題:
{json.dumps(state['errors'], ensure_ascii=False, indent=2)}

コード:
```python
{state['current_code']}
```

修正されたコードのみを出力してください。
""")
        ])
        
        chain = correction_prompt | llm
        response = chain.invoke({})
        
        # 修正されたコードを抽出
        corrected_code = response.content
        if isinstance(corrected_code, str):
            if "```python" in corrected_code:
                corrected_code = corrected_code.split("```python")[1].split("```")[0].strip()
            elif "```" in corrected_code:
                corrected_code = corrected_code.split("```")[1].split("```")[0].strip()
        
        state["correction_history"].append({
            "iteration": state["corrections_made"] + 1,
            "errors": state["errors"],
            "corrected_code": corrected_code
        })
        
        print(f"修正版 {state['corrections_made'] + 1} を生成しました")
        return state
    
    @staticmethod
    def apply_corrections(state: SelfCorrectionState, args: argparse.Namespace) -> SelfCorrectionState:
        """修正を適用"""
        if not state["correction_history"]:
            return state
        
        if args.dry_run:
            print("🔍 ドライランモード: 修正は適用されません")
            return state
        
        print("📝 修正を適用中...")
        
        latest_correction = state["correction_history"][-1]
        state["current_code"] = latest_correction["corrected_code"]
        state["corrections_made"] += 1
        
        print(f"修正 {state['corrections_made']} を適用しました")
        return state

class SelfCorrectionAgent:
    """自己修正エージェントクラス"""
    
    @staticmethod
    def should_continue_correcting(state: SelfCorrectionState, args: argparse.Namespace) -> str:
        """修正を続行するかどうかを判断"""
        if state["corrections_made"] >= state["max_corrections"]:
            print(f"⚠️ 最大修正回数 {state['max_corrections']} に達しました")
            return "end"
        
        if state["quality_score"] >= args.quality_threshold:
            print(f"✅ 品質スコアが{args.quality_threshold}以上に達しました")
            return "end"
        
        if not state["errors"]:
            print("✅ エラーが解決されました")
            return "end"
        
        return "continue"
    
    @staticmethod
    def create_workflow(args: argparse.Namespace) -> StateGraph:
        """自己修正ワークフローを作成"""
        workflow = StateGraph(SelfCorrectionState)
        
        # ノードの追加
        workflow.add_node("analyze_quality", lambda state: CodeQualityAnalyzer.analyze_code_quality(state, args))
        workflow.add_node("generate_corrections", lambda state: CodeCorrector.generate_corrections(state, args))
        workflow.add_node("apply_corrections", lambda state: CodeCorrector.apply_corrections(state, args))
        
        # エントリーポイントの設定（STARTから最初のノードへ）
        workflow.set_entry_point("analyze_quality")
        
        # エッジの定義
        workflow.add_edge("analyze_quality", "generate_corrections")
        workflow.add_edge("generate_corrections", "apply_corrections")
        
        # 条件分岐
        workflow.add_conditional_edges(
            "apply_corrections",
            lambda state: SelfCorrectionAgent.should_continue_correcting(state, args),
            {
                "continue": "analyze_quality",
                "end": END
            }
        )
        
        return workflow.compile()
    
    @staticmethod
    def execute(code: str, args: argparse.Namespace) -> Dict[str, Any]:
        """自己修正を実行"""
        print("🤖 自己修正エージェントを開始します...")
        print(f"設定: 最大修正回数={args.max_corrections}, 品質閾値={args.quality_threshold}")
        
        # 初期状態の設定
        initial_state = SelfCorrectionState(
            messages=[],
            current_code=code,
            errors=[],
            corrections_made=0,
            max_corrections=args.max_corrections,
            correction_history=[],
            quality_score=0.0
        )
        
        # 自己修正エージェントの実行
        agent = SelfCorrectionAgent.create_workflow(args)
        final_state = agent.invoke(initial_state)
        
        print(f"🎯 自己修正完了！最終品質スコア: {final_state['quality_score']}/100")
        print(f"📊 実行された修正回数: {final_state['corrections_made']}")
        
        # 修正履歴の保存
        if args.save_corrections and final_state["correction_history"]:
            correction_file = f"correction_history_{os.path.basename(__file__)}.json"
            with open(correction_file, 'w', encoding='utf-8') as f:
                json.dump(final_state["correction_history"], f, ensure_ascii=False, indent=2)
            print(f"修正履歴を保存しました: {correction_file}")
        
        return {
            "corrected_code": final_state["current_code"],
            "final_quality_score": final_state["quality_score"],
            "corrections_made": final_state["corrections_made"],
            "correction_history": final_state["correction_history"]
        }

# ===== メイン処理関数 =====
def analyze_api_document(args: argparse.Namespace) -> Dict[str, Any]:
    """APIドキュメントの解析を実行"""
    print("🤖 LLMを使ってAPIドキュメントを解析しています...")
    
    # ドキュメントとプロンプトの読み込み
    api_document_text = load_api_document(args.api_doc, args.api_arg)
    system_prompt_template = PromptManager.get_system_prompt()
    user_prompt_template = PromptManager.get_user_prompt()
    json_format_instructions = PromptManager.get_json_format()
    
    # LLMの作成と実行
    llm = LLMProcessor.create_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt_template),
        ("user", user_prompt_template),
    ])
    
    chain = prompt | llm
    response = chain.invoke({
        "document": api_document_text,
        "json_format": json_format_instructions,
    })
    
    # 応答のパース
    parsed_result = LLMProcessor.parse_response(response)
    
    # Responses API v1形式の処理
    if isinstance(parsed_result, dict):
        print("✅ 単一のJSONオブジェクトとして正しくパースされました")
    else:
        parsed_result = LLMProcessor.extract_from_responses_api(parsed_result)
    
    # 後処理の実行
    print("\n🔄 解析結果の後処理を実行中...")
    processed_result = DataProcessor.postprocess_parsed_result(parsed_result)
    
    return processed_result

def main():
    """メイン関数"""
    try:
        # コマンドライン引数の解析
        args = parse_arguments()
        
        if args.verbose:
            print("🔧 詳細モードで実行中...")
            print(f"APIドキュメント: {args.api_doc}")
            print(f"API引数: {args.api_arg}")
            print(f"出力ファイル: {args.output}")
            print(f"自己修正: {'有効' if args.self_correct else '無効'}")
            if args.self_correct:
                print(f"最大修正回数: {args.max_corrections}")
                print(f"品質閾値: {args.quality_threshold}")
        
        # APIドキュメントの解析
        processed_result = analyze_api_document(args)
        
        # 結果の表示と保存
        print("\n✅ 解析が完了し、JSONオブジェクトが生成されました。")
        if args.verbose:
            print(json.dumps(processed_result, indent=2, ensure_ascii=False))
        save_parsed_result(processed_result, args.output)
        
        # 自己修正機能の実行（オプション）
        if args.self_correct:
            print("\n🔧 自己修正機能を実行します...")
            
            # 現在のファイルの内容を読み込み
            current_file_path = __file__
            with open(current_file_path, 'r', encoding='utf-8') as f:
                current_code = f.read()
            
            # 自己修正の実行
            corrected_result = SelfCorrectionAgent.execute(current_code, args)
            
            # 修正されたコードの保存
            if corrected_result['corrections_made'] > 0:
                corrected_file_path = current_file_path + '.corrected'
                with open(corrected_file_path, 'w', encoding='utf-8') as f:
                    f.write(corrected_result['corrected_code'])
                print(f"修正されたコードを保存しました: {corrected_file_path}")
                
                if args.verbose:
                    print(f"最終品質スコア: {corrected_result['final_quality_score']}/100")
                    print(f"実行された修正回数: {corrected_result['corrections_made']}")
            else:
                print("✅ 修正は必要ありませんでした")
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        print(f"エラーの種類: {type(e).__name__}")
        if "api_key" in str(e).lower():
            print("\n💡 ヒント: .envファイルに正しいOPENAI_API_KEYが設定されているか確認してください。")

# ===== コマンドライン引数処理 =====
def parse_arguments():
    """コマンドライン引数を解析"""
    parser = argparse.ArgumentParser(
        description="EVO.SHIP APIドキュメント解析ツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 基本的なAPI解析のみ実行
  python doc_paser.py
  
  # 自己修正機能を有効にして実行
  python doc_paser.py --self-correct
  
  # 自己修正の最大回数を指定
  python doc_parser.py --self-correct --max-corrections 5
  
  # 出力ファイルパスを指定
  python doc_paser.py --output output.json
  
  # 入力ファイルパスを指定
  python doc_paser.py --api-doc custom_api.txt --api-arg custom_arg.txt
  
  # 詳細モードで実行
  python doc_paser.py --verbose
        """
    )
    
    # 基本オプション
    parser.add_argument(
        "--api-doc",
        default=Config.DEFAULT_API_DOC_PATH,
        help=f"APIドキュメントファイルのパス (デフォルト: {Config.DEFAULT_API_DOC_PATH})"
    )
    
    parser.add_argument(
        "--api-arg",
        default=Config.DEFAULT_API_ARG_PATH,
        help=f"API引数ファイルのパス (デフォルト: {Config.DEFAULT_API_ARG_PATH})"
    )
    
    parser.add_argument(
        "--output",
        default=Config.DEFAULT_OUTPUT_PATH,
        help=f"出力ファイルのパス (デフォルト: {Config.DEFAULT_OUTPUT_PATH})"
    )
    
    # 自己修正オプション
    parser.add_argument(
        "--self-correct",
        action="store_true",
        help="自己修正機能を有効にする"
    )
    
    parser.add_argument(
        "--max-corrections",
        type=int,
        default=Config.DEFAULT_MAX_CORRECTIONS,
        help=f"自己修正の最大回数 (デフォルト: {Config.DEFAULT_MAX_CORRECTIONS})"
    )
    
    parser.add_argument(
        "--quality-threshold",
        type=float,
        default=Config.DEFAULT_QUALITY_THRESHOLD,
        help=f"自己修正を終了する品質スコアの閾値 (デフォルト: {Config.DEFAULT_QUALITY_THRESHOLD})"
    )
    
    # その他のオプション
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="詳細なログを出力する"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="実際の修正は行わず、検出された問題のみを表示する"
    )
    
    parser.add_argument(
        "--save-corrections",
        action="store_true",
        help="修正履歴をファイルに保存する"
    )
    
    return parser.parse_args()

if __name__ == "__main__":
    # プロジェクトルートの設定
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    print(f"プロジェクトルートパス: {project_root}")
    print(f"Pythonパスに追加されました: {project_root in sys.path}")
    
    main()
