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

def load_system_prompt(file_path=None):
    """
    システムプロンプト（役割・方針・フォーマット指示）を読み込む関数
    """
    if file_path is None:
        DEFAULT_SYSTEM_PROMPT = """
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
                    <item>「引数の型と書式」から全データ型（例: 長さ, 角度, 平面 等）を抽出する。</item>
                    <item>各型は name と description を格納する。</item>
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
        return DEFAULT_SYSTEM_PROMPT
    return read_file_safely(file_path)

def load_user_prompt(file_path=None):
    """
    ユーザープロンプト（解析対象ドキュメントの提示）を読み込む関数
    """
    if file_path is None:
        DEFAULT_USER_PROMPT = """
以下のドキュメントを上記方針に従って解析し、単一のJSONオブジェクトのみを出力してください。

# 解析対象ドキュメント
---
{document}
---
"""
        return DEFAULT_USER_PROMPT
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
        # --- LIVE MODE ---
        print("🤖 LLMを使ってAPIドキュメントを解析しています...")
        api_document_text = load_api_document()
        system_prompt_template = load_system_prompt()
        user_prompt_template = load_user_prompt()
        json_format_instructions = load_json_format_instructions()
        
        # reasoning_effortを使用してより良い解析結果を得る
        llm = ChatOpenAI(
            model="gpt-5-nano",
            reasoning_effort="minimal",  # "minimal", 'low', 'medium', 'high' から選択
            model_kwargs={"response_format": {"type": "json_object"}}
        )
        
        # プロンプトを実行
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt_template),
                ("user", user_prompt_template),
            ])

            chain = prompt | llm
            response = chain.invoke({
                "document": api_document_text,
                "json_format": json_format_instructions,
            })
            parsed_result = json.loads(response.content)
        except json.JSONDecodeError as e:
            print(f"JSONパースエラー: {e}")
            print("LLM出力:", response.content)
            raise

        # 後処理を実行
        print("\n🔄 解析結果の後処理を実行中...")
        processed_result = postprocess_parsed_result(parsed_result)

        # --- Common Processing ---
        print("\n✅ 解析が完了し、JSONオブジェクトが生成されました。")
        print(json.dumps(processed_result, indent=2, ensure_ascii=False))
        save_parsed_result(processed_result)

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
