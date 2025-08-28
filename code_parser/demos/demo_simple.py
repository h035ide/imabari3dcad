"""
シンプルなデモ - 外部ライブラリに依存しないベクトル検索システムのデモ

ベクトル検索システムの基本的な機能をデモンストレーションします。
実際の実行では、chromadbとsentence-transformersが必要です。
"""

import os
import json
import time
from typing import List, Dict, Any, Optional
from pathlib import Path


class MockCodeInfo:
    """コード情報のモッククラス"""
    
    def __init__(self, id: str, name: str, content: str, type: str, 
                 file_path: str, description: str = "", 
                 parameters: List[str] = None, returns: str = ""):
        self.id = id
        self.name = name
        self.content = content
        self.type = type
        self.file_path = file_path
        self.description = description
        self.parameters = parameters or []
        self.returns = returns


def demo_basic_functionality():
    """基本機能のデモンストレーション"""
    print("=== ベクトル検索システム デモ ===")
    print("※ 実際の動作には chromadb と sentence-transformers が必要です")
    
    # サンプルデータの作成
    sample_codes = [
        MockCodeInfo(
            id="func_001",
            name="read_file",
            content="def read_file(filepath):\n    with open(filepath, 'r') as f:\n        return f.read()",
            type="function",
            file_path="file_utils.py",
            description="ファイルの内容を読み込む関数",
            parameters=["filepath"],
            returns="str"
        ),
        MockCodeInfo(
            id="func_002",
            name="write_file",
            content="def write_file(filepath, content):\n    with open(filepath, 'w') as f:\n        f.write(content)",
            type="function", 
            file_path="file_utils.py",
            description="ファイルに内容を書き込む関数",
            parameters=["filepath", "content"],
            returns="None"
        ),
        MockCodeInfo(
            id="func_003",
            name="calculate_area",
            content="def calculate_area(radius):\n    return 3.14159 * radius * radius",
            type="function",
            file_path="math_utils.py", 
            description="円の面積を計算する関数",
            parameters=["radius"],
            returns="float"
        ),
        MockCodeInfo(
            id="class_001",
            name="DataProcessor",
            content="class DataProcessor:\n    def __init__(self):\n        self.data = []\n    def process(self, item):\n        return item.upper()",
            type="class",
            file_path="data_utils.py",
            description="データ処理を行うクラス",
            parameters=[],
            returns=""
        ),
        MockCodeInfo(
            id="func_004",
            name="process_text",
            content="def process_text(text):\n    return text.strip().lower()",
            type="function",
            file_path="text_utils.py",
            description="テキストを処理する関数",
            parameters=["text"],
            returns="str"
        )
    ]
    
    print(f"\n1. サンプルデータ: {len(sample_codes)}個のコード要素")
    for code in sample_codes:
        print(f"   - {code.name} ({code.type}): {code.description}")
    
    # 模擬検索結果の生成
    print(f"\n2. 検索シミュレーション")
    
    search_queries = [
        ("ファイルを読む", ["read_file"]),
        ("データを処理する", ["DataProcessor", "process_text"]),
        ("計算する", ["calculate_area"]),
        ("ファイル操作", ["read_file", "write_file"])
    ]
    
    for query, expected_matches in search_queries:
        print(f"\n検索クエリ: '{query}'")
        
        # 簡単な文字列マッチングで模擬検索
        matches = []
        for code in sample_codes:
            score = calculate_simple_similarity(query, code)
            if score > 0.3:  # 閾値
                matches.append((code, score))
        
        # スコア順でソート
        matches.sort(key=lambda x: x[1], reverse=True)
        
        print(f"検索結果: {len(matches)}件")
        for code, score in matches[:3]:  # 上位3件
            print(f"  - {code.name} (スコア: {score:.3f})")
            print(f"    説明: {code.description}")
            print(f"    ファイル: {code.file_path}")
    
    # 統計情報の表示
    print(f"\n3. 統計情報")
    type_counts = {}
    for code in sample_codes:
        type_counts[code.type] = type_counts.get(code.type, 0) + 1
    
    print(f"総要素数: {len(sample_codes)}")
    for code_type, count in type_counts.items():
        print(f"  {code_type}: {count}個")
    
    # パフォーマンス情報
    print(f"\n4. パフォーマンス情報（模擬）")
    search_time = 0.001  # 模擬時間
    print(f"平均検索時間: {search_time:.3f}秒")
    print(f"検索スループット: {1/search_time:.0f} QPS")
    
    print(f"\n=== 実装済み機能 ===")
    print("✅ VectorSearchEngine - ChromaDBベクトル検索")
    print("✅ CodeExtractor - Tree-sitterコード解析")
    print("✅ RAGSearchEngine - 統合検索システム")
    print("✅ PerformanceOptimizer - パフォーマンス最適化")
    print("✅ 統合テスト - test_vector_search.py")
    
    print(f"\n=== 次のステップ ===")
    print("1. 必要なライブラリをインストール:")
    print("   pip install chromadb sentence-transformers tree-sitter tree-sitter-python")
    print("2. 実際のベクトル検索エンジンをテスト:")
    print("   python3 test_vector_search.py")
    print("3. 実際のプロジェクトでのインデックス化:")
    print("   python3 -c \"from rag_search_engine import RAGSearchEngine; rag = RAGSearchEngine(); rag.index_directory('./your_project')\"")


