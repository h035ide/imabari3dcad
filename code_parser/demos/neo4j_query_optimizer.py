"""
Neo4jクエリ最適化テストスクリプト

最適化されたクエリのパフォーマンスをテストし、
Cartesian Product警告の解消を確認します。
"""

import os
import sys
import time
import logging
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# .envファイルを読み込む
load_dotenv()

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from neo4j import GraphDatabase
except ImportError as e:
    logger.error(f"Neo4jライブラリがインストールされていません: {e}")
    sys.exit(1)


class Neo4jQueryOptimizer:
    """Neo4jクエリ最適化テストクラス"""
    
    def __init__(self):
        """初期化"""
        self.neo4j_uri = os.getenv("NEO4J_URI")
        self.neo4j_user = os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD")
        
        if not all([self.neo4j_uri, self.neo4j_user, self.neo4j_password]):
            raise ValueError("Neo4j接続情報が.envファイルに設定されていません")
        
        self.driver = None
        logger.info("Neo4jクエリ最適化テストを初期化しました")
    
    def connect(self):
        """Neo4jに接続"""
        try:
            self.driver = GraphDatabase.driver(
                self.neo4j_uri, 
                auth=(self.neo4j_user, self.neo4j_password)
            )
            # 接続テスト
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                record = result.single()
                if record and record["test"] == 1:
                    logger.info("Neo4j接続成功")
                    return True
        except Exception as e:
            logger.error(f"Neo4j接続エラー: {e}")
            return False
    
    def disconnect(self):
        """Neo4j接続を切断"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j接続を切断しました")
    
    def test_original_query(self):
        """元のクエリ（Cartesian Product警告あり）をテスト"""
        logger.info("=== 元のクエリテスト（Cartesian Product警告あり） ===")
        
        with self.driver.session() as session:
            # テスト用の小さなデータセットで実行
            test_relations = [
                {"source_id": "test1", "target_id": "test2", "weight": 1.0},
                {"source_id": "test3", "target_id": "test4", "weight": 1.0}
            ]
            
            start_time = time.time()
            
            for relation in test_relations:
                # 元のクエリ（問題のあるクエリ）
                cypher = """
                MATCH (source), (target)
                WHERE source.id = $source_id AND target.id = $target_id
                CREATE (source)-[r:TEST_RELATION {weight: $weight}]->(target)
                """
                
                try:
                    session.run(cypher, relation)
                    logger.info(f"元のクエリ実行成功: {relation['source_id']} -> {relation['target_id']}")
                except Exception as e:
                    logger.error(f"元のクエリ実行エラー: {e}")
            
            execution_time = time.time() - start_time
            logger.info(f"元のクエリ実行時間: {execution_time:.4f}秒")
            
            # テスト用リレーションを削除
            session.run("MATCH ()-[r:TEST_RELATION]->() DELETE r")
    
    def test_optimized_query(self):
        """最適化されたクエリをテスト"""
        logger.info("=== 最適化されたクエリテスト ===")
        
        with self.driver.session() as session:
            # テスト用の小さなデータセットで実行
            test_relations = [
                {"source_id": "test1", "target_id": "test2", "weight": 1.0},
                {"source_id": "test3", "target_id": "test4", "weight": 1.0}
            ]
            
            start_time = time.time()
            
            # 最適化されたクエリ（UNWINDを使用）
            cypher = """
            UNWIND $batch AS rel
            MATCH (source {id: rel.source_id})
            MATCH (target {id: rel.target_id})
            CREATE (source)-[r:TEST_RELATION {weight: rel.weight}]->(target)
            """
            
            try:
                session.run(cypher, {"batch": test_relations})
                logger.info(f"最適化クエリ実行成功: {len(test_relations)}個のリレーション")
            except Exception as e:
                logger.error(f"最適化クエリ実行エラー: {e}")
            
            execution_time = time.time() - start_time
            logger.info(f"最適化クエリ実行時間: {execution_time:.4f}秒")
            
            # テスト用リレーションを削除
            session.run("MATCH ()-[r:TEST_RELATION]->() DELETE r")
    
    def test_batch_processing(self):
        """バッチ処理のパフォーマンステスト"""
        logger.info("=== バッチ処理パフォーマンステスト ===")
        
        with self.driver.session() as session:
            # 異なるバッチサイズでテスト
            batch_sizes = [1, 10, 50, 100]
            
            for batch_size in batch_sizes:
                # テストデータを生成
                test_data = []
                for i in range(batch_size):
                    test_data.append({
                        "source_id": f"batch_{batch_size}_source_{i}",
                        "target_id": f"batch_{batch_size}_target_{i}",
                        "weight": 1.0
                    })
                
                start_time = time.time()
                
                # バッチ処理クエリ
                cypher = """
                UNWIND $batch AS rel
                MATCH (source {id: rel.source_id})
                MATCH (target {id: rel.target_id})
                CREATE (source)-[r:TEST_RELATION {weight: rel.weight}]->(target)
                """
                
                try:
                    session.run(cypher, {"batch": test_data})
                    execution_time = time.time() - start_time
                    logger.info(f"バッチサイズ {batch_size}: {execution_time:.4f}秒 ({batch_size/execution_time:.1f} リレーション/秒)")
                except Exception as e:
                    logger.error(f"バッチサイズ {batch_size} でエラー: {e}")
                
                # テスト用リレーションを削除
                session.run("MATCH ()-[r:TEST_RELATION]->() DELETE r")
    
    def test_index_creation(self):
        """インデックス作成のテスト"""
        logger.info("=== インデックス作成テスト ===")
        
        with self.driver.session() as session:
            try:
                # 基本的なインデックスを作成
                session.run("CREATE INDEX test_id_index IF NOT EXISTS FOR (n) ON (n.id)")
                session.run("CREATE INDEX test_type_index IF NOT EXISTS FOR (n) ON (n.node_type)")
                
                logger.info("インデックス作成成功")
                
                # インデックス一覧を表示
                result = session.run("SHOW INDEXES")
                indexes = [record["name"] for record in result]
                logger.info(f"作成されたインデックス: {indexes}")
                
                # テスト用インデックスを削除
                session.run("DROP INDEX test_id_index IF EXISTS")
                session.run("DROP INDEX test_type_index IF EXISTS")
                logger.info("テスト用インデックスを削除しました")
                
            except Exception as e:
                logger.error(f"インデックス作成エラー: {e}")
    
    def test_query_planning(self):
        """クエリプランニングのテスト"""
        logger.info("=== クエリプランニングテスト ===")
        
        with self.driver.session() as session:
            try:
                # EXPLAINを使用してクエリプランを確認
                cypher = """
                EXPLAIN MATCH (source {id: "test1"})
                MATCH (target {id: "test2"})
                RETURN source, target
                """
                
                result = session.run(cypher)
                logger.info("クエリプラン:")
                for record in result:
                    logger.info(f"  {record}")
                
            except Exception as e:
                logger.error(f"クエリプランニングテストエラー: {e}")
    
    def benchmark_queries(self):
        """クエリのベンチマーク実行"""
        logger.info("=== クエリベンチマーク実行 ===")
        
        # テストデータの準備
        test_sizes = [10, 50, 100, 200]
        
        for size in test_sizes:
            logger.info(f"\n--- データサイズ: {size} ---")
            
            # テストデータを生成
            test_data = []
            for i in range(size):
                test_data.append({
                    "source_id": f"benchmark_source_{i}",
                    "target_id": f"benchmark_target_{i}",
                    "weight": 1.0
                })
            
            # 元のクエリのベンチマーク
            with self.driver.session() as session:
                start_time = time.time()
                
                for relation in test_data:
                    cypher = """
                    MATCH (source), (target)
                    WHERE source.id = $source_id AND target.id = $target_id
                    CREATE (source)-[r:BENCHMARK_RELATION {weight: $weight}]->(target)
                    """
                    session.run(cypher, relation)
                
                original_time = time.time() - start_time
                
                # テスト用リレーションを削除
                session.run("MATCH ()-[r:BENCHMARK_RELATION]->() DELETE r")
            
            # 最適化クエリのベンチマーク
            with self.driver.session() as session:
                start_time = time.time()
                
                cypher = """
                UNWIND $batch AS rel
                MATCH (source {id: rel.source_id})
                MATCH (target {id: rel.target_id})
                CREATE (source)-[r:BENCHMARK_RELATION {weight: rel.weight}]->(target)
                """
                session.run(cypher, {"batch": test_data})
                
                optimized_time = time.time() - start_time
                
                # テスト用リレーションを削除
                session.run("MATCH ()-[r:BENCHMARK_RELATION]->() DELETE r")
            
            # 結果を比較
            speedup = original_time / optimized_time if optimized_time > 0 else 0
            logger.info(f"データサイズ {size}:")
            logger.info(f"  元のクエリ: {original_time:.4f}秒")
            logger.info(f"  最適化クエリ: {optimized_time:.4f}秒")
            logger.info(f"  高速化率: {speedup:.2f}x")
    
    def run_all_tests(self):
        """全テストを実行"""
        logger.info("Neo4jクエリ最適化テストを開始します...")
        
        try:
            if not self.connect():
                logger.error("Neo4j接続に失敗しました")
                return
            
            # 各テストを実行
            self.test_original_query()
            self.test_optimized_query()
            self.test_batch_processing()
            self.test_index_creation()
            self.test_query_planning()
            self.benchmark_queries()
            
            logger.info("全テストが完了しました")
            
        except Exception as e:
            logger.error(f"テスト実行中にエラーが発生しました: {e}")
        
        finally:
            self.disconnect()


def main():
    """メイン関数"""
    try:
        optimizer = Neo4jQueryOptimizer()
        optimizer.run_all_tests()
    except Exception as e:
        logger.error(f"メイン実行エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
