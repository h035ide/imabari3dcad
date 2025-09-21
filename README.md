# imabari3dcad ドキュメント（日本語）

## 概要

`imabari3dcad` は、技術ドキュメントを解析して知識グラフ（Neo4j）とベクトルDB（ChromaDB）に格納し、LlamaIndex を用いたハイブリッド検索（ベクトル検索 + グラフ検索）でQAを行うためのツール群です。主なエントリポイントは `main_0905.py` のCLIです。

## 主な機能（CLI `--function`）

- **nollm_doc**: ルールベース処理でドキュメントを解析し、Neo4jへ取り込み。
- **llm_doc**: LLMを用いた解析結果をNeo4jへ取り込み。
- **vectorize**: Neo4jから関数情報を取得し、ChromaDBへ埋め込み格納。
- **llamaindex_vectorize**: 既存Chromaコレクションから LlamaIndex のインデックスを構築。
- **qa**: ベクトル検索とグラフ検索を統合したQAを実行（対話/非対話）。
- **clear_db**: 指定のNeo4jデータベースをクリア（危険操作）。
- **config**: 使用するLLM/Embeddingの設定を表示。
- **full_pipeline**: `llm_doc → vectorize → llamaindex_vectorize` を一括実行。

---

## ディレクトリ構成（抜粋）

- `main_0905.py`: CLIエントリポイント。
- `main_helper_0905.py`: Neo4j/Chroma/LlamaIndex 連携のヘルパと設定クラス `Config`。
- `doc_parser/`: ドキュメント解析・Neo4jインポーター等。
- `help_preprocessor/`: EVOSHIP help preprocessing pipeline skeleton (Shift_JIS normalization, graph/vector loaders)
- `graphrag_gpt/ingest0903.py`: No LLM の解析・取り込み処理。
- `chroma_db_store/`: ChromaDB 永続化ディレクトリ。
- `data/src/`: 解析対象ドキュメント（例: `api.txt`）。
- `tests/`: テストコード。

---

## 必要条件

- Python 3.10+（推奨）
- Neo4j（APOCプラグイン推奨。グラフ検索を使う場合に必要）
- インターネット接続（OpenAI API を利用）

---

## 1. 環境変数（`.env`）

プロジェクトルートに `.env` を作成し、以下を設定してください。

```env
# Neo4j
NEO4J_URI="bolt://127.0.0.1:7687"
NEO4J_USER="neo4j"
NEO4J_PASSWORD="password"
NEO4J_DATABASE="neo4j"

# OpenAI
OPENAI_API_KEY="sk-..."

# 解析対象ドキュメント（任意。未指定時は data/src）
API_DOCUMENT_DIR="absolute/or/relative/path/to/docs"
```

補足:

- `.env` はプロジェクトルートに隠しファイルとして配置してください。
- Neo4j URI はローカル単一ノードの場合 `bolt://...` を推奨（`neo4j://` はルーティングの都合で置換されます）。

---

## 2. 依存関係のインストール

推奨: `uv`。代替: `pip`。

uv（推奨）:

```bash
uv pip install -r requirements.txt
```

pip（代替）:

```bash
pip install -r requirements.txt
```

注記（Windows PowerShell）: コマンドの連結は使用せず、1行ずつ実行してください。

---

## 3. 使い方（CLI）

基本形:

```bash
# uv 環境
uv run python main_0905.py -f <function>

# 通常のPython
python main_0905.py -f <function>
```

主な例:

```bash
# 解析→ベクトル化→LlamaIndex 準備まで一括
python main_0905.py -f full_pipeline

# ハイブリッドQA（対話）
python main_0905.py -f qa

# ハイブリッドQA（非対話）
python main_0905.py -f qa -q "関数 \"foo_bar\" の説明"

# Neo4j クリア（危険）
python main_0905.py -f clear_db --db neo4j -y

# 設定の確認
python main_0905.py -f config
```

オプション:

- `--question, -q`: `qa` の非対話実行用の質問文字列。
- `--db`: `clear_db` の対象データベース名。
- `-y, --yes`: 確認なしで危険操作を実行。

---

## 4. ワークフローの詳細

1. 解析（`nollm_doc` / `llm_doc`）

   - ドキュメントを解析し、API関数や説明を Neo4j に格納します。

2. ベクトル化（`vectorize`）

   - Neo4j から関数名・説明を取得し、ChromaDB に埋め込みとして保存します。

3. LlamaIndex 準備（`llamaindex_vectorize`）

   - 既存の Chroma コレクションから LlamaIndex のインデックスを構築します。

4. QA（`qa`）

   - ベクトル検索（Chroma）とグラフ検索（Neo4j）を統合し、包括的な回答を生成します。
   - グラフ検索が利用不可の場合はベクトル検索のみで動作します。

---

## 5. 設定の既定値（`main_helper_0905.Config`）

- Chroma 永続化パス: `chroma_db_store`
- Chroma コレクション: `api_documentation`
- 埋め込みモデル: `text-embedding-3-small`
- LLM モデル: `gpt-5-mini`（推論モデル設定に対応）

必要に応じて `.env` で上書き、または `Config` の実装を参照してください。

---

## 6. トラブルシューティング

- Neo4j 接続に失敗する: `NEO4J_URI/USER/PASSWORD/DATABASE` を確認。ローカルは `bolt://127.0.0.1:7687` を推奨。
- グラフ検索でエラー（APOC関連）: Neo4j に APOC プラグインを導入・有効化してください。未導入でもベクトル検索のみで動作します。
- `ChromaDB の永続化ディレクトリが見つからない/空` エラー: 先に `vectorize` を実行し、コレクションを作成してください。
- OpenAI API キー未設定: `.env` の `OPENAI_API_KEY` を設定してください。

---

## 7. 開発

- 型チェック・静的検査は `pyright` / 各種リンタ設定を利用。
- テストは `tests/` を参照。必要に応じて `uv run python -m unittest discover` を利用。

---

## 8. ライセンス

プロジェクトルートのライセンス表記がある場合はそれに従います。未記載の場合は研究用途を想定しています。
## help_preprocessor CLI

EVOSHIP ? Shift_JIS ????????????????????????????

1. `.env` ?????????????????:
   - `HELP_SOURCE_ROOT`: `EVOSHIP_HELP_FILES` ??????
   - `HELP_CACHE_DIR`: ????? JSON (`index_parse.json`) ???????????
   - `HELP_OUTPUT_DIR`: ????????????????
2. ??? `uv run help-preprocess --dry-run --sample-limit 5` ???????????????? index.txt ?????????????
3. ?????????????????????????????????????????????????????? `HELP_CACHE_DIR` ?? `index_parse.json` ??????????

