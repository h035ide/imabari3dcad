from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import json
import os
import sys

load_dotenv()

def read_file_safely(file_path, encoding="utf-8"):
    """
    ファイルを安全に読み込む共通関数
    Args:
        file_path (str): 読み込むファイルのパス
        encoding (str): ファイルのエンコーディング（デフォルト: utf-8）
    Returns:
        str: ファイルの内容
    Raises:
        FileNotFoundError: 指定されたファイルが見つからない場合
        UnicodeDecodeError: ファイルのエンコーディングが不正な場合
        IOError: その他のファイル読み込みエラー
    """
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
    api_doc_path="data/src/api 1.txt",
    api_arg_path="data/src/api_arg 1.txt"
):
    """
    APIドキュメントと引数情報を連結して読み込む関数

    Args:
        api_doc_path (str): API関数の仕様が書かれたテキストファイルのパス
        api_arg_path (str): API引数の仕様が書かれたテキストファイルのパス

    Returns:
        str: 2つのドキュメントを結合した内容

    Raises:
        FileNotFoundError: 指定されたファイルが見つからない場合
        IOError: ファイル読み込みエラー
    """
    try:
        api_doc_content = read_file_safely(api_doc_path)
        api_arg_content = read_file_safely(api_arg_path)
        
        # 2つのドキュメントを結合
        combined_document = f"""
# APIドキュメント

{api_doc_content}

---

# 引数の型と書式

{api_arg_content}
"""
        return combined_document
    except (FileNotFoundError, IOError) as e:
        print(f"ドキュメントの読み込みに失敗しました: {e}")
        raise

def load_prompt(file_path=None):
    """
    プロンプトファイルを読み込む関数
    
    Args:
        file_path (str): プロンプトファイルのパス
        
    Returns:
        str: プロンプトファイルの内容
        
    Raises:
        FileNotFoundError: 指定されたファイルが見つからない場合
        UnicodeDecodeError: ファイルのエンコーディングが不正な場合
        IOError: その他のファイル読み込みエラー
    """
    if file_path is None:
        DEFAULT_PROMPT = """あなたは「EVO.SHIP API」ドキュメントの解析に特化した、非常に優秀なソフトウェアエンジニアです。
提供されたAPIドキュメントを厳密に解析し、指定されたJSON形式の**単一のオブジェクト**として出力してください。

# 全体的な指示
- **出力は有効なJSONオブジェクトのみ**とし、Markdownやその他のテキストは一切含めないでください。
- ドキュメントに明記されていない情報の推測や補完は行わないでください。
- 解析対象ドキュメントは、「APIドキュメント」セクションと「引数の型と書式」セクションで構成されています。

# 解析のポイント
1.  **型の定義の抽出 (`type_definitions`)**:
    - まず、「引数の型と書式」セクションを解析し、そこにリストアップされているすべてのデータ型（例：「長さ」「角度」「平面」など）を抽出してください。
    - 各型について、`name`（型名）と`description`（その型の書式や仕様に関する説明文）を格納してください。

2.  **APIエントリーの抽出 (`api_entries`)**:
    - 「APIドキュメント」セクションを解析し、各関数やオブジェクト定義を抽出してください。
    - **エントリーの種類の識別**:
        - 各API（メソッド）は `entry_type: "function"` として解析してください。
        - 「〜のパラメータオブジェクト」のような、独立したオブジェクト定義は `entry_type: "object_definition"` として別のエントリーで解析してください。
    - **フィールドの抽出**:
        - `name`: 関数名やオブジェクト名を抽出します。
        - `params`: 関数の引数リスト。`name`, `position` (0から始まる引数の位置), `type`, `description`, `is_required` を設定します。
        - `properties`: オブジェクト定義の属性リスト。`name`, `type`, `description` を設定します。
        - `returns`: 関数の戻り値。`type`, `description`, `is_array` を設定します。戻り値がない場合は `type: "void"` としてください。
        - `is_required`: 引数の説明に「（空文字不可）」や「必須」とあれば `true`、なければ `false` とします。
        - `implementation_status`: 「（未実装、使用しない）」という記述があれば `'unimplemented'` と設定します。それ以外は `'implemented'` とします。

# 出力フォーマット
{json_format}

# 解析対象ドキュメント
---
{document}
---"""
        return DEFAULT_PROMPT
    return read_file_safely(file_path)

