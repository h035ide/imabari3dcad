# LangChain Interface for imabari3dcad

imabari3dcadプロジェクト用のLangChainインターフェースモジュールです。Neo4jグラフインデックスとChromaベクトルストアをサポートし、高い独立性を持ち、簡単に既存のプロジェクトに統合できます。

## 概要

このLangChainインターフェースは以下の機能を提供します：

- **Neo4jグラフインデックス**: グラフデータベースを使用したセマンティック検索
- **Chromaベクトルストア**: ベクトルベースの類似度検索
- **ハイブリッド検索**: グラフとベクトルの両方を組み合わせた検索
- **高い独立性**: 既存のコードに最小限の変更で統合可能
- **フォールバック機能**: 依存ライブラリがない場合でもモックモードで動作

## インストール

### 必要な依存関係

```bash
pip install langchain langchain-community langchain-openai chromadb neo4j
```

### pyproject.tomlへの追加

```toml
dependencies = [
    "langchain>=0.3.27",
    "langchain-community>=0.3.27", 
    "langchain-openai>=0.3.28",
    "langchain-core>=0.3.27",
    "chromadb>=0.5.0",
    "neo4j>=5.28.1",
]
```

## 使用方法

### 基本的な使用

```python
from langchain_interface import create_interface

# インターフェースの作成
interface = create_interface()

# ハイブリッド検索
results = interface.hybrid_search("3D CAD機能について")
print(results)

# ドキュメントの追加
interface.add_document(
    "新しいドキュメント内容",
    {"category": "api_doc", "language": "ja"}
)

# 接続状態の確認
status = interface.get_connection_status()
print(f"Neo4j: {status['neo4j_connected']}, Chroma: {status['chroma_connected']}")

# 終了
interface.close()
```

### 設定を使用した初期化

```python
from langchain_interface import create_interface, ConnectionConfig

# カスタム設定
config = ConnectionConfig(
    neo4j_uri="neo4j://localhost:7687",
    neo4j_username="neo4j", 
    neo4j_password="your_password",
    chroma_persist_directory="./my_chroma_db",
    openai_api_key="your_openai_key"
)

interface = create_interface(config.__dict__)
```

### 環境変数での設定

```bash
# Neo4j設定
export NEO4J_URI="neo4j://localhost:7687"
export NEO4J_USERNAME="neo4j"
export NEO4J_PASSWORD="your_password"
export NEO4J_DATABASE="neo4j"

# Chroma設定
export CHROMA_PERSIST_DIR="./chroma_db"
export CHROMA_COLLECTION="imabari3dcad"

# OpenAI設定
export OPENAI_API_KEY="your_openai_key"
export MODEL_NAME="gpt-3.5-turbo"
```

### 高度な使用（Advanced RAG）

```python
from langchain_advanced_rag import create_advanced_rag

# 高度なRAGシステムの作成
rag = create_advanced_rag()

# 包括的検索
results = rag.comprehensive_search("システム機能について", search_mode="comprehensive")

# 知識の追加
rag.add_knowledge(
    "新しい知識内容",
    metadata={"type": "technical_doc"},
    content_type="api_doc"
)

# システム状態の確認
status = rag.get_system_status()
print(status)

rag.close()
```

### 既存システムとの統合

```python
from langchain_integration_example import IntegratedRAGSystem

# 統合システムの初期化
system = IntegratedRAGSystem()

# 統一検索（既存システムと新システムの両方を使用）
results = system.unified_search("検索クエリ", search_type="comprehensive")

# システム健康状態の確認
health = system.get_system_health()
print(health)

system.close_all_connections()
```

## API リファレンス

### LangChainInterface

主要なインターフェースクラス。

#### メソッド

- `hybrid_search(query: str, k: int = 5) -> Dict[str, Any]`
  - グラフとベクトルの両方を使用したハイブリッド検索
  
- `add_document(content: str, metadata: Optional[Dict] = None) -> None`
  - ドキュメントをグラフとベクトルストアの両方に追加
  
- `query_graph(cypher_query: str, **params) -> str`
  - Neo4jに対して直接Cypherクエリを実行
  
- `search_vectors(query: str, k: int = 5) -> List[Dict[str, Any]]`
  - Chromaベクトルストアで類似度検索を実行
  
- `get_connection_status() -> Dict[str, bool]`
  - Neo4jとChromaの接続状態を確認
  
- `close() -> None`
  - すべての接続を閉じる

### ConnectionConfig

接続設定用のデータクラス。

#### パラメータ

- `neo4j_uri`: Neo4jサーバーのURI（デフォルト: "neo4j://localhost:7687"）
- `neo4j_username`: ユーザー名（デフォルト: "neo4j"）
- `neo4j_password`: パスワード
- `neo4j_database`: データベース名（デフォルト: "neo4j"）
- `chroma_persist_directory`: Chromaの永続化ディレクトリ（デフォルト: "./chroma_db"）
- `chroma_collection_name`: コレクション名（デフォルト: "imabari3dcad"）
- `openai_api_key`: OpenAI APIキー
- `model_name`: 使用するモデル名（デフォルト: "gpt-3.5-turbo"）

## 特徴

### 1. 高い独立性

- 既存のコードを変更せずに統合可能
- モジュラー設計により、必要な部分のみ使用可能
- 依存関係が満たされない場合でもモックモードで動作

### 2. フォールバック機能

- Neo4jライブラリがない場合：モック応答を返す
- Chromaライブラリがない場合：サンプル結果を返す
- 接続できない場合：エラーではなく警告で継続

### 3. 柔軟な設定

- 環境変数での設定
- 設定辞書での設定
- プログラム内での設定
- デフォルト値の提供

### 4. 既存システムとの統合

- 既存のNeo4jクエリエンジンとの連携
- LlamaIndexシステムとの統合
- 段階的な移行サポート

## テスト

```bash
# 基本テストの実行
python test_langchain_interface.py

# 統合テストの実行（依存関係が必要）
python langchain_integration_example.py
```

## トラブルシューティング

### よくある問題

1. **Neo4jに接続できない**
   ```
   neo4jライブラリが見つかりません。モックモードで動作します
   ```
   - 解決方法: `pip install neo4j` でライブラリをインストール
   - または: Neo4jサーバーが起動していることを確認

2. **Chromaに接続できない**
   ```
   chromadbライブラリが見つかりません。モックモードで動作します
   ```
   - 解決方法: `pip install chromadb` でライブラリをインストール

3. **OpenAI APIエラー**
   - 解決方法: `OPENAI_API_KEY` 環境変数を正しく設定

### デバッグ

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# これでより詳細なログが出力されます
interface = create_interface()
```

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 貢献

バグ報告や機能要望は、GitHubのIssueでお知らせください。
プルリクエストも歓迎します。

## 変更履歴

### v1.0.0
- 初期リリース
- LangChainインターフェースの基本機能
- Neo4jとChromaの統合
- モックモードの実装
- 既存システムとの統合サポート