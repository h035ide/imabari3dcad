from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import json
import os
import sys
from typing import Dict, List, Any, Union

# 定数定義
DEFAULT_API_DOC_PATH = "data/src/api 1.txt"
DEFAULT_API_ARG_PATH = "data/src/api_arg 1.txt"
DEFAULT_OUTPUT_PATH = "doc_paser/parsed_api_result.json"
DEFAULT_ENCODING = "utf-8"

# モデル設定
MODEL_CONFIG = {
    "model": "gpt-5-mini",#"gpt-5-nano","gpt-5-mini","gpt-5"
    "output_version": "responses/v1",
    "reasoning_effort": "high", # "minimal", 'low', 'medium', 'high' から選択
    "verbosity": "high" # 'low', 'medium', 'high' から選択
}

load_dotenv()

def read_file_safely(file_path: str, encoding: str = DEFAULT_ENCODING) -> str:
    """ファイルを安全に読み込む関数"""
    try:
        with open(file_path, "r", encoding=encoding) as file:
            return file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")
    except UnicodeDecodeError:
        raise UnicodeDecodeError(f"ファイルのエンコーディングが不正です: {file_path}")
    except IOError as e:
        raise IOError(f"ファイル読み込みエラー: {file_path} - {str(e)}")

def load_api_document(
    api_doc_path: str = DEFAULT_API_DOC_PATH,
    api_arg_path: str = DEFAULT_API_ARG_PATH
) -> str:
    """APIドキュメントと引数情報を連結して読み込む関数"""
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
    except (FileNotFoundError, IOError) as e:
        print(f"ドキュメントの読み込みに失敗しました: {e}")
        raise

def get_default_system_prompt() -> str:
    """デフォルトのシステムプロンプトを取得"""
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

def get_default_user_prompt() -> str:
    """デフォルトのユーザープロンプトを取得"""
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

def get_default_json_format() -> str:
    """デフォルトのJSONフォーマット例を取得"""
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

def load_system_prompt(file_path: str = None) -> str:
    """システムプロンプトを読み込む関数"""
    if file_path is None:
        return get_default_system_prompt()
    return read_file_safely(file_path)

def load_user_prompt(file_path: str = None) -> str:
    """ユーザープロンプトを読み込む関数"""
    if file_path is None:
        return get_default_user_prompt()
    return read_file_safely(file_path)

def load_json_format_instructions(file_path: str = None) -> str:
    """JSONフォーマット指示を読み込む関数"""
    if file_path is None:
        return get_default_json_format()
    return read_file_safely(file_path)

def write_file_safely(file_path: str, content: str, encoding: str = DEFAULT_ENCODING) -> None:
    """ファイルを安全に書き込む関数"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding=encoding) as file:
            file.write(content)
    except PermissionError:
        raise PermissionError(f"ファイルへの書き込み権限がありません: {file_path}")
    except IOError as e:
        raise IOError(f"ファイル書き込みエラー: {file_path} - {str(e)}")

def save_parsed_result(parsed_result: Union[Dict, List], output_file_path: str = DEFAULT_OUTPUT_PATH) -> None:
    """解析結果をJSONファイルとして保存する関数"""
    try:
        json_content = json.dumps(parsed_result, ensure_ascii=False, indent=2)
        write_file_safely(output_file_path, json_content)
        print(f"解析結果を保存しました: {output_file_path}")
    except Exception as e:
        print(f"解析結果の保存に失敗しました: {str(e)}")
        raise

def normalize_type_name(type_name: str) -> str:
    """型名を正規化する関数"""
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

def enrich_array_object_info(param: Dict[str, Any]) -> None:
    """配列オブジェクト情報を充実させる関数"""
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

def infer_is_required(param: Dict[str, Any]) -> None:
    """必須性を推論する関数"""
    cons = param.get("constraints") or []
    desc = param.get("description_raw") or ""
    text = " ".join(cons) + " " + desc
    
    required = ("空文字不可" in text) or ("必須" in text)
    if "空文字可" in text:
        required = False
    
    param["is_required"] = bool(required)

def postprocess_parsed_result(parsed_result: Union[Dict, List]) -> Union[Dict, List]:
    """解析結果の後処理を実行する関数"""
    if not isinstance(parsed_result, list):
        return parsed_result
    
    for fn in parsed_result:
        # 戻り値の正規化
        if isinstance(fn.get("returns"), dict):
            r_t = fn["returns"].get("type_name")
            if r_t is not None:
                fn["returns"]["type_name"] = normalize_type_name(r_t)
        
        # パラメータの処理
        params = fn.get("params") or []
        for idx, p in enumerate(params):
            t = p.get("type_name")
            if t is not None:
                p["type_name"] = normalize_type_name(t)
            enrich_array_object_info(p)
            infer_is_required(p)
            p["position"] = idx
        fn["params"] = params
    
    return parsed_result

def create_llm() -> ChatOpenAI:
    """LLMインスタンスを作成する関数"""
    return ChatOpenAI(**MODEL_CONFIG).bind(
        response_format={"type": "json_object"}
    )

def parse_response(response: Any) -> Union[Dict, List]:
    """LLMの応答をパースする関数"""
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

def extract_from_responses_api(parsed_result: Union[Dict, List]) -> Union[Dict, List]:
    """Responses API v1形式から実際のコンテンツを抽出する関数"""
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

def analyze_api_document() -> Dict[str, Any]:
    """APIドキュメントの解析を実行する関数"""
    print("🤖 LLMを使ってAPIドキュメントを解析しています...")
    
    # ドキュメントとプロンプトの読み込み
    api_document_text = load_api_document()
    system_prompt_template = load_system_prompt()
    user_prompt_template = load_user_prompt()
    json_format_instructions = load_json_format_instructions()
    
    # LLMの作成と実行
    llm = create_llm()
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
    parsed_result = parse_response(response)
    
    # Responses API v1形式の処理
    if isinstance(parsed_result, dict):
        print("✅ 単一のJSONオブジェクトとして正しくパースされました")
    else:
        parsed_result = extract_from_responses_api(parsed_result)
    
    # 後処理の実行
    print("\n🔄 解析結果の後処理を実行中...")
    processed_result = postprocess_parsed_result(parsed_result)
    
    return processed_result

def main():
    """メイン関数"""
    try:
        # APIドキュメントの解析
        processed_result = analyze_api_document()
        
        # 結果の表示と保存
        print("\n✅ 解析が完了し、JSONオブジェクトが生成されました。")
        print(json.dumps(processed_result, indent=2, ensure_ascii=False))
        save_parsed_result(processed_result)
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        print(f"エラーの種類: {type(e).__name__}")
        if "api_key" in str(e).lower():
            print("\n💡 ヒント: .envファイルに正しいOPENAI_API_KEYが設定されているか確認してください。")

if __name__ == "__main__":
    # プロジェクトルートの設定
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    print(f"プロジェクトルートパス: {project_root}")
    print(f"Pythonパスに追加されました: {project_root in sys.path}")
    
    main()