def load_json_format_instructions(file_path=None):
    if file_path is None:
        DEFAULT_JSON_FORMAT_INSTRUCTIONS = """
{
  "type_definitions": [
    {
      "name": "string (e.g., '長さ', '点', '平面')",
      "description": "string (The specification or format of the type)"
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
        return DEFAULT_JSON_FORMAT_INSTRUCTIONS
    return read_file_safely(file_path)

def write_file_safely(file_path, content, encoding="utf-8"):
    """
    ファイルを安全に書き込む共通関数
    
    Args:
        file_path (str): 書き込むファイルのパス
        content (str): 書き込む内容
        encoding (str): ファイルのエンコーディング（デフォルト: utf-8）
        
    Raises:
        IOError: ファイル書き込みエラー
        PermissionError: ファイルへの書き込み権限がない場合
    """
    try:
        # ディレクトリが存在しない場合は作成
        import os
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, "w", encoding=encoding) as file:
            file.write(content)
    except PermissionError:
        raise PermissionError(f"ファイルへの書き込み権限がありません: {file_path}")
    except IOError as e:
        raise IOError(f"ファイル書き込みエラー: {file_path} - {str(e)}")

def save_parsed_result(parsed_result, output_file_path="doc_paser/parsed_api_result.json"):
    """
    解析結果をJSONファイルとして保存する関数
    
    Args:
        parsed_result (dict or list): 保存する解析結果（辞書またはリスト）
        output_file_path (str): 出力ファイルのパス（デフォルト: parsed_api_result.json）
        
    Raises:
        IOError: ファイル書き込みエラー
        PermissionError: ファイルへの書き込み権限がない場合
    """
    import json
    
    try:
        # 解析結果をJSON形式で整形
        json_content = json.dumps(parsed_result, ensure_ascii=False, indent=2)
        
        # ファイルに保存
        write_file_safely(output_file_path, json_content)
        
        print(f"解析結果を保存しました: {output_file_path}")
        
    except Exception as e:
        print(f"解析結果の保存に失敗しました: {str(e)}")
        raise

def normalize_type_name(type_name: str) -> str:
    if not isinstance(type_name, str):
        return type_name
    name = type_name.strip()
    mapping = {
        "string": "文字列",
        "str": "文字列",
        "float": "浮動小数点",
        "double": "浮動小数点",
        "number": "浮動小数点",
        "int": "整数",
        "integer": "整数",
        "boolean": "bool",
        "bool": "bool",
        "length": "長さ",
        "angle": "角度",
        "direction": "方向",
        "direction2d": "方向(2D)",
        "plane": "平面",
        "point": "点",
        "point2d": "点(2D)",
        "element": "要素",
        "elementid": "要素ID",
        "element group": "要素グループ",
        "material": "材料",
        "style": "注記スタイル",
        "bstr": "BSTR",
        "配列": "配列",
        "浮動小数点(配列)": "浮動小数点(配列)",
    }
    key = name.lower().replace(" ", "")
    return mapping.get(key, name)


def enrich_array_object_info(param: dict) -> None:
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
        if param.get("array_info") is None:
            param["array_info"] = None


def infer_is_required(param: dict) -> None:
    cons = param.get("constraints") or []
    desc = param.get("description_raw") or ""
    text = " ".join(cons) + " " + desc
    required = ("空文字不可" in text) or ("必須" in text)
    if "空文字可" in text:
        required = False
    param["is_required"] = bool(required)


def postprocess_parsed_result(parsed_result):
    if not isinstance(parsed_result, list):
        return parsed_result
    for fn in parsed_result:
        if isinstance(fn.get("returns"), dict):
            r_t = fn["returns"].get("type_name")
            if r_t is not None:
                fn["returns"]["type_name"] = normalize_type_name(r_t)
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

def main():
    try:
        # --- MOCK MODE ---
        # The script is currently in mock mode.
        # To run in live mode, comment out the following 2 lines and uncomment the 'LIVE MODE' block below.
        # print("🤖 APIキーが不要なモックモードで実行します。")
        # parsed_result = {
        #   "type_definitions": [{"name": "長さ", "description": "mm単位の数値、変数要素名、式文字列"}],
        #   "api_entries": [{"entry_type": "function", "name": "CreateSketchLine", "params": [{"position": 0, "name": "SketchPlane"}]}]
        # }

        # --- LIVE MODE (Commented out) ---
        # To run in live mode, uncomment the block below and comment out the 2 lines in the 'MOCK MODE' block above.
        # You will also need a valid OPENAI_API_KEY in your .env file.
        #
        print("🤖 LLMを使ってAPIドキュメントを解析しています...")
        api_document_text = load_api_document()
        prompt = ChatPromptTemplate.from_template(load_prompt())
        json_format_instructions = load_json_format_instructions()
        # reasoning_effortを使用してより良い解析結果を得る
        llm = ChatOpenAI(
            model="gpt-5-nano",
            reasoning_effort="minimal",  # 'low', 'medium', 'high' から選択
            model_kwargs={"response_format": {"type": "json_object"}}
        )
        
        # 直接JSONとしてパース
        try:
            response = llm.invoke(prompt.format(
                document=api_document_text,
                json_format=json_format_instructions
            ))
            parsed_result = json.loads(response.content)
        except json.JSONDecodeError as e:
            print(f"JSONパースエラー: {e}")
            print("LLM出力:", response.content)
            raise

        # --- Common Processing ---
        print("\n✅ 解析が完了し、JSONオブジェクトが生成されました。")
        print(json.dumps(parsed_result, indent=2, ensure_ascii=False))
        save_parsed_result(parsed_result)

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        print(f"エラーの種類: {type(e).__name__}")
        if "api_key" in str(e).lower():
            print("\n💡 ヒント: .envファイルに正しいOPENAI_API_KEYが設定されているか確認してください。")
        pass
if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    print(f"プロジェクトルートパス: {project_root}")
    print(f"Pythonパスに追加されました: {project_root in sys.path}")
    
    main()
