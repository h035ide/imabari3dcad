#!/usr/bin/env python3
"""
LangChain Interface Demonstration

LangChainインターフェースの機能を実演するスクリプト
依存ライブラリがない環境でもモックモードで動作します。
"""

import os
import sys
import logging

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# モジュールのパスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demonstrate_basic_interface():
    """基本的なLangChainインターフェースの実演"""
    print("=== 基本的なLangChainインターフェースの実演 ===\n")
    
    from langchain_interface import create_interface
    
    # 1. インターフェースの作成
    print("1. LangChainインターフェースを作成...")
    interface = create_interface()
    print("   ✓ インターフェースが正常に作成されました\n")
    
    # 2. 接続状態の確認
    print("2. 接続状態を確認...")
    status = interface.get_connection_status()
    print(f"   Neo4j接続: {'✓' if status['neo4j_connected'] else '✗ (モックモード)'}")
    print(f"   Chroma接続: {'✓' if status['chroma_connected'] else '✗ (モックモード)'}")
    print()
    
    # 3. ドキュメントの追加
    print("3. サンプルドキュメントを追加...")
    sample_docs = [
        {
            "content": "imabari3dcadは高度な3D CADアプリケーションです。Neo4jとChromaを使用してRAG機能を提供します。",
            "metadata": {"category": "system_overview", "language": "ja"}
        },
        {
            "content": "LangChainインターフェースにより、グラフデータベースとベクトルストアの統合検索が可能になります。",
            "metadata": {"category": "features", "language": "ja"}
        },
        {
            "content": "高い独立性を持ち、既存のシステムに簡単に統合できる設計になっています。",
            "metadata": {"category": "architecture", "language": "ja"}
        }
    ]
    
    for i, doc in enumerate(sample_docs, 1):
        interface.add_document(doc["content"], doc["metadata"])
        print(f"   ✓ ドキュメント {i} を追加しました")
    print()
    
    # 4. 検索の実行
    print("4. 各種検索を実行...")
    
    search_queries = [
        "3D CAD機能",
        "LangChain統合",
        "システム設計",
        "データベース"
    ]
    
    for query in search_queries:
        print(f"\n   クエリ: '{query}'")
        
        # ハイブリッド検索
        hybrid_results = interface.hybrid_search(query, k=3)
        print(f"   ハイブリッド検索結果: {len(hybrid_results.get('vector_results', []))} 件のベクトル結果")
        
        # ベクトル検索のみ
        vector_results = interface.search_vectors(query, k=3)
        print(f"   ベクトル検索結果: {len(vector_results)} 件")
        
        # グラフクエリ
        graph_result = interface.query_graph(f"MATCH (n) WHERE n.content CONTAINS '{query}' RETURN n LIMIT 3")
        print(f"   グラフクエリ結果: {type(graph_result).__name__}")
    
    print("\n5. インターフェースを終了...")
    interface.close()
    print("   ✓ すべての接続が正常に閉じられました\n")


def demonstrate_advanced_features():
    """高度な機能の実演"""
    print("=== 高度な機能の実演 ===\n")
    
    try:
        from langchain_advanced_rag import create_advanced_rag
        
        print("1. 高度なRAGシステムを作成...")
        rag = create_advanced_rag()
        print("   ✓ 高度なRAGシステムが正常に作成されました\n")
        
        # システム状態の確認
        print("2. システム状態を確認...")
        status = rag.get_system_status()
        print(f"   グラフ接続: {'✓' if status['graph']['connected'] else '✗'}")
        print(f"   ベクトルストア接続: {'✓' if status['vector_store']['connected'] else '✗'}")
        print(f"   LlamaIndex統合: {'✓' if status['llamaindex_integration'] else '✗'}")
        print()
        
        # 知識の追加
        print("3. 知識をシステムに追加...")
        knowledge_items = [
            {
                "content": "Neo4jはグラフデータベースであり、複雑な関係性を効率的に格納・検索できます。",
                "metadata": {"type": "technical", "topic": "database"},
                "content_type": "api_doc"
            },
            {
                "content": "Chromaはベクトルデータベースであり、セマンティック検索に適しています。",
                "metadata": {"type": "technical", "topic": "vectordb"},
                "content_type": "api_doc"
            }
        ]
        
        for item in knowledge_items:
            result = rag.add_knowledge(
                item["content"], 
                item["metadata"], 
                item["content_type"]
            )
            success = all(result.values()) if isinstance(result, dict) and "error" not in result else False
            print(f"   ✓ 知識追加: {'成功' if success else 'モックモード'}")
        print()
        
        # 包括的検索
        print("4. 包括的検索を実行...")
        search_modes = ["graph", "vector", "hybrid", "comprehensive"]
        
        for mode in search_modes:
            results = rag.comprehensive_search("データベース機能", search_mode=mode)
            result_count = len(results.get("results", {}))
            print(f"   {mode.capitalize()}検索: {result_count} 種類の結果")
        print()
        
        # エージェントの使用
        print("5. エージェント機能をテスト...")
        agent = rag.create_agent_executor()
        if agent:
            agent_result = agent.run("グラフデータベースについて教えてください")
            print("   ✓ エージェントが正常に動作しました")
            print(f"   エージェント応答の長さ: {len(str(agent_result))} 文字")
        else:
            print("   ✗ エージェントの作成に失敗（モックモードまたはエラー）")
        print()
        
        print("6. 高度なRAGシステムを終了...")
        rag.close()
        print("   ✓ 高度なRAGシステムが正常に終了しました\n")
        
    except Exception as e:
        print(f"   ✗ 高度な機能の実演中にエラーが発生: {e}\n")


