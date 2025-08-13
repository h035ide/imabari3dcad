import os
import sys
import logging
from typing import Type, Dict, Any, List

# --- [Path Setup] ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- [End Path Setup] ---

from dotenv import load_dotenv
from neo4j import GraphDatabase
from langchain.tools import BaseTool
import subprocess
import tempfile
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from code_generator.schemas import ExtractedParameters

# .envファイルを読み込む
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path)

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 定数定義 ---
CHROMA_PERSIST_DIRECTORY = os.path.join(project_root, "chroma_db_store")
CHROMA_COLLECTION_NAME = "api_functions"

class GraphSearchInput(BaseModel):
    """グラフ検索ツールの入力スキーマ。"""
    query: str = Field(description="ナレッジグラフから情報を検索するための自然言語クエリ。")

class GraphSearchTool(BaseTool):
    """
    APIの機能やコード例を検索するためのハイブリッド検索ツール。
    まずベクトル検索で関連性の高いAPI候補を見つけ、次にグラフデータベースで詳細情報を取得します。
    """
    name: str = "hybrid_graph_knowledge_search"
    description: str = (
        "APIの機能、関数、クラス、またはコード例に関する情報を検索する場合に必ず使用します。"
        "「球を作成する関数」や「特定のパラメータを持つAPI」など、"
        "探している機能やコードを自然言語で具体的に記述したクエリを入力してください。"
    )
    args_schema: Type[BaseModel] = GraphSearchInput

    _neo4j_driver: GraphDatabase.driver = None
    _vector_store: Chroma = None
    _is_configured: bool = False

    def __init__(self, **data):
        super().__init__(**data)

        api_key = os.getenv("OPENAI_API_KEY")
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASSWORD")

        if not all([api_key, uri, user, password]):
            logger.warning("必要な環境変数が見つからないため、GraphSearchToolは非アクティブモードで初期化されました。")
            self._is_configured = False
        else:
            # Neo4jドライバを初期化
            self._neo4j_driver = GraphDatabase.driver(uri, auth=(user, password))
            self._db_name = os.getenv("NEO4J_DATABASE", "neo4j")

            # ChromaDBクライアントと埋め込み関数を初期化
            embedding_function = OpenAIEmbeddings(api_key=api_key)
            self._vector_store = Chroma(
                collection_name=CHROMA_COLLECTION_NAME,
                embedding_function=embedding_function,
                persist_directory=CHROMA_PERSIST_DIRECTORY
            )
            self._is_configured = True
            logger.info("GraphSearchToolは正常に設定され、アクティブです。")

    def _run(self, query: str) -> str:
        """ツールの同期実行ロジック（ハイブリッド検索）。"""
        if not self._is_configured:
            return "ツールが設定されていません。APIキーとDB接続情報を確認してください。"

        if not os.path.exists(CHROMA_PERSIST_DIRECTORY):
            return (f"ChromaDBのデータベースが見つかりません。先にデータ格納スクリプトを実行してください。\n"
                    f"コマンド: `python -m code_generator.db.ingest_to_chroma`")

        logger.info(f"ハイブリッド検索を開始。クエリ: '{query}'")
        try:
            # 1. ベクトル検索で関連性の高いノード候補を取得
            logger.info(f"ステップ1/2: ChromaDBでベクトル検索を実行中...")
            # `include=['metadatas', 'documents']` を指定して、Re-Rankingで利用するドキュメント内容も取得
            results = self._vector_store.similarity_search(query, k=20) # Re-Rankingのため、より多くの候補(k=20)を取得

            if not results:
                return "ベクトル検索で関連するAPIが見つかりませんでした。"

            logger.info(f"{len(results)}件の候補をベクトル検索で発見しました。")

            # --- [Re-Ranking Integration Point] ---
            # Re-Ranking機能を有効化するには、以下のコメントを解除し、ReRankerをインポートしてください。
            # from code_generator.rerank_feature.reranker import ReRanker
            # reranker = ReRanker()
            # reranked_results = reranker.rerank(query, results)
            # top_results = reranked_results[:5] # 上位5件に絞り込み
            # logger.info(f"Re-Ranking後の候補件数: {len(top_results)}")
            # node_ids = [doc.metadata.get("neo4j_node_id") for doc in top_results if doc.metadata.get("neo4j_node_id")]
            # --- [End Re-Ranking Integration Point] ---

            # 注：上記のRe-Rankingを有効化した場合、以下の行は不要になります。
            node_ids = [doc.metadata.get("neo4j_node_id") for doc in results if doc.metadata.get("neo4j_node_id")]

            # 2. グラフ探索で詳細情報を取得
            logger.info(f"ステップ2/2: Neo4jで詳細情報を取得中...")

            if not node_ids:
                 return "ベクトル検索の結果から有効なノードIDを取得できませんでした。"

            cypher_query = """
            MATCH (api:APIFunction)
            WHERE elementId(api) IN $node_ids
            OPTIONAL MATCH (f:Function)-[:IMPLEMENTS_API]->(api)
            OPTIONAL MATCH (api)-[:HAS_PARAMETER]->(p:Parameter)
            OPTIONAL MATCH (c:Class)-[:CONTAINS]->(f)
            OPTIONAL MATCH (caller:Function)-[:CALLS]->(f)
            OPTIONAL MATCH (api)-[:RETURNS]->(ret)
            RETURN api.name AS apiName,
                   api.description AS apiDescription,
                   f.signature AS functionSignature,
                   c.name AS className,
                   collect(DISTINCT p.name) AS parameters,
                   collect(DISTINCT caller.name) AS calledBy,
                   labels(ret)[0] AS returnType,
                   ret.name AS returnName
            """

            with self._neo4j_driver.session(database=self._db_name) as session:
                result = session.run(cypher_query, node_ids=node_ids)
                records = [record.data() for record in result]

            if not records:
                return "グラフデータベースで詳細情報の取得に失敗しました。"

            return self._format_results(records)

        except Exception as e:
            logger.error(f"ハイブリッド検索の実行中にエラーが発生しました: {e}", exc_info=True)
            return f"ツールの実行中にエラーが発生しました: {e}"

    def _format_results(self, records: List[Dict[str, Any]]) -> str:
        """データベースの検索結果をエージェントが理解しやすい文字列に整形します。"""
        if not records: return "結果なし"

        formatted_string = "ナレッジグラフから以下の情報が見つかりました:\n\n"
        for i, record in enumerate(records):
            formatted_string += f"--- 関連API候補 {i+1} ---\n"

            # RETURNで指定した順序に近い形で、見やすく整形
            if record.get('apiName'):
                formatted_string += f"- API名: {record['apiName']}\n"
            if record.get('className'):
                formatted_string += f"- 所属クラス: {record['className']}\n"
            if record.get('description'):
                formatted_string += f"- 説明: {record['description']}\n"
            if record.get('functionSignature'):
                formatted_string += f"- シグネチャ: {record['functionSignature']}\n"

            # パラメータリストの整形
            params = record.get('parameters')
            if params:
                # 空の要素('')やNoneを除外
                clean_params = [p for p in params if p]
                formatted_string += f"- パラメータ: {', '.join(clean_params) if clean_params else 'なし'}\n"

            # 戻り値の整形
            ret_type = record.get('returnType')
            ret_name = record.get('returnName')
            if ret_type and ret_name:
                 formatted_string += f"- 戻り値: {ret_name} (型: {ret_type})\n"
            elif ret_type:
                 formatted_string += f"- 戻り値の型: {ret_type}\n"

            # 呼び出し元リストの整形
            called_by = record.get('calledBy')
            if called_by:
                clean_called_by = [c for c in called_by if c]
                if clean_called_by:
                    formatted_string += f"- 主な呼び出し元: {', '.join(clean_called_by)}\n"

            formatted_string += "\n"

        return formatted_string

    def close(self):
        """ドライバ接続を閉じます。"""
        if self._neo4j_driver:
            self._neo4j_driver.close()

