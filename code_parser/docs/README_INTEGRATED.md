# 統合コードパーサー

3つのブランチの機能を統合したPythonコード解析システムです。

## 🚀 主な機能

### 1. Tree-sitterによる構文解析
- Pythonコードの構文構造を解析
- 関数、クラス、変数などの要素を抽出
- Neo4jデータベースにグラフデータとして格納

### 2. ベクトル検索による意味的検索
- ChromaDBを使用したベクトル検索
- コードの意味的な類似性を検索
- 自然言語クエリによるコード検索

### 3. LLMによる高度なコード分析
- OpenAI APIを使用したコード分析
- 関数の目的、使用例、エラーハンドリングの分析
- クラスの設計パターン、責任範囲の分析

### 4. パフォーマンス最適化
- 検索パフォーマンスの測定
- キャッシュ機能による高速化
- ベンチマーク機能

## 📁 ファイル構成

```
code_parser/
├── main_integrated.py          # 統合メインスクリプト
├── simple_config.py            # シンプルな設定ファイル
├── simple_utils.py             # ユーティリティ機能
├── demo_integrated.py          # 統合デモスクリプト
├── test_integrated.py          # 統合テスト
├── test_mock_integration.py    # モック統合テスト
├── run_tests.py                # テスト実行スクリプト
├── treesitter_neo4j_advanced.py    # Tree-sitter統合
├── vector_search.py            # ベクトル検索エンジン
├── enhanced_llm_analyzer.py    # LLM分析器
├── performance_optimizer.py    # パフォーマンス最適化器
├── rag_search_engine.py        # RAG検索エンジン
├── enhanced_data_models.py     # 拡張データモデル
├── enhanced_parser_adapter.py  # パーサーアダプター
└── enhanced_data_migration.py  # データ移行機能
```

## 🛠️ セットアップ

### 1. 環境変数の設定
プロジェクトルートの`.env`ファイルに以下を設定：

```bash
# Neo4j設定
NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

# OpenAI API設定（LLM分析用）
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.1
```

### 2. 依存関係のインストール
```bash
# プロジェクトルートで実行
uv run pip install -r requirements.txt
```

## 🚀 使用方法

### 1. 基本的な使用方法
```bash
# プロジェクトルートで実行
uv run python code_parser/main_integrated.py path/to/your/file.py
```

### 2. オプション付きの実行
```bash
# LLM分析を無効化
uv run python code_parser/main_integrated.py --no-llm path/to/your/file.py

# ベクトル検索を無効化
uv run python code_parser/main_integrated.py --no-vector path/to/your/file.py

# コード検索
uv run python code_parser/main_integrated.py --search "ファイル処理関数"

# LLM分析
uv run python code_parser/main_integrated.py --analyze "def test(): pass"
```

### 3. デモの実行
```bash
# 統合デモの実行
uv run python code_parser/demo_integrated.py
```

## 🧪 テスト

### 1. 全テストの実行
```bash
# プロジェクトルートで実行
uv run python code_parser/run_tests.py --all
```

### 2. 特定のテストの実行
```bash
# ユニットテストのみ
uv run python code_parser/run_tests.py --unit

# カバレッジテストのみ
uv run python code_parser/run_tests.py --coverage

# シンプルテストのみ
uv run python code_parser/run_tests.py --simple

# 統合テストのみ
uv run python code_parser/run_tests.py --integration
```

### 3. 個別テストの実行
```bash
# 統合テスト
uv run python code_parser/test_integrated.py

# モック統合テスト
uv run python code_parser/test_mock_integration.py
```

## 📊 機能詳細

### Tree-sitter統合
- **ファイル解析**: Pythonファイルの構文解析
- **Neo4j格納**: 解析結果をグラフデータベースに格納
- **LLM統合**: 構文解析結果をLLMで詳細分析

### ベクトル検索
- **コード抽出**: 関数、クラス、メソッドの情報抽出
- **ベクトル化**: 意味的な特徴をベクトルとして表現
- **類似検索**: 自然言語クエリによるコード検索

### LLM分析
- **関数分析**: 目的、入出力、使用例、エラーハンドリング
- **クラス分析**: 設計パターン、責任範囲、使用場面
- **エラー分析**: 例外、原因、解決方法、予防策

### パフォーマンス最適化
- **検索ベンチマーク**: 検索パフォーマンスの測定
- **キャッシュ管理**: 検索結果のキャッシュ
- **最適化提案**: パフォーマンス改善の提案

## 🔧 カスタマイズ

### 設定の変更
`simple_config.py`で各種設定を変更できます：

```python
# Neo4j設定
NEO4J_CONFIG = {
    "uri": "neo4j://your_host:7687",
    "user": "your_username",
    "password": "your_password"
}

# ベクトル検索設定
VECTOR_SEARCH_CONFIG = {
    "persist_directory": "./custom_vector_store",
    "collection_name": "custom_collection"
}
```

### 新しい機能の追加
各モジュールは独立しており、新しい機能を追加しやすい構造になっています。

## 🐛 トラブルシューティング

### よくある問題

1. **Neo4j接続エラー**
   - `.env`ファイルの設定を確認
   - Neo4jサーバーが起動しているか確認

2. **LLM分析エラー**
   - OpenAI APIキーが正しく設定されているか確認
   - API制限に達していないか確認

3. **ベクトル検索エラー**
   - ChromaDBの依存関係がインストールされているか確認
   - 十分なディスク容量があるか確認

### ログの確認
ログレベルを調整して詳細な情報を確認できます：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 パフォーマンス

### 推奨設定
- **小規模プロジェクト**: デフォルト設定で十分
- **中規模プロジェクト**: キャッシュサイズを増加
- **大規模プロジェクト**: ベクトル検索のインデックス最適化

### ベンチマーク結果
一般的なPythonファイル（1000行程度）の解析：
- 構文解析: 0.1-0.5秒
- ベクトル化: 0.5-2.0秒
- LLM分析: 2.0-10.0秒（API応答時間に依存）

## 🤝 貢献

1. 機能の提案やバグ報告
2. テストケースの追加
3. ドキュメントの改善
4. パフォーマンスの最適化

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 📞 サポート

問題や質問がある場合は、以下の方法でサポートを受けることができます：

1. イシューの作成
2. ドキュメントの確認
3. テストの実行による動作確認
