"""
LLM抽出処理モジュール

OpenAI APIを使用してAPI仕様書からグラフデータを抽出します。
"""

import re
import json
from typing import Dict, List, Any
from langchain_openai import ChatOpenAI

from ..core.exceptions import LLMError, DataProcessingError
from ..core.logger import get_logger

logger = get_logger(__name__)


class LLMExtractor:
    """LLMを使用したグラフデータ抽出クラス"""

    def __init__(
        self, openai_api_key: str, model_name: str = "gpt-4", temperature: float = 0
    ):
        """
        初期化

        Args:
            openai_api_key: OpenAI APIキー
            model_name: 使用するモデル名
            temperature: 生成温度（推論モデルの場合はNone）
        """
        # 推論モデルかどうかを判定
        inference_models = ["o4-mini", "o4", "gpt-5", "gpt-5-mini", "gpt-5-nano"]
        is_inference_model = any(model in model_name.lower() for model in inference_models)

        # LLM設定を構築
        llm_config = {
            "openai_api_key": openai_api_key,
            "model_name": model_name,
        }

        if is_inference_model:
            # 推論モデル用パラメータ（temperatureは使用しない）
            from ..config import (
                LLM_VERBOSITY,
                LLM_REASONING_EFFORT,
                LLM_OUTPUT_VERSION,
            )
            # response_formatはLangChainで問題を起こす可能性があるため削除
            # プロンプトでJSON形式を指定することで対応
            llm_config.update({
                "reasoning_effort": LLM_REASONING_EFFORT,
                "output_version": LLM_OUTPUT_VERSION,
                "verbosity": LLM_VERBOSITY,
                # response_formatは削除（LangChainが関数定義として解釈するため）
            })
        else:
            # 標準モデル用パラメータ
            if temperature is not None:
                llm_config["temperature"] = temperature

        self.llm = ChatOpenAI(**llm_config)

    def extract_graph_from_specs(
        self, raw_text: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        API仕様書テキストからノードとリレーションを抽出する

        Args:
            raw_text: API仕様書の生テキスト

        Returns:
            抽出されたグラフデータ（nodes, relationships）

        Raises:
            LLMError: LLM処理エラー時
        """
        prompt = self._build_graph_extraction_prompt(raw_text)

        try:
            logger.info("LLMによるAPI仕様書からのグラフ抽出を開始")
            response = self.llm.invoke(prompt)

            # レスポンス内容を取得（推論モデルと標準モデルで形式が異なる可能性がある）
            if hasattr(response, 'content'):
                response_content = response.content
            elif hasattr(response, 'text'):
                response_content = response.text
            elif isinstance(response, str):
                response_content = response
            else:
                # その他の形式の場合、文字列に変換を試みる
                response_content = str(response)

            logger.debug("LLMレスポンス受信（最初の500文字）: %s", response_content[:500] if response_content else "空")

            # レスポンスが空でないか確認
            if not response_content or not response_content.strip():
                logger.error("LLMレスポンスが空です。レスポンスオブジェクト: %s", type(response))
                raise LLMError("LLMレスポンスが空です")

            # JSONの抽出とパース
            graph_data = self._extract_json_from_response(response_content)

            nodes = graph_data.get("nodes", [])
            relationships = graph_data.get("relationships", [])

            logger.info(
                "グラフ抽出完了: ノード=%d件, リレーション=%d件", len(nodes), len(relationships)
            )
            return graph_data

        except LLMError:
            raise
        except Exception as e:
            logger.error("LLM処理エラー: %s", e, exc_info=True)
            raise LLMError("LLMによるグラフ抽出に失敗しました", str(e))

    def extract_datatype_descriptions(self, raw_text: str) -> Dict[str, str]:
        """
        api_arg.txtからデータ型の説明を抽出する

        Args:
            raw_text: api_arg.txtの内容

        Returns:
            データ型名と説明のマッピング

        Raises:
            LLMError: LLM処理エラー時
        """
        prompt = self._build_datatype_extraction_prompt(raw_text)

        try:
            logger.info("LLMによるデータ型説明の抽出を開始")
            response = self.llm.invoke(prompt)

            # レスポンス内容を取得（推論モデルと標準モデルで形式が異なる可能性がある）
            if hasattr(response, 'content'):
                response_content = response.content
            elif hasattr(response, 'text'):
                response_content = response.text
            elif isinstance(response, str):
                response_content = response
            else:
                # その他の形式の場合、文字列に変換を試みる
                response_content = str(response)

            logger.debug("LLMレスポンス受信（最初の500文字）: %s", response_content[:500] if response_content else "空")

            # レスポンスが空でないか確認
            if not response_content or not response_content.strip():
                logger.error("LLMレスポンスが空です。レスポンスオブジェクト: %s", type(response))
                raise LLMError("LLMレスポンスが空です")

            # JSONの抽出とパース
            type_descriptions = self._extract_json_from_response(response_content)

            logger.info("データ型説明抽出完了: %d件", len(type_descriptions))
            return type_descriptions

        except LLMError:
            raise
        except Exception as e:
            logger.error("LLM処理エラー: %s", e, exc_info=True)
            raise LLMError("LLMによるデータ型説明抽出に失敗しました", str(e))

    def _build_graph_extraction_prompt(self, raw_text: str) -> str:
        """グラフ抽出用のプロンプトを構築する"""
        return f"""
        あなたはAPI仕様書を解析し、知識グラフを構築する専門家です。
        以下のAPI仕様書テキストから、指定されたスキーマに従ってノードとリレーションを抽出し、JSON形式で出力してください。

        --- グラフのスキーマ定義 ---
        1.  **ノードの種類とプロパティ:**
            - `Object`: APIの操作対象となるオブジェクト。 (例: "Part")
                - `id`: オブジェクト名 (例: "Part")
                - `properties`: {{ "name": "オブジェクト名" }}
            - `Method`: オブジェクトに属するメソッド。
                - `id`: メソッド名 (例: "CreateVariable")
                - `properties`: {{ "name": "メソッド名", "description": "メソッドの日本語説明" }}
            - `Parameter`: メソッドが受け取る引数。
                - `id`: `メソッド名_引数名` (例: "CreateVariable_VariableName")
                - `properties`: {{ "name": "引数名", "description": "引数の説明", "order": 引数の順番(0から) }}
            - `ReturnValue`: メソッドの戻り値。
                - `id`: `メソッド名_ReturnValue` (例: "CreateVariable_ReturnValue")
                - `properties`: {{ "description": "戻り値の説明" }}
            - `DataType`: 引数や戻り値、属性の型。
                - `id`: データ型名 (例: "文字列", "長さ", "bool", "ブラケット要素のパラメータオブジェクト", "整数")
                - `properties`: {{ "name": "データ型名" }} # 説明は後で別のプロンプトで付与します
            - `Attribute`: パラメータオブジェクトが持つ属性。
                - `id`: `データ型名_属性名` (例: "ブラケット要素のパラメータオブジェクト_DefinitionType")
                - `properties`: {{ "name": "属性名", "description": "属性の日本語説明 (型情報を除いたもの)" }}

        2.  **リレーションの種類:**
            - `BELONGS_TO`: (Method) -> (Object)
            - `HAS_PARAMETER`: (Method) -> (Parameter)
            - `HAS_RETURNS`: (Method) -> (ReturnValue)
            - `HAS_TYPE`: (Parameter) -> (DataType), (ReturnValue) -> (DataType), (Attribute) -> (DataType)
            - `HAS_ATTRIBUTE`: (DataType) -> (Attribute)

        --- 抽出ルール ---
        1.  `■オブジェクト名` は `Object` ノードとし、後続の `Method` は `BELONGS_TO` で接続してください。
        2.  `〇〇パラメータオブジェクト` というセクションは `DataType` ノードとしてください。
        3.  上記 `DataType` に続く `属性` (例: `DefinitionType //s整数: ...`) は
            `Attribute` ノード (`id: DataType_Attr`) とし、`DataType` に `HAS_ATTRIBUTE` で接続してください。
        4.  `Attribute` の `description` には型情報 (例: `整数:`, `文字列：`) を *除いた*
            説明文 (例: "ブラケットの作成方法指定...") を格納してください。
        5.  `//` の後の説明文に型情報 (例: `整数:`) が含まれる場合、
            (Attribute)から該当`DataType` (例: "整数") へ `HAS_TYPE` リレーションを張ってください。
        6.  `Create[... ]Param` (例: `CreateBracketParam`) メソッドは、
            対応する `〇〇パラメータオブジェクト` (例: "ブラケット要素のパラメータオブジェクト") を
            `DataType` とする `ReturnValue` を持つ `Method` として抽出してください。
        7.  Parameterノードのdescriptionには、`：`の後の文章をそのまま指定してください。

        --- 出力形式 ---
        - 全体を1つのJSONオブジェクトで出力してください。
        - **`nodes`** の値は、以下の形式の**ノードオブジェクト**のリストです:
        `{{"id": "一意のID", "type": "ノードの種類", "properties": {{...}} }}`
        - **`relationships`** の値は、以下の形式の**リレーションオブジェクト**のリストです:
        `{{"source": "ソースノードID", "target": "ターゲットノードID", "type": "リレーションの種類"}}`

        --- API仕様書テキスト ---
        {raw_text}
        --- ここまで ---

        抽出後のJSON:
        """

    def _build_datatype_extraction_prompt(self, raw_text: str) -> str:
        """データ型説明抽出用のプロンプトを構築する"""
        return f"""
        あなたはAPI仕様書のデータ型定義を解析する専門家です。
        以下のテキストから、データ型とその説明文を抽出し、JSON形式で出力してください。

        --- 解析ルール ---
        1.  `■` (U+25A0) で始まる行は、新しいデータ型の定義開始を示します。
        2.  `■` の後に続くテキストが「データ型名」です (例: `■文字列` -> "文字列")。
        3.  データ型名の次の行から、次の `■` が出現する直前まで、またはファイルの終わりまでが、そのデータ型の「説明文」です。
        4.  説明文は、改行を含めてそのまま連結してください。

        --- 出力形式 ---
        - 全体を1つのJSONオブジェクトで出力してください。
        - キーを「データ型名」、値を「説明文」とした辞書(マップ)形式とします。
        - 例: {{"文字列": "通常の文字列", "浮動小数点": "通常の数値\\n\\n例: 3.14"}}
        - JSONはマークダウンのコードブロック(` ```json ... ``` `)で囲んでください。
        - JSONオブジェクトにはコメントをいれないでください。
        - 必ずJSONオブジェクトで出力してください。

        --- データ型定義テキスト ---
        {raw_text}
        --- ここまで ---

        抽出後のJSON:
        """

    def _extract_json_from_response(self, response_content: str) -> Dict[str, Any]:
        """
        LLMレスポンスからJSONを抽出・パースする

        Args:
            response_content: LLMのレスポンス内容

        Returns:
            パースされたJSONデータ

        Raises:
            DataProcessingError: JSON抽出・パースエラー時
        """
        try:
            # レスポンスが空でないか確認
            if not response_content or not response_content.strip():
                raise DataProcessingError("レスポンス内容が空です")

            # マークダウンのコードブロックからJSON部分を抽出
            match = re.search(r"```json\s*([\s\S]+?)\s*```", response_content)
            if match:
                json_str = match.group(1).strip()
                logger.debug("JSONコードブロックを抽出: %s", json_str[:200])
                return json.loads(json_str)
            else:
                # コードブロックがない場合、直接パースを試みる
                # レスポンスの前後の不要な文字を削除
                cleaned_content = response_content.strip()
                # JSONオブジェクトの開始位置を探す
                json_start = cleaned_content.find('{')
                if json_start != -1:
                    cleaned_content = cleaned_content[json_start:]
                logger.debug("直接パースを試行: %s", cleaned_content[:200])
                return json.loads(cleaned_content)
        except json.JSONDecodeError as e:
            logger.error("JSONパースエラー: %s", e)
            logger.error("レスポンス内容（最初の1000文字）: %s", response_content[:1000])
            raise DataProcessingError("JSONパースエラー", f"{str(e)} - レスポンス内容をログに記録しました")
        except Exception as e:
            logger.error("JSON抽出エラー: %s", e)
            logger.error("レスポンス内容（最初の1000文字）: %s", response_content[:1000])
            raise DataProcessingError("JSON抽出エラー", str(e))