# `if __name__ == '__main__':` ブロックは、テストファイルに移行したため削除。
# このファイルはツール定義に専念する。

# --- Unit Test Tool ---

class UnitTestInput(BaseModel):
    """単体テストツールの入力スキーマ。"""
    code_to_test: str = Field(description="テスト対象のPythonコード文字列。")
    test_code: str = Field(description="テスト対象コードを検証するためのunittestコード文字列。")

class UnitTestTool(BaseTool):
    """
    生成されたPythonコードとそれに対応する単体テストを実行し、
    コードが期待通りに動作するかを検証するツール。
    """
    name: str = "python_unit_test_runner"
    description: str = (
        "Pythonコードとそのコードを検証するための単体テスト（unittest）を実行するために使用します。"
        "引数'code_to_test'にテストしたいコード、'test_code'にテストコードをそれぞれ文字列として渡してください。"
        "テストコードは、'code_to_test'のコードをモジュールとしてインポートしてテストする必要があります。"
    )
    args_schema: Type[BaseModel] = UnitTestInput

    def _run(self, code_to_test: str, test_code: str) -> str:
        logger.info("UnitTestToolの実行を開始...")

        # 一時ディレクトリを作成して、ソースコードとテストコードを配置
        with tempfile.TemporaryDirectory() as tmp_dir:
            source_filepath = os.path.join(tmp_dir, "source_code.py")
            test_filepath = os.path.join(tmp_dir, "test_code.py")

            with open(source_filepath, "w", encoding="utf-8") as f:
                f.write(code_to_test)

            with open(test_filepath, "w", encoding="utf-8") as f:
                f.write(test_code)

            # unittestをサブプロセスとして実行
            # cwdを一時ディレクトリに設定し、PYTHONPATHにも追加することで、
            # テストコードがソースコードを正しくインポートできるようにする
            logger.info(f"unittestを実行: python -m unittest {os.path.basename(test_filepath)}")
            process = subprocess.run(
                [sys.executable, '-m', 'unittest', os.path.basename(test_filepath)],
                capture_output=True,
                text=True,
                encoding='utf-8',
                cwd=tmp_dir,
                env={**os.environ, "PYTHONPATH": tmp_dir}
            )

            # unittestは通常、結果をstderrに出力する
            output = process.stderr

            if "OK" in output and "FAILED" not in output:
                logger.info("単体テストに成功しました。")
                return "単体テストに成功しました。コードは期待通りに動作します。"
            else:
                logger.warning(f"単体テストで失敗またはエラーが検出されました:\n{output}")
                return f"単体テストで失敗またはエラーが検出されました:\n{output}"

