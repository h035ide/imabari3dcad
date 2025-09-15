### 開発概要（共有用）

本リポジトリで進めている自動コード生成基盤の全体像と各モジュールの要点をまとめました。詳細は各モジュール別ドキュメントを参照してください。

- [01_doc_paser.md](./01_doc_paser.md)
- [02_code_parser.md](./02_code_parser.md)
- [03_code_generator.md](./03_code_generator.md)

### システム全体フロー（高レベル）

```mermaid
flowchart LR
    subgraph A[ドキュメント解析ライン]
        SRC[(API原文: data/src)] --> P1[LLM解析\n(doc_paser/doc_paser.py)]
        P1 --> JSON[parsed_api_result.json]
        JSON --> NEO4J_A[Neo4j: APIグラフ\n(Type/ObjectDefinition/Function/Parameter)]
        NEO4J_A -->|code_generator/db/ingest_to_chroma.py| CHROMA[(ChromaDB)]
    end

    subgraph B[コード解析ライン]
        PY[(Pythonソース)] --> P2[Tree-sitter解析\n(code_parser/parse_code.py)]
        P2 --> NEO4J_B[Neo4j: コードグラフ\n(Module/Class/Function/...)]
    end

    CHROMA --> AGENT[コード生成エージェント\n(code_generator/main.py)]
    NEO4J_A -. 検索/関連取得 .-> AGENT
    NEO4J_B -. 参照(将来拡張) .-> AGENT
```

### 役割の要点
- **doc_paser**: EVO.SHIP API等の自然文ドキュメントをLLMで構造化(JSON)→Neo4jへ取込。API間の依存(Builderパターン)もグラフ化。
- **code_parser**: PythonコードをTree‑sitterで解析し、コード構造の詳細グラフをNeo4jへ格納（任意でLLMによるノード説明付与）。
- **code_generator**: LangChainベースのエージェント。前検証→生成→静的検証→テスト実行の自己修正ループ。Graph/Vector検索を統合。

### 先に読むと良いもの
- `code_generator/doc/COMPREHENSIVE_SYSTEM_ANALYSIS_2025.md`
- `code_generator/doc/HYBRID_RAG_DESIGN.md`


