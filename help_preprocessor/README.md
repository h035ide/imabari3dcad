# Help Preprocessor

EVOSHIPヘルプドキュメント（Shift_JIS エンコード）を構造化データに変換し、Neo4j グラフデータベースと Chroma ベクトルストアに保存するための専用モジュールです。

## 概要

このモジュールは以下の機能を提供します：

- **HTMLパース**: Shift_JIS エンコードされたヘルプHTMLファイルの正規化と構造化
- **インデックス解析**: `index.txt` からカテゴリ階層の構築
- **グラフ生成**: Neo4j用のノードとリレーションシップの生成
- **ベクトル化**: セクション単位でのチャンク化とメタデータ付与
- **ストレージ統合**: Neo4j と Chroma への自動アップサート

## セットアップ

### 必要な依存関係

```bash
uv pip install neo4j chromadb openai
```

### 環境変数の設定

`.env` ファイルに以下の設定を追加：

```bash
# ソースファイル設定
HELP_SOURCE_ROOT=evoship/EVOSHIP_HELP_FILES
HELP_CACHE_DIR=data/help_preprocessor/cache
HELP_OUTPUT_DIR=data/help_preprocessor/output
HELP_SOURCE_ENCODING=shift_jis

# チャンク設定
HELP_CHUNK_SIZE=1200
HELP_CHUNK_OVERLAP=120

# Neo4j 設定
HELP_NEO4J_URI=bolt://localhost:7687
HELP_NEO4J_USERNAME=neo4j
HELP_NEO4J_PASSWORD=your_password
HELP_NEO4J_DATABASE=evoship_help

# Chroma 設定
HELP_CHROMA_COLLECTION=evoship-help
HELP_CHROMA_PERSIST_DIR=data/help_preprocessor/chroma

# OpenAI 設定（将来の埋め込み用）
HELP_OPENAI_MODEL=text-embedding-3-small
```

## 使用方法

### コマンドライン実行

```bash
# ドライラン（ストレージへの書き込みなし）
uv run help-preprocess --dry-run

# 本実行
uv run help-preprocess

# カスタムソースディレクトリ指定
uv run help-preprocess /path/to/help/files --log-level DEBUG

# サンプル処理数制限（ドライラン時）
uv run help-preprocess --dry-run --sample-limit 5
```

### プログラムからの利用

```python
from help_preprocessor.config import load_config_from_env
from help_preprocessor.pipeline import HelpPreprocessorPipeline
from help_preprocessor.storage.neo4j_loader import HelpNeo4jLoader
from help_preprocessor.storage.chroma_loader import HelpChromaLoader

# 設定読み込み
config = load_config_from_env()

# ストレージローダー初期化
neo4j_loader = HelpNeo4jLoader(
    uri=config.neo4j_uri,
    username=config.neo4j_username,
    password=config.neo4j_password,
    database=config.neo4j_database
)

chroma_loader = HelpChromaLoader(
    collection_name=config.chroma_collection,
    persist_directory=str(config.chroma_persist_dir)
)

# パイプライン実行
pipeline = HelpPreprocessorPipeline(
    config,
    neo4j_loader=neo4j_loader,
    chroma_loader=chroma_loader
)

result = pipeline.run(dry_run=False)
print(f"処理完了: {len(result.graph_nodes)} ノード, {len(result.vector_chunks)} チャンク")

# クリーンアップ
neo4j_loader.close()
```

## データ構造

### Neo4j グラフスキーマ

```cypher
# ノードタイプ
(:HelpCategory {category_id, name, topic_count, child_count})
(:HelpTopic {topic_id, title, source_path, section_count})

# リレーションシップ
(HelpCategory)-[:HAS_CHILD_CATEGORY {order}]->(HelpCategory)
(HelpCategory)-[:HAS_TOPIC {order}]->(HelpTopic)
```

### Chroma ベクトルメタデータ

```python
{
    "id": "topic_id#section_id:chunk_index",
    "text": "チャンク化されたテキスト",
    "metadata": {
        "section_id": "section_identifier", 
        "title": "セクションタイトル",
        "offset": 0,
        "length": 1200,
        "anchors": ["anchor1", "anchor2"],
        "link_count": 3,
        "media_count": 1,
        "source": "evoship-help"
    }
}
```

## 処理フロー

1. **解析**: `index.txt` と HTML ファイルを読み込み、カテゴリ階層を構築
2. **キャッシュ**: 解析結果を JSON 形式でキャッシュ（高速再実行）
3. **グラフ化**: Neo4j 用のノード・リレーションシップペイロードを生成
4. **ベクトル化**: セクション単位でチャンク分割、メタデータ付与
5. **保存**: Neo4j と Chroma に並列でアップサート

## トラブルシューティング

### エンコーディングエラー
- 複数エンコーディングでの自動フォールバック機能あり
- ログで使用されたエンコーディングを確認可能

### Neo4j接続エラー
```bash
# 接続テスト
uv run python -c "from help_preprocessor.storage.neo4j_loader import HelpNeo4jLoader; HelpNeo4jLoader('bolt://localhost:7687', 'neo4j', 'password').close()"
```

### キャッシュクリア
```bash
rm -rf data/help_preprocessor/cache/
```

## 開発者向け

### テスト実行
```bash
uv run pytest tests/help_preprocessor/ -v
uv run pytest tests/help_preprocessor/ --cov=help_preprocessor
```

### リント・フォーマット
```bash
uv run ruff check help_preprocessor/
uv run black help_preprocessor/
```

## ライセンス

プロジェクトのライセンスに従います。