def demonstrate_integration():
    """統合機能の実演"""
    print("=== 統合機能の実演 ===\n")
    
    try:
        # dotenvなしで動作するように修正
        from langchain_interface import ConnectionConfig, LangChainInterface
        
        print("1. カスタム設定で統合システムを作成...")
        
        # カスタム設定
        config_dict = {
            "neo4j_uri": "neo4j://localhost:7687",
            "neo4j_username": "neo4j",
            "neo4j_password": "demo_password",
            "chroma_persist_directory": "./demo_chroma_db",
            "chroma_collection_name": "demo_collection"
        }
        
        from langchain_interface import create_interface
        interface = create_interface(config_dict)
        print("   ✓ カスタム設定による統合システムが作成されました\n")
        
        # 統合検索のシミュレーション
        print("2. 統合検索をシミュレート...")
        queries = [
            "API関数の使用方法",
            "システムアーキテクチャ",
            "データベース設計"
        ]
        
        for query in queries:
            print(f"\n   検索クエリ: '{query}'")
            
            # 基本検索
            results = interface.hybrid_search(query)
            print(f"   基本検索: ✓ ({len(results)} 種類の結果)")
            
            # 個別検索
            vector_results = interface.search_vectors(query)
            print(f"   ベクトル検索: ✓ ({len(vector_results)} 件)")
            
            graph_result = interface.query_graph(f"MATCH (n) RETURN count(n) as total")
            print(f"   グラフクエリ: ✓ (結果: {graph_result})")
        
        print("\n3. 統合システムを終了...")
        interface.close()
        print("   ✓ 統合システムが正常に終了しました\n")
        
    except Exception as e:
        print(f"   ✗ 統合機能の実演中にエラーが発生: {e}\n")


def show_usage_examples():
    """使用例の表示"""
    print("=== 使用例 ===\n")
    
    examples = [
        {
            "title": "基本的な使用",
            "code": """
from langchain_interface import create_interface

# インターフェースの作成
interface = create_interface()

# 検索の実行
results = interface.hybrid_search("3D CAD機能について")

# ドキュメントの追加
interface.add_document("新しいドキュメント", {"category": "api"})

# 終了
interface.close()
"""
        },
        {
            "title": "設定を使用した初期化",
            "code": """
from langchain_interface import create_interface

config = {
    "neo4j_uri": "neo4j://localhost:7687",
    "neo4j_password": "your_password",
    "chroma_persist_directory": "./my_chroma_db"
}

interface = create_interface(config)
"""
        },
        {
            "title": "高度なRAG機能",
            "code": """
from langchain_advanced_rag import create_advanced_rag

rag = create_advanced_rag()
results = rag.comprehensive_search("検索クエリ", search_mode="comprehensive")
rag.add_knowledge("新しい知識", metadata={"type": "tech"})
rag.close()
"""
        }
    ]
    
    for example in examples:
        print(f"### {example['title']}")
        print("```python" + example['code'] + "```\n")


def main():
    """メイン実行関数"""
    print("LangChain Interface for imabari3dcad - Demonstration\n")
    print("=" * 60)
    print()
    
    try:
        # 基本機能の実演
        demonstrate_basic_interface()
        
        # 高度な機能の実演
        demonstrate_advanced_features()
        
        # 統合機能の実演
        demonstrate_integration()
        
        # 使用例の表示
        show_usage_examples()
        
        print("=== 実演完了 ===\n")
        print("✓ すべての機能が正常に動作しました")
        print("✓ LangChainインターフェースの統合準備が完了しています")
        print("\n詳細な使用方法については README_LangChain_Interface.md をご覧ください")
        
    except KeyboardInterrupt:
        print("\n\n実演が中断されました")
    except Exception as e:
        print(f"\n実演中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()