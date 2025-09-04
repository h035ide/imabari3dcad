"""
RAG検索エンジン - 統合されたコード検索システム

ベクトル検索エンジンとコード抽出器を統合し、
独自APIを活用したPythonコード生成のための高度な検索機能を提供します。
"""

import time
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

from vector_search import VectorSearchEngine, CodeInfo
from code_extractor import CodeExtractor


class RAGSearchEngine:
    """
    RAG（Retrieval-Augmented Generation）検索エンジン
    
    コード抽出とベクトル検索を統合し、
    自然言語クエリに基づいてPythonコードを検索できます。
    """
    
    def __init__(self, 
                 persist_directory: str = "./rag_vector_store",
                 collection_name: str = "python_code_rag"):
        """
        RAG検索エンジンを初期化
        
        Args:
            persist_directory: ベクトルデータベースの保存先
            collection_name: コレクション名
        """
        print("RAG検索エンジンを初期化中...")
        
        # ベクトル検索エンジンの初期化
        self.vector_engine = VectorSearchEngine(
            persist_directory=persist_directory,
            collection_name=collection_name
        )
        
        # コード抽出器の初期化
        self.code_extractor = CodeExtractor()
        
        # 統計情報
        self.stats = {
            "indexed_files": 0,
            "indexed_functions": 0,
            "indexed_classes": 0,
            "indexed_methods": 0,
            "last_index_time": None
        }
        
        print("RAG検索エンジンの初期化が完了しました")
    
    def index_file(self, file_path: str) -> Dict[str, int]:
        """
        単一ファイルをインデックス化
        
        Args:
            file_path: インデックス化するPythonファイルのパス
            
        Returns:
            Dict[str, int]: インデックス化の結果統計
        """
        start_time = time.time()
        
        print(f"ファイルをインデックス化中: {file_path}")
        
        # コード情報を抽出
        code_infos = self.code_extractor.extract_from_file(file_path)
        
        # ベクトルデータベースに追加
        success_count = 0
        for code_info in code_infos:
            if self.vector_engine.add_code_info(code_info):
                success_count += 1
                
                # 統計情報を更新
                if code_info.type == "function":
                    self.stats["indexed_functions"] += 1
                elif code_info.type == "class":
                    self.stats["indexed_classes"] += 1
                elif code_info.type == "method":
                    self.stats["indexed_methods"] += 1
        
        # ファイルカウントを更新
        if success_count > 0:
            self.stats["indexed_files"] += 1
        
        self.stats["last_index_time"] = time.time()
        
        elapsed_time = time.time() - start_time
        result = {
            "total_extracted": len(code_infos),
            "successfully_indexed": success_count,
            "elapsed_time": elapsed_time
        }
        
        print(f"インデックス化完了: {success_count}/{len(code_infos)}個 ({elapsed_time:.2f}秒)")
        return result
    
    def index_directory(self, 
                       directory_path: str, 
                       recursive: bool = True,
                       exclude_patterns: List[str] = None) -> Dict[str, Any]:
        """
        ディレクトリを再帰的にインデックス化
        
        Args:
            directory_path: インデックス化するディレクトリのパス
            recursive: 再帰的に検索するかどうか
            exclude_patterns: 除外するパターンのリスト
            
        Returns:
            Dict[str, Any]: インデックス化の結果統計
        """
        start_time = time.time()
        
        print(f"ディレクトリをインデックス化中: {directory_path}")
        
        # コード情報を一括抽出
        code_infos = self.code_extractor.extract_from_directory(
            directory_path, recursive, exclude_patterns
        )
        
        # ベクトルデータベースに一括追加
        success_count = 0
        file_count = 0
        current_file = ""
        
        for code_info in code_infos:
            # ファイルが変わったときのカウント
            if code_info.file_path != current_file:
                current_file = code_info.file_path
                file_count += 1
            
            if self.vector_engine.add_code_info(code_info):
                success_count += 1
                
                # 統計情報を更新
                if code_info.type == "function":
                    self.stats["indexed_functions"] += 1
                elif code_info.type == "class":
                    self.stats["indexed_classes"] += 1
                elif code_info.type == "method":
                    self.stats["indexed_methods"] += 1
        
        # ファイルカウントを更新
        self.stats["indexed_files"] += file_count
        self.stats["last_index_time"] = time.time()
        
        elapsed_time = time.time() - start_time
        result = {
            "directory": directory_path,
            "files_processed": file_count,
            "total_extracted": len(code_infos),
            "successfully_indexed": success_count,
            "elapsed_time": elapsed_time,
            "items_per_second": len(code_infos) / elapsed_time if elapsed_time > 0 else 0
        }
        
        print(f"ディレクトリインデックス化完了: {success_count}個の要素を{elapsed_time:.2f}秒で処理")
        return result
    
    def search(self, 
              query: str, 
              search_type: str = "semantic",
              top_k: int = 5,
              filters: Optional[Dict[str, Any]] = None,
              include_content: bool = True) -> List[Dict[str, Any]]:
        """
        コードを検索
        
        Args:
            query: 検索クエリ（自然言語）
            search_type: 検索タイプ ("semantic", "type", "name")
            top_k: 取得する結果数
            filters: フィルター条件
            include_content: コード内容を含めるかどうか
            
        Returns:
            List[Dict[str, Any]]: 検索結果
        """
        start_time = time.time()
        
        print(f"検索実行: '{query}' (タイプ: {search_type})")
        
        if search_type == "semantic":
            results = self.vector_engine.search_similar_functions(
                query, top_k, filters=filters
            )
        elif search_type == "type":
            # タイプで検索（クエリをタイプとして使用）
            results = self.vector_engine.search_by_type(query, top_k)
        else:
            # デフォルトは意味的検索
            results = self.vector_engine.search_similar_functions(
                query, top_k, filters=filters
            )
        
        # 結果の後処理
        processed_results = []
        for result in results:
            processed_result = self._process_search_result(result, include_content)
            processed_results.append(processed_result)
        
        elapsed_time = time.time() - start_time
        print(f"検索完了: {len(processed_results)}件の結果 ({elapsed_time:.3f}秒)")
        
        return processed_results
    
    def search_by_functionality(self, 
                              description: str, 
                              top_k: int = 5) -> List[Dict[str, Any]]:
        """
        機能説明による検索
        
        Args:
            description: 機能の説明
            top_k: 取得する結果数
            
        Returns:
            List[Dict[str, Any]]: 検索結果
        """
        # 機能説明を使って意味的検索を実行
        enhanced_query = f"機能: {description} 目的: {description} 処理内容: {description}"
        return self.search(enhanced_query, "semantic", top_k)
    
    def search_by_input_output(self, 
                             input_type: str = "", 
                             output_type: str = "",
                             top_k: int = 5) -> List[Dict[str, Any]]:
        """
        入力・出力タイプによる検索
        
        Args:
            input_type: 入力の型
            output_type: 出力の型
            top_k: 取得する結果数
            
        Returns:
            List[Dict[str, Any]]: 検索結果
        """
        query_parts = []
        if input_type:
            query_parts.append(f"入力: {input_type}")
        if output_type:
            query_parts.append(f"出力: {output_type} 戻り値: {output_type}")
        
        query = " ".join(query_parts)
        return self.search(query, "semantic", top_k)
    
    def get_similar_implementations(self, 
                                  code_snippet: str, 
                                  top_k: int = 3) -> List[Dict[str, Any]]:
        """
        類似実装を検索
        
        Args:
            code_snippet: 比較対象のコードスニペット
            top_k: 取得する結果数
            
        Returns:
            List[Dict[str, Any]]: 類似実装のリスト
        """
        # コードスニペットから機能を推測してクエリを作成
        query = f"類似コード: {code_snippet[:200]}"  # 最初の200文字のみ使用
        return self.search(query, "semantic", top_k)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        システム統計情報を取得
        
        Returns:
            Dict[str, Any]: 統計情報
        """
        vector_stats = self.vector_engine.get_collection_stats()
        
        combined_stats = {
            **self.stats,
            "vector_database": vector_stats,
            "total_indexed_items": (
                self.stats["indexed_functions"] + 
                self.stats["indexed_classes"] + 
                self.stats["indexed_methods"]
            )
        }
        
        return combined_stats
    
    def clear_index(self):
        """インデックスをクリア"""
        print("インデックスをクリア中...")
        
        # 新しいコレクションを作成して既存のものを置き換える
        # 注意: ChromaDBではコレクションの完全クリアは制限される場合があります
        self.vector_engine.clear_cache()
        
        # 統計情報をリセット
        self.stats = {
            "indexed_files": 0,
            "indexed_functions": 0,
            "indexed_classes": 0,
            "indexed_methods": 0,
            "last_index_time": None
        }
        
        print("インデックスのクリアが完了しました")
    
    def _process_search_result(self, result: Dict[str, Any], include_content: bool) -> Dict[str, Any]:
        """検索結果を後処理"""
        processed = {
            "id": result.get("id", ""),
            "name": result.get("name", ""),
            "type": result.get("type", ""),
            "file_path": result.get("file_path", ""),
            "description": result.get("description", ""),
            "parameters": result.get("parameters", "").split(",") if result.get("parameters") else [],
            "returns": result.get("returns", ""),
        }
        
        # 類似度情報があれば追加
        if "similarity" in result:
            processed["similarity"] = result["similarity"]
        
        # コンテンツを含めるかどうか
        if include_content and "content" in result:
            processed["content"] = result["content"]
        
        return processed


def demo_rag_system():
    """RAGシステムのデモ"""
    print("=== RAG検索システム デモ ===")
    
    # RAGエンジンの初期化
    rag_engine = RAGSearchEngine()
    
    # 現在のディレクトリにサンプルファイルがあるかチェック
    current_dir = Path(".")
    python_files = list(current_dir.glob("*.py"))
    
    if python_files:
        print(f"\n現在のディレクトリの.pyファイルをインデックス化: {len(python_files)}ファイル")
        
        # 最初の数ファイルをインデックス化（デモ用）
        for py_file in python_files[:3]:  # 最初の3ファイルのみ
            result = rag_engine.index_file(str(py_file))
            print(f"  {py_file.name}: {result['successfully_indexed']}個の要素をインデックス化")
    
    # 検索デモ
    print(f"\n=== 検索デモ ===")
    
    search_queries = [
        "ファイルを読み込む関数",
        "データを処理するクラス",
        "文字列を返す",
        "計算機能"
    ]
    
    for query in search_queries:
        print(f"\n検索クエリ: '{query}'")
        results = rag_engine.search(query, top_k=3, include_content=False)
        
        if results:
            for i, result in enumerate(results, 1):
                similarity_info = f" (類似度: {result['similarity']:.3f})" if 'similarity' in result else ""
                print(f"  {i}. {result['name']} ({result['type']}){similarity_info}")
                if result['description']:
                    print(f"     説明: {result['description'][:100]}...")
        else:
            print("  結果が見つかりませんでした")
    
    # 統計情報の表示
    print(f"\n=== 統計情報 ===")
    stats = rag_engine.get_statistics()
    print(f"インデックス化ファイル数: {stats['indexed_files']}")
    print(f"関数: {stats['indexed_functions']}")
    print(f"クラス: {stats['indexed_classes']}")
    print(f"メソッド: {stats['indexed_methods']}")
    print(f"総要素数: {stats['total_indexed_items']}")


if __name__ == "__main__":
    demo_rag_system()