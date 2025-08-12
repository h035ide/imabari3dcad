import os
import sys
import json
import logging
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# ロギング設定
logger = logging.getLogger(__name__)

class ApiParser:
    """
    自然言語のAPIドキュメントを解析し、構造化されたJSONを出力するクラス。
    """

    def __init__(self, model_name="gpt-4-turbo", reasoning_effort="medium"):
        """
        ApiParserを初期化します。

        Args:
            model_name (str): 使用するOpenAIのモデル名。
            reasoning_effort (str): LangChainのreasoning_effortパラメータ。
        """
        self.llm = ChatOpenAI(
            model="gpt-5-nano",
            reasoning_effort="low",  # 'low', 'medium', 'high' から選択
        )
        logger.info(f"ApiParserがモデル '{model_name}' で初期化されました。")

    def _read_file_safely(self, file_path, encoding="utf-8"):
        """ファイルを安全に読み込む。"""
        try:
            with open(file_path, "r", encoding=encoding) as file:
                return file.read()
        except FileNotFoundError:
            logger.error(f"ファイルが見つかりません: {file_path}")
            raise
        except Exception as e:
            logger.error(f"ファイル読み込みエラー ({file_path}): {e}")
            raise

    def _load_api_document(self, api_doc_path: str, api_arg_path: str) -> str:
        """APIドキュメントと引数情報を連結して読み込む。"""
        try:
            api_doc_content = self._read_file_safely(api_doc_path)
            api_arg_content = self._read_file_safely(api_arg_path)

            combined_document = f"""
# APIドキュメント
{api_doc_content}
---
# 引数の型と書式
{api_arg_content}
"""
            return combined_document
        except Exception as e:
            logger.error(f"APIドキュメントの読み込みに失敗しました: {e}")
            raise

    def _get_prompt_template(self) -> str:
        """LLMに与えるプロンプトテンプレートを返す。"""
        return """あなたは「EVO.SHIP API」ドキュメントの解析に特化した、非常に優秀なソフトウェアエンジニアです。
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
        - `description`: 関数やオブジェクトの概要説明。
        - `category`: 所属するカテゴリ。
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

    def _get_json_format_instructions(self) -> str:
        """期待するJSONのフォーマットを説明する文字列を返す。"""
        return """
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

    def parse(self, api_doc_path: str, api_arg_path: str) -> dict:
        """
        APIドキュメントを解析して、構造化された辞書を返します。

        Args:
            api_doc_path (str): API関数の仕様が書かれたテキストファイルのパス。
            api_arg_path (str): API引数の仕様が書かれたテキストファイルのパス。

        Returns:
            dict: 解析されたAPIの構造。
        """
        logger.info(f"APIドキュメントの解析を開始します: {api_doc_path}, {api_arg_path}")

        api_document_text = self._load_api_document(api_doc_path, api_arg_path)
        prompt_template = self._get_prompt_template()
        json_format_instructions = self._get_json_format_instructions()

        prompt = ChatPromptTemplate.from_template(prompt_template)

        chain = prompt | self.llm

        try:
            response = chain.invoke({
                "document": api_document_text,
                "json_format": json_format_instructions
            })

            # response.contentがJSON文字列であることを想定
            parsed_result = json.loads(response.content)
            logger.info("APIドキュメントの解析が完了し、JSONオブジェクトが生成されました。")

            # ここで後処理を追加することも可能
            # postprocessed_result = self._postprocess(parsed_result)
            # return postprocessed_result

            return parsed_result

        except json.JSONDecodeError as e:
            logger.error(f"LLMからの応答のJSONパースに失敗しました: {e}")
            logger.debug(f"LLM出力: {response.content}")
            raise
        except Exception as e:
            logger.error(f"LLMの呼び出し中に予期せぬエラーが発生しました: {e}")
            raise

    def _postprocess(self, parsed_result: dict) -> dict:
        """
        解析結果の後処理を行います（正規化など）。
        (現在は `neo4j_uploader` にロジックがあるため、必要に応じてこちらに移動)
        """
        # TODO: 必要に応じて `doc_paser.py` の後処理ロジックをここに移植
        return parsed_result
