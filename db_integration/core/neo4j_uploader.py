import logging
import json
from typing import List
from neo4j import GraphDatabase
from .code_parser import SyntaxNode, SyntaxRelation

# ロギング設定
logger = logging.getLogger(__name__)

class Neo4jUploader:
    """
    解析されたデータをNeo4jデータベースにアップロードおよびリンクするためのクラス。
    """

    def __init__(self, uri, user, password, database):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        # データベース名の検証と修正
        self.database = self._sanitize_database_name(database)
        logger.info(f"Neo4jUploaderがデータベース '{self.database}' に接続されました。")
        # データベースが存在しない場合は作成
        self._ensure_database_exists()

    def _sanitize_database_name(self, database_name):
        """データベース名をNeo4jの命名規則に適合させます。"""
        # アンダースコアとハイフンを削除し、英数字のみにする
        import re
        sanitized_name = re.sub(r'[^a-zA-Z0-9]', '', database_name)
        if sanitized_name != database_name:
            logger.info(f"データベース名を '{database_name}' から '{sanitized_name}' に修正しました。")
        return sanitized_name

    def _ensure_database_exists(self):
        """データベースが存在しない場合は作成します。"""
        try:
            # まず、指定されたデータベースに直接接続を試行
            with self.driver.session(database=self.database) as session:
                # 簡単なクエリを実行してデータベースが利用可能かテスト
                session.run("RETURN 1")
                logger.info(f"データベース '{self.database}' は既に存在し、利用可能です。")
                return
        except Exception as e:
            logger.info(f"データベース '{self.database}' への接続に失敗しました: {e}")
            
        # データベースが存在しない場合、作成を試行
        try:
            # デフォルトデータベース（通常は'neo4j'）に接続してデータベース作成
            with self.driver.session(database="neo4j") as session:
                logger.info(f"データベース '{self.database}' を作成します...")
                # データベース作成（Neo4j 4.0以降）
                session.run(f"CREATE DATABASE {self.database}")
                logger.info(f"データベース '{self.database}' が作成されました。")
                
                # 作成後、少し待ってから利用可能になるまで待機
                import time
                time.sleep(2)
                
        except Exception as e:
            logger.error(f"データベース '{self.database}' の作成に失敗しました: {e}")
            logger.info("既存のデータベースを使用するか、手動でデータベースを作成してください。")
            raise

    def close(self):
        self.driver.close()

    def clear_database(self):
        """データベース内のすべてのノードとリレーションを削除します。"""
        with self.driver.session(database=self.database) as session:
            try:
                logger.warning(f"データベース '{self.database}' の全データを削除します...")
                session.run("MATCH (n) DETACH DELETE n")
                logger.info("データベースのクリアが完了しました。")
            except Exception as e:
                logger.error(f"データベースのクリア中にエラーが発生しました: {e}")
                raise

    def upload_api_data(self, api_data: dict):
        """
        API仕様書の解析結果（辞書）をNeo4jにアップロードします。
        (doc_paser/neo4j_importer.py のロジックを適応)
        """
        logger.info("API仕様データのアップロードを開始します...")
        with self.driver.session(database=self.database) as session:
            # 1. 型定義のインポート
            type_defs = api_data.get("type_definitions", [])
            if type_defs:
                session.run("""
                    UNWIND $types as type_data
                    MERGE (t:ApiType {name: type_data.name})
                    SET t.description = type_data.description
                """, types=type_defs)
                logger.info(f"{len(type_defs)}件の型定義をインポートしました。")

            # 2. APIエントリーのインポート
            api_entries = api_data.get("api_entries", [])
            for entry in api_entries:
                if entry.get("entry_type") == "function":
                    self._create_api_function(session, entry)
                elif entry.get("entry_type") == "object_definition":
                    self._create_api_object(session, entry)
        logger.info("API仕様データのアップロードが完了しました。")

    def _create_api_function(self, session, func_data):
        """API関数ノードと関連ノードを作成します。"""
        func_query = """
        MERGE (f:ApiFunction {name: $func.name})
        SET f += {
            description: $func.description,
            category: $func.category,
            notes: $func.notes,
            implementation_status: $func.implementation_status
        }
        """
        session.run(func_query, func=func_data)

        for param_data in func_data.get("params", []):
            param_query = """
            MATCH (f:ApiFunction {name: $func_name})
            MERGE (p:ApiParam {name: $param.name, parent_function: $func_name})
            SET p += {description: $param.description, is_required: $param.is_required}
            MERGE (f)-[r:HAS_PARAMETER]->(p)
            SET r.position = $param.position

            MERGE (t:ApiType {name: $param.type})
            MERGE (p)-[:HAS_TYPE]->(t)
            """
            session.run(param_query, func_name=func_data['name'], param=param_data)

        if func_data.get('returns'):
            return_query = """
            MATCH (f:ApiFunction {name: $func_name})
            MERGE (rt:ApiType {name: $return_type})
            MERGE (f)-[:RETURNS]->(rt)
            """
            session.run(return_query, func_name=func_data['name'], return_type=func_data['returns'].get('type'))

    def _create_api_object(self, session, obj_data):
        """APIオブジェクト定義ノードと関連ノードを作成します。"""
        # (実装は _create_api_function と同様のパターン)
        pass

    def upload_code_data(self, nodes: List[SyntaxNode], relations: List[SyntaxRelation]):
        """
        コード解析結果（ノードとリレーションのリスト）をNeo4jにアップロードします。
        (code_parser/treesitter_neo4j_advanced.py のロジックを適応)
        """
        logger.info("コード解析データのアップロードを開始します...")
        with self.driver.session(database=self.database) as session:
            # ノードの作成
            for node in nodes:
                properties = node.properties.copy()
                properties['id'] = node.node_id
                properties['name'] = node.name
                properties['text'] = node.text
                if node.llm_insights:
                    properties['llm_description'] = node.llm_insights.get('description', '')

                # ネストした辞書やリストをJSON文字列に変換
                for key, value in properties.items():
                    if isinstance(value, (dict, list)):
                        properties[key] = json.dumps(value, ensure_ascii=False)

                cypher = f"""
                CREATE (n:{node.node_type.value} $props)
                """
                session.run(cypher, props=properties)
            logger.info(f"{len(nodes)}個のコードノードを作成しました。")

            # リレーションの作成
            for rel in relations:
                cypher = f"""
                MATCH (source {{id: $source_id}}), (target {{id: $target_id}})
                CREATE (source)-[r:{rel.relation_type.value}]->(target)
                """
                session.run(cypher, source_id=rel.source_id, target_id=rel.target_id)
            logger.info(f"{len(relations)}個のコードリレーションを作成しました。")
        logger.info("コード解析データのアップロードが完了しました。")

    def link_graphs(self):
        """
        API仕様グラフとコード実装グラフをリンクします。
        """
        logger.info("API仕様とコード実装のリンクを開始します...")
        with self.driver.session(database=self.database) as session:
            query = """
            MATCH (api_func:ApiFunction)
            MATCH (code_func:Function)
            WHERE api_func.name = code_func.name
            MERGE (code_func)-[r:IMPLEMENTS_API]->(api_func)
            RETURN count(r) as linked_count
            """
            result = session.run(query)
            linked_count = result.single()["linked_count"]
            logger.info(f"{linked_count}件の `IMPLEMENTS_API` リンクを作成・更新しました。")
        logger.info("グラフのリンクが完了しました。")
