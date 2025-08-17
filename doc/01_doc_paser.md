### doc_paser モジュール概要

自然文のAPIドキュメントをLLMで厳密に解析して `parsed_api_result.json` を生成し、Neo4jへ取り込みます。API関数・オブジェクト定義・型・パラメータとその関係をグラフ化し、後段の検索・コード生成に供給します。

### 主なスクリプト
- `doc_paser.py`: 原文読込＋プロンプト生成＋LLM呼び出し→JSON出力。型名正規化・配列情報付与・必須推定などの後処理を実施。
- `neo4j_importer.py`: JSONをNeo4jへ投入。ノード(`Type`/`ObjectDefinition`/`Function`/`Parameter`)と関係(`HAS_PARAMETER`/`HAS_PROPERTY`/`HAS_TYPE`/`RETURNS`/`FEEDS_INTO`)を作成。
- `check_detailed.py`/`check_relationships.py`: ノード/関係の統計・重複確認。
- `cleanup_duplicates.py`/`clear_database.py`: 重複関係のクリーンアップ・DB初期化。

### 環境変数(.env)
- `OPENAI_API_KEY`（LLM解析）
- `NEO4J_URI`, `NEO4J_USER` or `NEO4J_USERNAME`, `NEO4J_PASSWORD`

### 使い方
1) 解析（JSON生成）
```bash
python doc_paser/doc_paser.py
```
生成物: `doc_paser/parsed_api_result.json`

2) Neo4jへ投入
```bash
python doc_paser/neo4j_importer.py
```

### 生成されるグラフの要点
- ノード
  - **Type**: 例「長さ」「角度」「点」など。
  - **ObjectDefinition**: 「〜パラメータオブジェクト」等。
  - **Function**: API関数。
  - **Parameter**: 関数パラメータ/オブジェクト属性。
- 関係
  - **HAS_PARAMETER {position}**: 関数→パラメータ（順序保持）。
  - **HAS_PROPERTY**: オブジェクト定義→属性。
  - **HAS_TYPE**: パラメータ/属性→型（`Type` か `ObjectDefinition` に接続）。
  - **RETURNS**: 関数→戻り値型。
  - **FEEDS_INTO {via_object}**: 関数Aの戻り値(オブジェクト)が関数Bの引数として使われる依存関係（Builderパターンの明示化）。

### LLM解析のプロンプト方針
- 出力はJSONオブジェクトのみ（Markdown禁止）。
- 「引数の型と書式」を優先して `type_definitions` を抽出。
- 「APIドキュメント」から `api_entries` を抽出し、`entry_type`（function/object_definition）を厳密に分類。

### 注意点 / 既知の課題
- `doc_paser.py` はLLMレスポンスをJSONとして直接パースします。失敗時は出力を確認してください。
- 型名は `normalize_type_name()` で正規化（例: `string`→`文字列`）。
- `FEEDS_INTO` の作成は、戻り値が `ObjectDefinition` で、他関数のパラメータ型として参照される場合に自動生成されます。


