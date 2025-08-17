### code_parser モジュール概要

PythonソースをTree‑sitterで解析し、コード構造を詳細なNeo4jグラフに格納します。関数/クラス/呼び出し/代入/属性/パラメータ等を網羅し、循環/認知的複雑度などのメトリクスも記録します。任意でLLM説明を各ノードに付与可能です。

### 主な構成
- `parse_code.py`: CLI。対象ファイルを解析→`TreeSitterNeo4jAdvancedBuilder` でNeo4jへ格納。
- `treesitter_neo4j_advanced.py`: 解析/ノード生成/関係生成/統計出力を担当。
  - ノード種別（例）: `Module`, `Class`, `Function`, `Variable`, `Parameter`, `Import`, `Call`, `Assignment`, `Attribute`...
  - 関係（例）: `CONTAINS`, `CALLS`, `ASSIGNS`, `HAS_ATTRIBUTE`, `IMPORTS`, `HAS_PARAMETER`, `RETURNS`...
  - メトリクス: 行数/関数数/複雑度など。LLM説明の付与にも対応。

### 環境変数(.env)
- `NEO4J_URI`, `NEO4J_USERNAME` or `NEO4J_USER`, `NEO4J_PASSWORD`
- 任意: `OPENAI_API_KEY`（LLM説明を有効化する場合）

### 使い方
```bash
# デフォルト対象（evoship/create_test.py）
python code_parser/parse_code.py

# 任意ファイルを指定
python code_parser/parse_code.py path/to/file.py --db-name treesitter --no-llm
```

### 注意点
- `store_to_neo4j()` は対象データベースの既存ノードを削除してから投入します。専用DB（例: `treesitter`）での使用を推奨。
- 本グラフはAPIグラフ（`doc_paser`）とはスキーマが異なります。混在を避けるためDB名を分ける運用を推奨します。