def calculate_simple_similarity(query: str, code: MockCodeInfo) -> float:
    """簡単な類似度計算（デモ用）"""
    query_lower = query.lower()
    
    # 名前での一致
    name_score = 0.0
    if query_lower in code.name.lower():
        name_score = 0.8
    
    # 説明での一致
    desc_score = 0.0
    if query_lower in code.description.lower():
        desc_score = 0.6
    
    # キーワードベースの一致
    keyword_mappings = {
        "ファイル": ["file", "read", "write"],
        "読む": ["read", "load"],
        "書く": ["write", "save"],
        "計算": ["calculate", "compute"],
        "処理": ["process", "handle"],
        "データ": ["data", "process"]
    }
    
    keyword_score = 0.0
    for japanese_word, english_words in keyword_mappings.items():
        if japanese_word in query_lower:
            for eng_word in english_words:
                if eng_word in code.name.lower() or eng_word in code.description.lower():
                    keyword_score = max(keyword_score, 0.4)
    
    return max(name_score, desc_score, keyword_score)


def show_file_structure():
    """作成されたファイル構造を表示"""
    print(f"\n=== 作成されたファイル一覧 ===")
    
    current_dir = Path(".")
    python_files = list(current_dir.glob("*.py"))
    md_files = list(current_dir.glob("*.md"))
    
    all_files = sorted(python_files + md_files)
    
    for file_path in all_files:
        size = file_path.stat().st_size
        print(f"{file_path.name:<25} ({size:,} bytes)")
    
    print(f"\n総ファイル数: {len(all_files)}")
    print(f"Pythonファイル: {len(python_files)}")
    print(f"ドキュメント: {len(md_files)}")


def create_installation_guide():
    """インストールガイドの作成"""
    print(f"\n=== インストールガイド ===")
    
    guide = """
# ベクトル検索システム セットアップガイド

## 1. 必要なライブラリのインストール

### 基本ライブラリ
```bash
pip install chromadb sentence-transformers tree-sitter tree-sitter-python
```

### 追加ライブラリ（オプション）
```bash
pip install numpy pandas matplotlib  # データ分析用
```

## 2. 基本動作確認

### テストの実行
```bash
python3 test_vector_search.py
```

### サンプル使用例の実行  
```bash
python3 test_vector_search.py sample
```

## 3. 実際の使用例

### プロジェクトのインデックス化
```python
from rag_search_engine import RAGSearchEngine

rag = RAGSearchEngine()
result = rag.index_directory("./your_project")
print(f"インデックス化完了: {result['successfully_indexed']}個")
```

### コード検索
```python
results = rag.search("ファイルを読み込む関数", top_k=5)
for result in results:
    print(f"{result['name']}: {result.get('similarity', 0):.3f}")
```

## 4. パフォーマンス確認

```python
from performance_optimizer import PerformanceOptimizer

optimizer = PerformanceOptimizer(rag.vector_engine)
report = optimizer.generate_performance_report()
optimizer.save_report(report)
```
"""
    
    print(guide)


if __name__ == "__main__":
    demo_basic_functionality()
    show_file_structure()
    create_installation_guide()