# --- Code Validation Tool ---

class CodeValidationInput(BaseModel):
    """コード検証ツールの入力スキーマ。"""
    code: str = Field(description="検証対象のPythonコード文字列。")

# --- Parameter Extraction Tool ---

class ParameterExtractionInput(BaseModel):
    """パラメータ抽出ツールの入力スキーマ。"""
    query: str = Field(description="分析対象のユーザーの自然言語クエリ。")

class ParameterExtractionTool(BaseTool):
    """
    ユーザーの自然言語クエリを分析し、構造化された「意図」と「パラメータ」を抽出するツール。
    """
    name: str = "user_query_parameter_extractor"
    description: str = (
        "ユーザーからの最初の要求を分析するために使用します。"
        "ユーザーの主な目的（意図）と、サイズや名前などの具体的なパラメータを抽出します。"
    )
    args_schema: Type[BaseModel] = ParameterExtractionInput
    _llm: ChatOpenAI = None
    _parser: PydanticOutputParser = None
    _is_configured: bool = False

    def __init__(self, **data):
        super().__init__(**data)
        if not os.getenv("OPENAI_API_KEY"):
            logger.warning("OPENAI_API_KEYが見つからないため、ParameterExtractionToolは非アクティブです。")
            self._is_configured = False
        else:
            self._llm = ChatOpenAI(model="gpt-4o", temperature=0)
            self._parser = PydanticOutputParser(pydantic_object=ExtractedParameters)
            self._is_configured = True

    def _run(self, query: str) -> dict:
        if not self._is_configured:
            return {"intent": query, "parameters": {}}

        logger.info(f"ParameterExtractionToolの実行を開始。クエリ: '{query}'")

        prompt_template = """
        ユーザーの以下の要求から、その主な「意図」と、指定されている「パラメータ」を抽出し、指定されたJSON形式で出力してください。

        ### 要求
        {query}

        ### 指示
        - 「意図」は、ユーザーが何をしたいのかを簡潔に表現する文字列です。（例：「立方体を作成」「球を検索」）
        - 「パラメータ」は、キーと値のペアを持つ辞書です。数値は必ず数値型に変換してください。
        - 該当するパラメータがない場合は、空の辞書 `{{}}` を返してください。

        ### 例
        - 要求: "一辺が50mmの正方形のキューブを作成してください"
        - 出力JSON: {{"intent": "create a square cube", "parameters": {{"side_length": 50}}}}

        - 要求: "青色のボールを作って"
        - 出力JSON: {{"intent": "create a ball", "parameters": {{"color": "blue"}}}}

        {format_instructions}
        """

        prompt = prompt_template.format(
            query=query,
            format_instructions=self._parser.get_format_instructions()
        )

        try:
            response = self._llm.invoke(prompt)
            parsed_response = self._parser.parse(response.content)
            logger.info(f"パラメータ抽出成功: {parsed_response}")
            return parsed_response.dict()
        except Exception as e:
            logger.error(f"パラメータの抽出中にエラーが発生しました: {e}", exc_info=True)
            # フォールバックとして、意図をクエリ全体とし、パラメータを空にする
            return {"intent": query, "parameters": {}}

