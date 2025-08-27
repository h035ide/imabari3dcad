"""
ベクトル検索エンジン - ChromaDBを使用したシンプルな実装

独自APIを活用したPythonコード生成のためのRAGシステムの一部として、
関数やクラスの意味的検索を提供します。
"""

import os
import time
import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

try:
    import chromadb
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    print(f"必要なライブラリがインストールされていません: {e}")
    print("以下のコマンドでインストールしてください:")
    print("pip install chromadb sentence-transformers")
    raise


@dataclass
class CodeInfo:
    """コード情報を格納するデータクラス"""
    id: str
    name: str
    content: str
    type: str  # "function", "class", "method"
    file_path: str
    description: str = ""
    parameters: List[str] = None
    returns: str = ""
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []


class VectorSearchEngine:
    """
    シンプルなベクトル検索エンジン
    
    ChromaDBを使用して、Pythonコード（関数・クラス）の意味的検索を提供します。
    """
    
    def __init__(self, 
                 persist_directory: str = "./vector_store", 
                 collection_name: str = "code_functions",
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        ベクトル検索エンジンを初期化
        
        Args:
            persist_directory: データ永続化ディレクトリ
            collection_name: コレクション名
            embedding_model: 埋め込みモデル名
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # 埋め込みモデルの初期化
        print(f"埋め込みモデル '{embedding_model}' を読み込み中...")
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # ChromaDBクライアントの初期化
        os.makedirs(persist_directory, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # コレクションの作成または取得
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={
                "hnsw:space": "cosine",
                "description": "Pythonコードの意味的検索用コレクション"
            }
        )
        
        # パフォーマンス記録用
        self.performance_metrics = {}
        self.query_cache = {}
        self.cache_ttl = 3600  # 1時間
        
        print(f"ベクトル検索エンジンが初期化されました。コレクション: {collection_name}")
    
    def add_code_info(self, code_info: CodeInfo) -> bool:
        """
        コード情報をベクトルデータベースに追加
        
        Args:
            code_info: 追加するコード情報
            
        Returns:
            bool: 追加が成功したかどうか
        """
        try:
            start_time = time.time()
            
            # テキスト情報の作成（埋め込み用）
            text_for_embedding = self._create_embedding_text(code_info)
            
            # ベクトル化
            embedding = self.embedding_model.encode(text_for_embedding).tolist()
            
            # メタデータの作成
            metadata = {
                "name": code_info.name,
                "type": code_info.type,
                "file_path": code_info.file_path,
                "description": code_info.description,
                "parameters": ",".join(code_info.parameters),
                "returns": code_info.returns,
                "content_length": len(code_info.content)
            }
            
            # ChromaDBに追加
            self.collection.add(
                embeddings=[embedding],
                metadatas=[metadata],
                documents=[code_info.content],
                ids=[code_info.id]
            )
            
            # パフォーマンス記録
            add_time = time.time() - start_time
            self.performance_metrics[f"add_{code_info.id}"] = add_time
            
            print(f"コード情報を追加しました: {code_info.name} ({add_time:.3f}秒)")
            return True
            
        except Exception as e:
            print(f"コード情報の追加に失敗しました: {e}")
            return False
    
    def search_similar_functions(self, 
                               query: str, 
                               top_k: int = 5,
                               similarity_threshold: float = 0.7,
                               filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        類似関数を検索
        
        Args:
            query: 検索クエリ（自然言語）
            top_k: 取得する結果数
            similarity_threshold: 類似度の閾値
            filters: メタデータフィルター
            
        Returns:
            List[Dict]: 検索結果のリスト
        """
        start_time = time.time()
        
        # キャッシュチェック
        cache_key = self._create_cache_key(query, top_k, filters)
        if cache_key in self.query_cache:
            cache_time, cached_results = self.query_cache[cache_key]
            if time.time() - cache_time < self.cache_ttl:
                print(f"キャッシュから結果を取得: {query}")
                return cached_results
        
        try:
            # クエリをベクトル化
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # ChromaDBで検索
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k * 2,  # フィルタリング用に多めに取得
                where=filters
            )
            
            # 結果の整形
            formatted_results = self._format_search_results(results, similarity_threshold)
            
            # top_kに制限
            formatted_results = formatted_results[:top_k]
            
            # キャッシュに保存
            self.query_cache[cache_key] = (time.time(), formatted_results)
            
            # パフォーマンス記録
            search_time = time.time() - start_time
            self.performance_metrics[f"search_{top_k}"] = search_time
            
            print(f"検索完了: {len(formatted_results)}件の結果 ({search_time:.3f}秒)")
            return formatted_results
            
        except Exception as e:
            print(f"検索に失敗しました: {e}")
            return []
    
    def search_by_type(self, code_type: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        コードタイプで検索
        
        Args:
            code_type: コードタイプ ("function", "class", "method")
            top_k: 取得する結果数
            
        Returns:
            List[Dict]: 検索結果のリスト
        """
        try:
            results = self.collection.get(
                where={"type": code_type},
                limit=top_k
            )
            
            return self._format_get_results(results)
            
        except Exception as e:
            print(f"タイプ検索に失敗しました: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        コレクションの統計情報を取得
        
        Returns:
            Dict: 統計情報
        """
        try:
            count = self.collection.count()
            
            # タイプ別の件数を取得
            type_counts = {}
            for code_type in ["function", "class", "method"]:
                try:
                    results = self.collection.get(where={"type": code_type})
                    type_counts[code_type] = len(results['ids']) if results['ids'] else 0
                except:
                    type_counts[code_type] = 0
            
            return {
                "total_count": count,
                "type_distribution": type_counts,
                "cache_size": len(self.query_cache),
                "performance_operations": len(self.performance_metrics)
            }
            
        except Exception as e:
            print(f"統計情報の取得に失敗しました: {e}")
            return {}
    
    def clear_cache(self):
        """クエリキャッシュをクリア"""
        self.query_cache.clear()
        print("キャッシュをクリアしました")
    
    def _create_embedding_text(self, code_info: CodeInfo) -> str:
        """埋め込み用のテキストを作成"""
        parts = [
            f"名前: {code_info.name}",
            f"種類: {code_info.type}",
        ]
        
        if code_info.description:
            parts.append(f"説明: {code_info.description}")
        
        if code_info.parameters:
            parts.append(f"パラメータ: {', '.join(code_info.parameters)}")
        
        if code_info.returns:
            parts.append(f"戻り値: {code_info.returns}")
        
        # コード内容（最初の200文字のみ）
        content_preview = code_info.content[:200]
        parts.append(f"コード: {content_preview}")
        
        return " ".join(parts)
    
    def _create_cache_key(self, query: str, top_k: int, filters: Optional[Dict[str, Any]]) -> str:
        """キャッシュキーを作成"""
        key_data = f"{query}_{top_k}_{str(filters)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _format_search_results(self, results: Dict[str, Any], similarity_threshold: float) -> List[Dict[str, Any]]:
        """検索結果を整形"""
        formatted_results = []
        
        if not results['distances'] or not results['distances'][0]:
            return formatted_results
        
        for i, distance in enumerate(results['distances'][0]):
            similarity = 1 - distance  # コサイン距離を類似度に変換
            
            if similarity >= similarity_threshold:
                result_data = {
                    'id': results['ids'][0][i],
                    'similarity': similarity,
                    'distance': distance,
                    'content': results['documents'][0][i] if results['documents'] else "",
                }
                
                # メタデータを追加
                if results['metadatas'] and results['metadatas'][0]:
                    metadata = results['metadatas'][0][i]
                    result_data.update(metadata)
                
                formatted_results.append(result_data)
        
        # 類似度でソート
        formatted_results.sort(key=lambda x: x['similarity'], reverse=True)
        return formatted_results
    
    def _format_get_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """get結果を整形"""
        formatted_results = []
        
        if not results['ids']:
            return formatted_results
        
        for i, result_id in enumerate(results['ids']):
            result_data = {
                'id': result_id,
                'content': results['documents'][i] if results['documents'] else "",
            }
            
            # メタデータを追加
            if results['metadatas'] and i < len(results['metadatas']):
                metadata = results['metadatas'][i]
                result_data.update(metadata)
            
            formatted_results.append(result_data)
        
        return formatted_results


def create_sample_data() -> List[CodeInfo]:
    """サンプルデータを作成"""
    return [
        CodeInfo(
            id="func_001",
            name="calculate_area",
            content="def calculate_area(radius):\n    return 3.14159 * radius * radius",
            type="function",
            file_path="math_utils.py",
            description="円の面積を計算する関数",
            parameters=["radius"],
            returns="float"
        ),
        CodeInfo(
            id="func_002", 
            name="read_file",
            content="def read_file(filepath):\n    with open(filepath, 'r') as f:\n        return f.read()",
            type="function",
            file_path="file_utils.py",
            description="ファイルを読み込む関数",
            parameters=["filepath"],
            returns="str"
        ),
        CodeInfo(
            id="class_001",
            name="DataProcessor",
            content="class DataProcessor:\n    def __init__(self):\n        self.data = []\n    def process(self, item):\n        return item.upper()",
            type="class",
            file_path="data_utils.py",
            description="データ処理を行うクラス",
            parameters=[],
            returns=""
        )
    ]


if __name__ == "__main__":
    # 使用例の実行
    print("ベクトル検索エンジンのテストを開始します...")
    
    # エンジンの初期化
    engine = VectorSearchEngine()
    
    # サンプルデータの追加
    sample_data = create_sample_data()
    for code_info in sample_data:
        engine.add_code_info(code_info)
    
    # 検索テスト
    print("\n=== 検索テスト ===")
    
    # 類似検索
    results = engine.search_similar_functions("ファイルを読む", top_k=3)
    print(f"\n'ファイルを読む'の検索結果: {len(results)}件")
    for result in results:
        print(f"  - {result['name']} (類似度: {result['similarity']:.3f})")
    
    # タイプ検索
    functions = engine.search_by_type("function")
    print(f"\n関数の検索結果: {len(functions)}件")
    for func in functions:
        print(f"  - {func['name']}")
    
    # 統計情報
    stats = engine.get_collection_stats()
    print(f"\n=== 統計情報 ===")
    print(f"総件数: {stats['total_count']}")
    print(f"タイプ別: {stats['type_distribution']}")
    
    print("\nテスト完了!")