#!/usr/bin/env python3
"""
Tree-sitter Neo4j統合システムのテストスクリプト
"""

import os
import sys
import logging
from pathlib import Path

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_basic_parsing():
    """基本的なTree-sitter解析のテスト"""
    logger.info("=== 基本的なTree-sitter解析テスト ===")
    
    try:
        from treesitter_neo4j_advanced import TreeSitterNeo4jAdvancedBuilder
        
        # ビルダーの作成（Neo4j接続なし）
        builder = TreeSitterNeo4jAdvancedBuilder(
            "neo4j://localhost:7687",
            "neo4j",
            "password",
            enable_llm=False  # LLM無効化
        )
        
        # テストファイルの解析
        test_file = "./evoship/create_test.py"
        if os.path.exists(test_file):
            builder.analyze_file(test_file)
            
            logger.info(f"解析されたノード数: {len(builder.syntax_nodes)}")
            logger.info(f"解析されたリレーション数: {len(builder.syntax_relations)}")
            
            # ノードタイプ別の統計
            node_types = {}
            for node in builder.syntax_nodes:
                node_type = node.node_type.value
                node_types[node_type] = node_types.get(node_type, 0) + 1
            
            logger.info("ノードタイプ別統計:")
            for node_type, count in sorted(node_types.items()):
                logger.info(f"  {node_type}: {count}個")
            
            return True
        else:
            logger.error(f"テストファイルが見つかりません: {test_file}")
            return False
            
    except Exception as e:
        logger.error(f"基本的な解析テストでエラーが発生しました: {e}")
        return False

def test_neo4j_integration():
    """Neo4j統合のテスト"""
    logger.info("=== Neo4j統合テスト ===")
    
    try:
        from treesitter_neo4j_advanced import TreeSitterNeo4jAdvancedBuilder
        
        # Neo4j接続情報
        neo4j_uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        
        # ビルダーの作成
        builder = TreeSitterNeo4jAdvancedBuilder(
            neo4j_uri,
            neo4j_user,
            neo4j_password,
            database_name="treesitter_test",
            enable_llm=False  # LLM無効化
        )
        
        # テストファイルの解析
        test_file = "./evoship/create_test.py"
        if os.path.exists(test_file):
            builder.analyze_file(test_file)
            
            # Neo4jへの格納
            builder.store_to_neo4j()
            
            logger.info("Neo4j統合テストが成功しました")
            return True
        else:
            logger.error(f"テストファイルが見つかりません: {test_file}")
            return False
            
    except Exception as e:
        logger.error(f"Neo4j統合テストでエラーが発生しました: {e}")
        return False

def test_query_engine():
    """クエリエンジンのテスト"""
    logger.info("=== クエリエンジンテスト ===")
    
    try:
        from neo4j_query_engine import Neo4jQueryEngine
        
        # Neo4j接続情報
        neo4j_uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        
        # クエリエンジンの作成
        query_engine = Neo4jQueryEngine(
            neo4j_uri,
            neo4j_user,
            neo4j_password,
            database_name="treesitter_test"
        )
        
        # コードメトリクスの取得
        metrics = query_engine.find_code_metrics()
        logger.info(f"コードメトリクス: {metrics}")
        
        # 関数の検索
        functions = query_engine.find_functions_by_complexity(min_complexity=1.0)
        logger.info(f"関数数: {len(functions)}")
        
        # クラスの検索
        classes = query_engine.find_classes_with_methods()
        logger.info(f"クラス数: {len(classes)}")
        
        logger.info("クエリエンジンテストが成功しました")
        return True
        
    except Exception as e:
        logger.error(f"クエリエンジンテストでエラーが発生しました: {e}")
        return False

def test_llm_integration():
    """LLM統合のテスト"""
    logger.info("=== LLM統合テスト ===")
    
    # OpenAI APIキーの確認
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEYが設定されていません。LLMテストをスキップします。")
        return True
    
    try:
        from treesitter_neo4j_advanced import TreeSitterNeo4jAdvancedBuilder
        
        # ビルダーの作成（LLM有効）
        builder = TreeSitterNeo4jAdvancedBuilder(
            "neo4j://localhost:7687",
            "neo4j",
            "password",
            database_name="treesitter_llm_test",
            enable_llm=True
        )
        
        # テストファイルの解析
        test_file = "./evoship/create_test.py"
        if os.path.exists(test_file):
            builder.analyze_file(test_file)
            
            # LLM分析済みノードの確認
            llm_analyzed = [node for node in builder.syntax_nodes if node.llm_insights]
            logger.info(f"LLM分析済みノード数: {len(llm_analyzed)}")
            
            if llm_analyzed:
                logger.info("LLM分析例:")
                for node in llm_analyzed[:3]:  # 最初の3つを表示
                    logger.info(f"  {node.node_type.value}: {node.name}")
                    logger.info(f"    LLM分析: {node.llm_insights}")
            
            logger.info("LLM統合テストが成功しました")
            return True
        else:
            logger.error(f"テストファイルが見つかりません: {test_file}")
            return False
            
    except Exception as e:
        logger.error(f"LLM統合テストでエラーが発生しました: {e}")
        return False