class CodeValidationTool(BaseTool):
    """
    Pythonコードを静的解析ツール(flake8)で検証し、エラーやスタイル問題を検出するツール。
    """
    name: str = "python_code_validator"
    description: str = (
        "Pythonコードの品質をチェックするために使用します。"
        "構文エラー、未使用のインポート、スタイル違反などの問題を検出できます。"
        "引数'code'に、検証したいPythonコードの全文を文字列として渡してください。"
    )
    args_schema: Type[BaseModel] = CodeValidationInput

    def _run(self, code: str) -> str:
        """flake8を使ってコードを検証する同期実行ロジック。"""
        logger.info("CodeValidationToolの実行を開始...")

        # 一時ファイルを作成してコードを書き込む
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_file:
            tmp_file.write(code)
            tmp_filepath = tmp_file.name

        try:
            # flake8をサブプロセスとして実行
            process = subprocess.run(
                ['flake8', tmp_filepath],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )

            if process.returncode == 0 and not process.stdout:
                logger.info("コードの検証に成功しました。問題は見つかりませんでした。")
                return "コードの検証に成功しました。問題は見つかりませんでした。"
            else:
                logger.warning(f"コードの検証で問題が検出されました:\n{process.stdout}")
                # flake8の出力からファイルパス部分を除去して、よりクリーンな結果を返す
                clean_output = '\n'.join(line.split(':', 1)[1] for line in process.stdout.strip().split('\n'))
                return f"コードの検証で以下の問題が検出されました:\n{clean_output}"

        except FileNotFoundError:
            logger.error("flake8コマンドが見つかりません。環境にインストールされているか確認してください。")
            return "エラー: flake8コマンドが見つかりません。"
        except Exception as e:
            logger.error(f"コード検証中に予期せぬエラーが発生しました: {e}", exc_info=True)
            return f"コード検証中に予期せぬエラーが発生しました: {e}"
        finally:
            # 一時ファイルを確実に削除
            if os.path.exists(tmp_filepath):
                os.remove(tmp_filepath)
