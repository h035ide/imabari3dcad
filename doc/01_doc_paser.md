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



### ワークフロー（全体）
1) 解析（`doc_paser.py`）
   - `load_api_document()` で原文（APIドキュメント＋引数の型と書式）を連結読込
   - `load_prompt()` と `load_json_format_instructions()` でプロンプトとJSON仕様を準備
   - `ChatOpenAI(model="gpt-5-mini", reasoning_effort="medium", response_format=json_object)` を生成
   - `llm.invoke(prompt.format(...)) → json.loads()` で厳密なJSONへ変換
   - 必要に応じて `postprocess_parsed_result()`（型名正規化・配列情報付与・必須推定・引数`position`付与）
   - `save_parsed_result()` で `doc_paser/parsed_api_result.json` に保存

2) 取込（`neo4j_importer.py`）
   - `.env` から `NEO4J_URI` / `NEO4J_USER or NEO4J_USERNAME` / `NEO4J_PASSWORD` を読込
   - JSON（`doc_paser/parsed_api_result.json`）をロードし `Neo4jImporter.import_data()` を実行
   - `Type` をUNWINDで一括 `MERGE`
   - `api_entries` を種別で分岐
     - 関数: `Function` 作成 → `Parameter` を順序付きで `HAS_PARAMETER{position}` 接続 → `HAS_TYPE` で `Type` or `ObjectDefinition` にリンク → `RETURNS` 接続
     - オブジェクト定義: `ObjectDefinition` 作成 → `HAS_PROPERTY` で属性を接続 → 属性に `HAS_TYPE`
   - 戻り値オブジェクト経由の依存: `FEEDS_INTO{via_object}` を一括生成

3) 検査/メンテ（任意）
   - `check_detailed.py`/`check_relationships.py` で統計と重複確認
   - `cleanup_duplicates.py` で重複/孤立ノード除去、`clear_database.py` で初期化


### 関数レベルのワークフロー（doc_paser.py）
- `read_file_safely(path, encoding)`
  - 例外安全にテキストを読込（FileNotFound/UnicodeDecode/IO を個別化）

- `load_api_document(api_doc_path, api_arg_path)`
  - `read_file_safely` で両ファイルを読込 → 「APIドキュメント」「引数の型と書式」を連結して返却

- `load_prompt(file_path=None)` / `load_json_format_instructions(file_path=None)`
  - 引数省略時は埋め込み既定文を返却、指定時は `read_file_safely` で外部ファイルを読込

- `write_file_safely(path, content)` / `save_parsed_result(parsed_result, output)`
  - ディレクトリ作成→UTF-8で書込、`save_parsed_result` は `json.dumps(indent=2, ensure_ascii=False)` を経て保存

- `normalize_type_name(type_name)`
  - 代表的型名の正規化（`string|str→文字列`, `float|double|number→浮動小数点`, `int|integer→整数`, `boolean|bool→bool`, ほか幾何/要素系）

- `enrich_array_object_info(param)`
  - `type_name` に「(配列) / 配列 / (array)」を含む場合、`array_info={is_array, element_type, ...}` を付与

- `infer_is_required(param)`
  - `constraints` と `description_raw` を結合し、「空文字不可/必須」で `is_required=True`、「空文字可」で `False`

- `postprocess_parsed_result(parsed_result)`
  - `returns.type_name` と `params[].type_name` を正規化
  - 各パラメータに `enrich_array_object_info` と `infer_is_required` を適用し、`position` を連番で付与

- `main()`（LLM解析の実行）
  - `.env` 読込済み → ドキュメント/プロンプト/JSON仕様を準備
  - `ChatOpenAI(..., response_format=json_object)` を生成し `invoke` 実行
  - `json.loads(response.content)` で受け取り、整形表示→ `save_parsed_result()`
  - 例外捕捉しヒント表示（APIキー未設定等）


### 関数レベルのワークフロー（neo4j_importer.py）
- `Neo4jImporter.__init__(uri, user, password)` / `close()`
  - ドライバ生成/クローズ

- `import_data(data)`
  - セッション内で順に `_import_type_definitions` → `_import_api_entries` → `_create_dependency_links`

- `_import_type_definitions(session, type_definitions)`
  - `UNWIND $types AS type_data` → `MERGE (t:Type {name})` → `SET t.description`

- `_import_api_entries(session, api_entries)`
  - `entry_type` で分岐：`function`→`_create_function_graph`、`object_definition`→`_create_object_definition_graph`

- `_create_function_graph(session, func)`
  - `MERGE (f:Function {name})` と主要プロパティ
  - `params[]` を反復：`MERGE (p:Parameter {name,parent_function})` → `MERGE (f)-[:HAS_PARAMETER {position}]->(p)`
  - `HAS_TYPE` で `ObjectDefinition` を優先参照、なければ `Type` を `MERGE`
  - `returns` があれば `MERGE (f)-[:RETURNS]->(rt:Type)`

- `_create_object_definition_graph(session, obj)`
  - `MERGE (od:ObjectDefinition {name})` と主要プロパティ
  - `properties[]`：`MERGE (p:Parameter {name,parent_object})` → `MERGE (od)-[:HAS_PROPERTY]->(p)` → `HAS_TYPE` 接続

- `_create_dependency_links(session)`
  - クエリ1本で `Function -[:RETURNS]-> ObjectDefinition` とそれを要求する `Function` の `Parameter` を突き合わせ、`FEEDS_INTO{via_object}` を生成

- `main()`
  - `.env` 確認 → インポータ生成 → `parsed_api_result.json` 読込 → `import_data()` 実行（ファイル未検出時はヒント出力）


### 図（`doc_paser.drawio`）
- シート `doc_paser` に全体フロー、`doc_paser_functions` に関数レベルのフローを追加（本ドキュメントの内容と対応）。
