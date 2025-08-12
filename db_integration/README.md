# データベース統合モジュール (`db_integration`)

このモジュールは、APIの仕様書（自然言語ドキュメント）と、そのAPIを利用するPythonのソースコードを解析し、両者の関係性をリンクさせたナレッジグラフをNeo4jデータベース上に構築します。

最終的な目標である「ユーザー指示に基づくAIコード生成」において、この統合されたグラフは「APIが仕様上どうあるべきか」と「実際にコードでどう使われているか」という2つの重要なコンテキストを提供し、コード生成の精度を飛躍的に向上させるための基盤となります。

## 機能

- **API仕様解析**: 自然言語で書かれたAPIドキュメントをLLM（GPT-4など）を用いて解析し、関数、パラメータ、型定義などを構造化データとして抽出します。
- **Pythonコード解析**: `tree-sitter` を用いてPythonソースコードの構文を詳細に解析し、クラス、関数、変数、呼び出し関係などを抽出します。
- **Neo4jへのインポート**: 上記2つの解析結果をNeo4jデータベースに格納します。
- **グラフのリンク**: API仕様上の関数と、コード中の同名の関数（実装）を `IMPLEMENTS_API` リレーションで結びつけ、統合ナレッジグラフを完成させます。

## 設定方法

実行には、Neo4jデータベースとOpenAI APIへの接続情報が必要です。プロジェクトのルートディレクトリに`.env`という名前のファイルを作成し、以下の内容を記述してください。

```env
# Neo4j データベース接続情報
NEO4J_URI="bolt://localhost:7687"
NEO4J_USER="neo4j"
NEO4J_PASSWORD="YOUR_NEO4J_PASSWORD"

# OpenAI APIキー
OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
```

## 依存ライブラリのインストール

必要なライブラリは `requirements.txt` に記載されています。以下のコマンドでインストールしてください。

```bash
pip install -r requirements.txt
```
*(注: 今回のタスクでいくつかのライブラリを追加しました。`requirements.txt` の更新も後ほど行います。)*


## 使用方法

`integrate.py`スクリプトをコマンドラインから実行します。

### コマンド

```bash
# uvを使用する場合（推奨）
uv run .\db_integration\integrate.py --code-file <path_to_code> --api-doc <path_to_api_doc> --api-args <path_to_api_args> [options]

# または、Pythonモジュールとして実行
python -m db_integration.integrate --code-file <path_to_code> --api-doc <path_to_api_doc> --api-args <path_to_api_args> [options]
```

### 引数

- `--code-file` (必須): 解析対象のPythonソースファイルへのパス。
- `--api-doc` (必須): API関数の仕様が書かれたテキストファイルへのパス。
- `--api-args` (必須): API引数の仕様が書かれたテキストファイルへのパス。
- `--db-name` (任意): 使用するNeo4jデータベース名。デフォルトは `unifieddb` です。
- `--clear-db` (任意): このフラグを立てると、インポート実行前にデータベース内のすべてのデータが削除されます。
- `--no-llm` (任意): このフラグを立てると、コード解析時のLLMによる説明生成を無効にします。

### 実行例

`data/src`にあるサンプルファイルを使ってデータベースを構築する例です。

```bash
# Windows PowerShellの場合
uv run .\db_integration\integrate.py --code-file "evoship\create_test.py" --api-doc "data\src\api 1.txt" --api-args "data\src\api_arg 1.txt" --clear-db

# または、データベース名を指定する場合
uv run .\db_integration\integrate.py --code-file "evoship\create_test.py" --api-doc "data\src\api 1.txt" --api-args "data\src\api_arg 1.txt" --db-name evoship_knowledge_base --clear-db
```
