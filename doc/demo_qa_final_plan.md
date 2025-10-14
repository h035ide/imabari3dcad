# Demo API QA 最終実装計画

## 1. 目的とゴール
- `structured_api/demo_qa/` 以下に demo データベース向けのハイブリッド QA パイプラインを構築する。
- LangChain と LlamaIndex を補助的に利用しつつ、retriever・スコア統合・レスポンス整形は自前実装で統一。
- 密／疎ベクトル、全文検索、グラフ検索を統合し、比較検証済みの日本語回答とトレーサビリティ情報を提供する。
- 継続的リファクタリングとテストで運用しやすいモジュール構成を維持する。

## 2. ディレクトリ構成
```
structured_api/demo_qa/
├── __init__.py
├── cli.py                # CLI エントリポイント
├── config.py             # .env + YAML の設定ロードと検証
├── query_preprocessor.py # クエリ再生成・正規化・意図抽出
├── fusion.py             # 検索結果統合とリランキング
├── response_builder.py   # 回答生成と参照情報整形
├── retrievers/
│   ├── __init__.py
│   ├── dense.py          # 密ベクトル検索 (LangChain/LlamaIndex ラッパー)
│   ├── sparse.py         # TF-IDF/BM25 実装
│   ├── fulltext.py       # Whoosh ベース全文検索
│   └── graph.py          # Neo4j グラフ検索
├── pipeline/
│   ├── __init__.py
│   ├── layer_b.py        # Recall 強化 (QueryFusionRetriever 中心)
│   └── layer_a.py        # Precision 強化 (Cypher テンプレート適用)
├── debug.py              # ログ・ダンプ補助
└── tools/
    ├── build_sparse_index.py
    └── build_whoosh_index.py
```

## 3. 処理フロー概要
1. **設定ロード**: `cli.py` から `.env` と `config.yaml` を読み込み、必須キーを検証。
2. **クエリ前処理**: `query_preprocessor.generate_queries()` で元文／パラフレーズ／キーワード重視の複数クエリを生成し、`ParameterExtractionTool` を用いて意図・スロット候補を抽出。
3. **入口統合 (Layer B)**: `pipeline.layer_b.run_layer_b_pipeline()` が複数 retriever を並列実行し、Recall 重視のスロット候補を `{name_candidates, type_candidates, category_candidates, score}` 形式で出力。
4. **確定取得 (Layer A)**: `pipeline.layer_a.run_layer_a_pipeline()` が Layer B の候補を精査し、Cypher テンプレート T1〜T6 を優先順位 (例: T2→T3→T6) に従って適用、Neo4j から精度重視の結果を取得。
5. **スコア統合・リランキング**: `fusion.rerank_and_merge()` が正規化スコアを統合し、`ReRanker` クロスエンコーダーで再評価。グラフ裏付けをボーナス加点。
6. **ベクトル／グラフ比較**: `fusion.compare_vector_graph()` が結果整合性を判定し、矛盾時は警告。
7. **回答生成**: `response_builder.format_response()` がクラスタリングされた候補と参照情報を整形し、日本語で回答と追跡可能な表を出力。
8. **デバッグ・ダンプ**: `debug.py` が `--dump-intermediate` 指定時に JSON へ中間結果を保存。

## 4. 各コンポーネントの要点
- **CLI (`cli.py`)**: `argparse` でクエリ、検索モード、設定パス、Chroma/Neo4j 接続情報を受け取り、起動前に環境変数不足を検知。
- **設定 (`config.py`)**: `.env` と YAML をマージし、`retrieval.weights`、`rerank.thresholds`、`debug.level` などを提供。検証失敗時は修正例付きでエラー。
- **Retrievers**:
  - `dense.py`: LlamaIndex `QueryEngine` と LangChain `RetrievalQA` の双方をラップし、Chroma データストア設定を CLI オプションで上書き可能。
  - `sparse.py`: `scikit-learn` で TF-IDF と BM25 を生成し、結果は共通スキーマで返却。
  - `fulltext.py`: Whoosh インデックスを初期化。未生成時は `tools/build_whoosh_index.py` を案内。
  - `graph.py`: Neo4j ドライバを扱い、Cypher 実行結果を QA 共通フォーマットへ変換。
- **Pipeline Layer B**: QueryFusionRetriever を中心に、生成クエリごとに retriever を実行。LLM シノニム展開で Recall を補強。
- **Pipeline Layer A**: 軽量辞書・正規表現でスロット抽出後、テンプレート切替を制御。フォールバック順を明確にし、段階的に検索領域を絞る。
- **Fusion (`fusion.py`)**: スコア正規化ユーティリティを整備し、ソース種別・一致度を保持。リランキング後はクラスタリングし、重複を削除。
- **Response Builder**: パラメータや擬似コードなどのメタ情報を集約し、表形式で参照リンク・ソースを提示。ベクトルとグラフで差異がある場合は両方の見解を記載。
- **Debug**: ログレベルを `debug.level` で制御。追跡 ID を付与し、例外時の経路を記録。