def test_complexity_analysis():
    """複雑性分析のテスト"""
    logger.info("=== 複雑性分析テスト ===")
    
    try:
        from treesitter_neo4j_advanced import TreeSitterNeo4jAdvancedBuilder, CodeComplexityAnalyzer
        
        # ビルダーの作成
        builder = TreeSitterNeo4jAdvancedBuilder(
            "neo4j://localhost:7687",
            "neo4j",
            "password",
            enable_llm=False
        )
        
        # テストファイルの解析
        test_file = "./evoship/create_test.py"
        if os.path.exists(test_file):
            builder.analyze_file(test_file)
            
            # 複雑性スコアの分析
            function_nodes = [node for node in builder.syntax_nodes if node.node_type.value == "Function"]
            class_nodes = [node for node in builder.syntax_nodes if node.node_type.value == "Class"]
            
            logger.info(f"関数数: {len(function_nodes)}")
            logger.info(f"クラス数: {len(class_nodes)}")
            
            # 高複雑性の関数を表示
            high_complexity_functions = [f for f in function_nodes if f.complexity_score > 3]
            logger.info(f"高複雑性関数数 (複雑性 > 3): {len(high_complexity_functions)}")
            
            for func in high_complexity_functions:
                logger.info(f"  関数: {func.name}, 複雑性: {func.complexity_score}")
            
            # ファイルメトリクスの表示
            for file_path, metrics in builder.file_metrics.items():
                logger.info(f"ファイル: {file_path}")
                logger.info(f"  総行数: {metrics['total_lines']}")
                logger.info(f"  コード行数: {metrics['code_lines']}")
                logger.info(f"  関数数: {metrics['functions']}")
                logger.info(f"  クラス数: {metrics['classes']}")
                logger.info(f"  複雑性スコア: {metrics['complexity_score']}")
            
            logger.info("複雑性分析テストが成功しました")
            return True
        else:
            logger.error(f"テストファイルが見つかりません: {test_file}")
            return False
            
    except Exception as e:
        logger.error(f"複雑性分析テストでエラーが発生しました: {e}")
        return False

def run_all_tests():
    """すべてのテストを実行"""
    logger.info("Tree-sitter Neo4j統合システムのテストを開始します")
    
    tests = [
        ("基本的なTree-sitter解析", test_basic_parsing),
        ("複雑性分析", test_complexity_analysis),
        ("Neo4j統合", test_neo4j_integration),
        ("クエリエンジン", test_query_engine),
        ("LLM統合", test_llm_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"テスト: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            success = test_func()
            results.append((test_name, success))
            
            if success:
                logger.info(f"✅ {test_name}: 成功")
            else:
                logger.error(f"❌ {test_name}: 失敗")
                
        except Exception as e:
            logger.error(f"❌ {test_name}: エラー - {e}")
            results.append((test_name, False))
    
    # 結果の要約
    logger.info(f"\n{'='*50}")
    logger.info("テスト結果要約")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ 成功" if success else "❌ 失敗"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\n総合結果: {passed}/{total} テストが成功")
    
    if passed == total:
        logger.info("🎉 すべてのテストが成功しました！")
        return True
    else:
        logger.error("⚠️  一部のテストが失敗しました")
        return False

def main():
    """メイン関数"""
    # 環境変数の確認
    logger.info("環境変数の確認:")
    logger.info(f"NEO4J_URI: {os.getenv('NEO4J_URI', '未設定')}")
    logger.info(f"NEO4J_USER: {os.getenv('NEO4J_USER', '未設定')}")
    logger.info(f"NEO4J_PASSWORD: {'設定済み' if os.getenv('NEO4J_PASSWORD') else '未設定'}")
    logger.info(f"OPENAI_API_KEY: {'設定済み' if os.getenv('OPENAI_API_KEY') else '未設定'}")
    
    # テストファイルの確認
    test_file = "./evoship/create_test.py"
    if not os.path.exists(test_file):
        logger.error(f"テストファイルが見つかりません: {test_file}")
        logger.info("evoship/create_test.pyファイルが存在することを確認してください")
        return False
    
    # すべてのテストを実行
    success = run_all_tests()
    
    if success:
        logger.info("\n🎉 統合テストが完了しました！")
        logger.info("Tree-sitter Neo4j統合システムが正常に動作しています。")
    else:
        logger.error("\n⚠️  統合テストで問題が発生しました。")
        logger.info("エラーログを確認して問題を修正してください。")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 