# ベクトル検索システム

独自APIを活用したPythonコード生成のためのRAG（Retrieval-Augmented Generation）ベクトル検索システムです。

## 概要

このシステムは、Pythonコードから関数やクラスの情報を抽出し、ChromaDBを使用したベクトル検索により意味的な検索を可能にします。自然言語でのクエリに基づいて、関連するコードを効率的に検索できます。

## 主要コンポーネント

### 1. VectorSearchEngine (`vector_search.py`)
- ChromaDBを使用したベクトル検索エンジン
- コード情報の埋め込みとインデックス化
- 意味的検索とフィルタリング機能

### 2. CodeExtractor (`code_extractor.py`)
- Tree-sitterを使用したPythonコード解析
- 関数、クラス、メソッドの自動抽出
- ドキュメント文字列とパラメータ情報の取得

### 3. RAGSearchEngine (`rag_search_engine.py`)
- ベクトル検索とコード抽出の統合システム
- ディレクトリ単位でのインデックス化
- 高度な検索機能（機能別、入出力型別検索）

### 4. PerformanceOptimizer (`performance_optimizer.py`)
- パフォーマンス測定とベンチマーク
- ChromaDB設定の最適化
- 総合的なパフォーマンスレポート

## インストール

必要なライブラリをインストールしてください：

```bash
pip install chromadb sentence-transformers tree-sitter tree-sitter-python
```

## 基本的な使用方法

### 1. シンプルなベクトル検索

```python
from vector_search import VectorSearchEngine, CodeInfo

# エンジンの初期化
engine = VectorSearchEngine()

# コード情報の追加
code_info = CodeInfo(
    id="func_001",
    name="read_file",
    content="def read_file(path): ...",
    type="function",
    file_path="utils.py",
    description="ファイルを読み込む関数"
)
engine.add_code_info(code_info)

# 検索の実行
results = engine.search_similar_functions("ファイルを読む", top_k=5)
for result in results:
    print(f"{result['name']}: {result['similarity']:.3f}")
```

### 2. コード抽出

```python
from code_extractor import CodeExtractor

# 抽出器の初期化
extractor = CodeExtractor()

# ファイルからコード情報を抽出
code_infos = extractor.extract_from_file("sample.py")

# ディレクトリから一括抽出
all_code_infos = extractor.extract_from_directory("./src", recursive=True)
```

### 3. RAG検索システム

```python
from rag_search_engine import RAGSearchEngine

# RAGエンジンの初期化
rag_engine = RAGSearchEngine()

# ディレクトリをインデックス化
result = rag_engine.index_directory("./my_project")
print(f"インデックス化完了: {result['successfully_indexed']}個の要素")

# 自然言語での検索
results = rag_engine.search("データを処理する関数")

# 機能別検索
func_results = rag_engine.search_by_functionality("ファイル操作")

# 入出力型での検索
io_results = rag_engine.search_by_input_output("str", "list")
```

### 4. パフォーマンス分析

```python
from performance_optimizer import PerformanceOptimizer

# 最適化器の初期化
optimizer = PerformanceOptimizer(engine)

# 検索パフォーマンスのベンチマーク
test_queries = ["計算", "ファイル", "データ処理"]
benchmark_results = optimizer.benchmark_search_performance(test_queries)

# 設定の最適化
optimal_settings = optimizer.optimize_collection_settings()

# 総合レポートの生成
report = optimizer.generate_performance_report()
optimizer.save_report(report, "performance_report.json")
```

## 検索の種類

### 1. 意味的検索
自然言語での検索が可能：
- "ファイルを読み込む関数"
- "データを変換する"
- "エラーをハンドリングする"

### 2. 機能的検索
特定の機能に特化した検索：
```python
results = rag_engine.search_by_functionality("データベース接続")
```

### 3. 型による検索
入力・出力の型を指定した検索：
```python
results = rag_engine.search_by_input_output("list", "dict")
```

### 4. 類似実装検索
コードスニペットに基づく検索：
```python
code_snippet = "def process_data(data): return [x for x in data if x]"
results = rag_engine.get_similar_implementations(code_snippet)
```

## 設定とカスタマイズ

### ChromaDB設定
```python
engine = VectorSearchEngine(
    persist_directory="./my_vector_store",
    collection_name="my_collection",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2"
)
```

### 除外パターンの設定
```python
code_infos = extractor.extract_from_directory(
    "./project",
    recursive=True,
    exclude_patterns=["__pycache__", ".git", "venv", "tests"]
)
```

## パフォーマンス最適化

### 1. コレクションサイズ別の最適化設定

- **小規模（< 1,000要素）**: construction_ef=64, search_ef=32, m=16
- **中規模（< 10,000要素）**: construction_ef=128, search_ef=64, m=32  
- **大規模（10,000要素以上）**: construction_ef=256, search_ef=128, m=64

### 2. キャッシュ機能
- クエリ結果の自動キャッシュ（1時間TTL）
- キャッシュヒット率の監視
- 手動キャッシュクリア機能

### 3. バッチ処理の最適化
```python
# 大量データの効率的なインデックス化
result = rag_engine.index_directory("./large_project", recursive=True)
```

## テストとデバッグ

### 統合テストの実行
```bash
python test_vector_search.py
```

### サンプル使用例の実行
```bash
python test_vector_search.py sample
```

### 個別コンポーネントのテスト
```bash
python vector_search.py          # ベクトル検索エンジンのデモ
python code_extractor.py         # コード抽出器のデモ  
python rag_search_engine.py      # RAG検索システムのデモ
python performance_optimizer.py  # パフォーマンス最適化のデモ
```

## トラブルシューティング

### よくある問題と解決方法

1. **埋め込みモデルのダウンロードが遅い**
   - 初回実行時に自動ダウンロードされます
   - ネットワーク環境を確認してください

2. **検索結果が少ない**
   - 類似度閾値を下げてください（デフォルト0.7）
   - より多くのコードをインデックス化してください

3. **パフォーマンスが低下している**
   - `PerformanceOptimizer`でベンチマークを実行してください
   - コレクション設定を最適化してください
   - キャッシュをクリアしてください

4. **メモリ使用量が多い**
   - バッチサイズを小さくしてください
   - 古いキャッシュを定期的にクリアしてください

## ファイル構成

```
code_parser/
├── vector_search.py           # ベクトル検索エンジン
├── code_extractor.py          # コード抽出器
├── rag_search_engine.py       # RAG検索システム
├── performance_optimizer.py   # パフォーマンス最適化器
├── test_vector_search.py      # テストとサンプル
└── README_vector_search.md    # このドキュメント
```

## 今後の拡張計画

1. **LLM分析機能の統合**
   - より詳細なコード分析
   - 自動ドキュメント生成

2. **追加の検索機能**
   - 複雑な複合検索
   - 時系列での検索

3. **パフォーマンス改善**
   - GPU加速サポート
   - 分散処理対応

4. **UI/API**
   - Web UIの追加
   - REST API提供

---

このベクトル検索システムは、独自APIを活用したPythonコード生成を支援する強力なRAGシステムの基盤となります。