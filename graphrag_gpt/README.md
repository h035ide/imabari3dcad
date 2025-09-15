# GraphRAG GPT

このプロジェクトは、ベクトル検索（Chroma）とグラフ検索（Neo4j）を組み合わせた GraphRAG（Graph Retrieval-Augmented Generation）の最小実装です。`data/api.txt` をソースとして決定的なロジックで知識グラフを構築し、検索は「ベクトル」または「グラフ」ルートを選択して実行できます。

## 🚀 特徴

- ベクトル検索: Chroma + OpenAI Embeddings によるセマンティック検索
- グラフ検索: Neo4j + Cypher 生成チェーンによるグラフQA
- LLMレスな取り込み: `api.txt` を決定的に解析し、安定したグラフ構造（`sample.json` 同等形式）を生成
- 冪等な再構築: 取り込み時にNeo4jを初期化して再構築（実行毎に同じ結果）

## 📋 前提条件

- Python 3.8以上
- Neo4j（ローカルまたはクラウド）
- OpenAI互換APIキー（Embeddings および Chat モデル用）

## 🛠️ セットアップ

### 1. リポジトリのクローン
```bash
git clone <repository-url>
cd graphrag-gpt
```

### 2. 仮想環境の作成と有効化
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate    # Windows
```

### 3. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 4. 環境変数の設定
リポジトリ直下に `.env` を作成し、以下を設定してください。

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
OPENAI_API_KEY=your_openai_api_key
```

### 5. Neo4j の起動
Neo4j が起動済みで、URI/ユーザー/パスワードが正しいことを確認してください。

## 📖 使い方

### 取り込み（ingest）

```bash
python ingest.py
```

- `data/` 配下の `*.txt` を読み込み、前処理後に Chroma へ登録します。
- `data/api.txt` を解析し、決定的ロジックでグラフを組み立て Neo4j を再構築します。
- 実行時、Neo4j 上の既存ノード/リレーションは削除されます（`MATCH (n) DETACH DELETE n`）。

主なオプション:

- 前処理のみ（ベクトル登録・Neo4j再構築を行わない）
  ```bash
  python ingest.py --preprocess-only
  ```
- 前処理結果の書き出し
  ```bash
  python ingest.py --preprocess-out ./.preprocessed
  ```
- Embeddings 登録をスキップ
  ```bash
  python ingest.py --skip-embeddings
  ```
- 解析結果を JSON でエクスポート（`sample.json` と同形式）
  ```bash
  python ingest.py --export-json ./graph.json
  ```

### 質問（query）

```bash
# ベクトル検索（既定）
python query.py "スケッチ平面の作成方法を教えてください"

# グラフ検索
python query.py "スケッチ平面の作成方法を教えてください" graph
```

`vector`/`graph` を明示しない場合は `vector` が選択されます。

## 📁 プロジェクト構成

```
graphrag-gpt/
├── config.py         # 環境変数読み込み
├── ingest.py         # 取り込み: 前処理, Chroma登録, Neo4j再構築, JSON出力
├── query.py          # 質問実行: vector / graph ルート
├── requirements.txt  # 依存関係
├── data/
│   └── api.txt       # 解析対象API仕様（テキスト）
├── sample.json       # 決定的ロジックの出力例
└── venv/             # 仮想環境（任意）
```

## 🔧 設定の要点

- `config.py`: `.env` を読み込んで `NEO4J_*` と `OPENAI_API_KEY` を使用します。
- `ingest.py`: Chroma の保存先は `.chroma`（自動生成）。決定的ロジックで Neo4j を毎回初期化して再構築します。
- `query.py`: 既定ルートは `vector`。モデル名は必要に応じて調整してください。

## 🔍 ヒント（検索の使い分け）

- ベクトル検索（vector）: 用語や記述の曖昧さに強い、質問応答全般に適合。
- グラフ検索（graph）: エンティティや関係性に基づく正確な抽出が必要な場合に有効。

## 📝 付属データ

`data/api.txt` は 3D CAD ツールのコマンドスクリプト API 仕様の一部です。例:

- 「CreateSketchPlane のパラメータは？」
- 「スケッチ平面の軸方向はどう指定する？」

## 🚨 トラブルシューティング

- Neo4j 接続エラー:
  - Neo4j が起動しているか、`NEO4J_URI/USERNAME/PASSWORD` が正しいか確認
  - 例外: `RuntimeError: Neo4j に接続できません。起動を確認してください`
- OpenAI API エラー:
  - `OPENAI_API_KEY` の設定、利用上限を確認
- 依存関係エラー:
  ```bash
  pip install -r requirements.txt --upgrade
  ```

## 📄 ライセンス / 🤝 貢献

デモ用途のサンプルです。バグ報告や要望は Issue でお知らせください。