## 5. データソースとインデックス
- **Neo4j**: `.env` の `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `NEO4J_DATABASE` を使用。ETL は `structured_api/api_entries_demo_etl.py` で実施。
- **Chroma**: 既定は `chroma_db_store/demo` で `demo_api_entries` コレクション。CLI で `--chroma-dir` / `--chroma-collection` を上書き可能。
- **疎ベクトル・全文検索**: 元データは `structured_api/data/structured_api.json`。`tools/build_sparse_index.py` と `tools/build_whoosh_index.py` で `data/sparse_index/demo/` と `data/whoosh_index/demo/` を生成し、CLI 起動時に存在チェックと生成コマンド案内を行う。

## 6. 実装ステップ
1. 環境変数ロード・バリデーション (`config.py` + CLI) を実装し、ユニットテストを追加。
2. クエリ前処理モジュールを整備。LLM 依存部分は関数分割しモック容易にする。
3. 密／疎／全文／グラフの retriever を実装し、共通結果フォーマットを確立。
4. Layer B → Layer A のパイプラインを構築し、スロット候補生成から Cypher 実行までのインターフェースを明文化。
5. `fusion.py` でスコア統合と `ReRanker` 連携を実装。ボーナススコアや整合性チェックを組み込む。
6. `response_builder.py` で回答整形と参照情報の表形式出力を実装。
7. CLI 入出力と `debug.py` のオプション (`--dump-intermediate`) を追加。
8. インデックス生成ツールを作成し README / ヘルプに反映。
9. 単体テスト・統合テストを整備し、`uv run black` / `ruff` / `pytest` で品質確認。

## 7. 検証計画
- **機能テスト**: 各検索モード単体を起動し、想定フィールドが返るかを確認。
- **統合テスト**: `--mode auto` でハイブリッド検索を実行し、スコア統合とリランキングの結果を検証。
- **フォールバックテスト**: クロスエンコーダー未導入環境で LLM ベースのリランキングに自動切替されることを確認。
- **設定切替テスト**: Neo4j/Chroma 接続情報を変更し、CLI オプションで上書きできるかを確認。
- **品質テスト**: `uv run black`, `uv run ruff check`, `uv run pytest` を CI 相当で実行。主要フローはモックを活用し、外部依存を遮断。

## 8. 運用・拡張上の留意点
- Retrievers やリランカーはインターフェースベースで実装し、Elasticsearch 等の追加も差し替えで対応可能にする。
- 並列検索にはタイムアウトと結果件数制限を設け、過負荷時のフェイルセーフを実装。
- ログにはスコア、テンプレート選択理由、再現用追跡 ID を出力し、デバッグ容易性を担保。
- 秘密情報は `.env` 管理とし、生成したベクトルストアやインデックスは `.gitignore` に追加する。

## 9. インターフェースとデータモデル仕様
- Retrievers 層には `BaseRetrieverProtocol`（`retrieve(query: QueryBundle) -> List[ScoredNode]` を想定）を定義し、LangChain/LlamaIndex 由来の実装は DI 経由で差し込む。
- Layer B の I/O は `pydantic` モデルで固定する。
  - `QueryVariant`（元文／パラフレーズ／キーワード種別と生成根拠を保持）。
  - `SlotCandidate`（`name: str`, `score: float`, `source: Literal["dense","sparse","graph",...]`）。
  - `LayerBOutput`（`query_variant: QueryVariant`, `slot_candidates: Dict[str, List[SlotCandidate]]`, `debug: Dict[str, Any]`）。
- Layer A は `LayerBOutput` を受け、`TemplateDecision`（採用テンプレートと根拠）、`CypherResult`（取得したノード・リレーションの標準化構造）を返却する。
- `response_builder` は `HybridAnswer`（回答本文、証拠リスト、比較サマリ）を返すことで CLI と API の両方から共通利用可能にする。

## 10. スコア正規化と統合アルゴリズム
- 各 retriever のスコア分布を事前に計測し、`fusion.py` では以下の順序で処理する。
  1. ソース別に Min-Max 正規化（必要に応じて Z-Score に切替可能な設定フラグを保持）。
  2. `retrieval.weights` に従って線形結合し、`graph` 結果には `graph_bonus` を加算。
  3. クロスエンコーダー `ReRanker` には上位 `config.rerank.top_k` 件のみ渡し、スコアを再付与。
  4. `cluster_threshold` に基づくヒエラルキー型クラスタリングで重複を削除し、クラスタ代表にソース別統計を保持。
- 正規化・重み付け結果は `debug.py` から JSON ダンプ可能にし、閾値調整時の検証を容易にする。

## 11. LLM / リランカー運用方針
- クエリ前処理での `ChatOpenAI` 呼び出しは `config.query_generation.max_calls` を上限とし、結果は SQLite ベースのローカルキャッシュで再利用。
- レート制限エラー時は BM25 ベースのフォールバックモードへ自動切替し、警告ログを出力。
- `ReRanker` は GPU 有無に応じてバッチサイズを調整し、`config.rerank.batch_size` として設定可能にする。未導入時は LLM ベースのスコアリングプロンプトへ切替。
- LangChain CallbackManager と LlamaIndex observability API を連携させ、LLM 呼び出し時間とトークン使用量を記録する。

## 12. 設定優先順位と型バリデーション
- `config.py` で `pydantic-settings` を採用し、CLI > 環境変数 > YAML > デフォルトの優先順位を明文化。
- 数値・真偽値は `pydantic` の型変換に任せ、文字列からの暗黙変換は抑止。検証失敗時は CLI に修正例を表示。
- インデックス生成ツールでは出力先ディレクトリを CLI 引数で受け取り、`config.yaml` からも参照できるようにする。

## 13. テスト詳細シナリオ
- Retrievers: 5 件程度のダミーコーパスを用いた期待値テストを追加し、`BaseRetrieverProtocol` に準拠した結果が返るか検証する。
- Pipeline: Layer B/A は依存をモック化し、テンプレート選択やフォールバック順序をシナリオテストで確認。
- Fusion: 正規化・重み付け・クラスタリングの各フェーズをユニットテスト化し、閾値変更時も破綻しないことを保証。
- Response Builder: 表形式出力とグラフ・ベクトル比較メッセージをスナップショットテストで固定。
- Debug: JSON ダンプ構造がスキーマに従うことを検証し、追跡 ID が常に付与されることを確認。

## 14. 最終チェックリスト
- [ ] 必須環境変数と `.env` サンプルを README に追記し、設定優先順位を周知した。
- [ ] `tools/` 以下のインデックス生成スクリプトを実装し、CI で存在確認を行うジョブを追加した。
- [ ] Layer B/A/Pipeline/Fusion/Response Builder の `pydantic` モデルを定義し、型互換性テストを通過した。
- [ ] LLM キャッシュとフォールバックが統合テストで確認できるよう、再現手順を doc/README に記録した。
- [ ] Neo4j テンプレート T1〜T6 の仕様書（入力／出力フィールド、適用条件）を作成した。

## 15. ツール連携による AI エージェント化の方針
- **エージェントの役割設計**: `query_preprocessor` で抽出した意図・スロット候補を、LangChain の `AgentExecutor` 相当のステートマシンに渡し、Layer B/A のパイプラインや `response_builder` をツール（`Tool`/`Runnable`) として逐次呼び出す。CLI/API からは「質問 → エージェント初期化 → 実行結果返却」の一貫したハンドラを提供する。
- **ツール郡の切り出し**: `retrievers/` 各モジュールを LangChain/LlamaIndex の `Tool` としてラップし、`tools/build_sparse_index.py` や `tools/build_whoosh_index.py` をメンテナンスタスク用の別ツールに登録。エージェントは Layer B 実行前に必要なインデックス存在チェックをツール経由で行う。
- **意思決定ロジック**: Layer B/A の制御フローを `StateGraph` もしくは LlamaIndex の `AgentWorkflow` へ移植し、スコア閾値やテンプレート選択を状態遷移として表現する。これにより、フォールバック（例: LLM リランカー不在時の BM25 代替）をエージェントポリシーで明示できる。
- **メモリとコンテキスト管理**: `debug.py` で生成する追跡 ID と中間 JSON を会話メモリに保存し、連続クエリ時に前回のスロット候補やテンプレート選択理由を参照できるようにする。LangChain の `ConversationBufferMemory` 互換クラスを用意し、Graph/Vector 結果の比較サマリを永続化する。
- **監視・チューニング支援**: エージェント実行時にツール呼び出しログを構造化し、Neo4j/Chroma 接続失敗やスコアドリフトを検知したら専用の「ヘルスチェックツール」でリカバリ手順（再接続、キャッシュクリア、代替モード起動）を提案する。CI ではエージェント経由の E2E テストケースを追加し、状態遷移とツール呼び出し順序が想定通りか検証する。
- **拡張余地**: 将来的に社内 API やワークフロー自動化ツールと統合する場合は、エージェントのツール登録レイヤーに外部 API コネクタを追加し、アクセス制御や監査ログ方針（Section 8 参照）を共通で適用する。
