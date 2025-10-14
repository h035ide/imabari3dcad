# Demo API QA 実装計画

## 目的
- `structured_api/demo_qa` 配下に、demo データベース向けの高度な QA システムを実装する。
- LangChain と LlamaIndex を併用しつつ、retriever やユーティリティは `structured_api` 内で再実装する。
- 密ベクトル・疎ベクトル・全文検索・グラフ検索を統合したハイブリッド検索を実現し、比較・統合結果を日本語で提示できるようにする。
- 開発中は常にリファクタリングを検討し、読みやすく簡潔なコードを維持する。整形には `uv run black "<ファイル名>"` を使用する。

## 全体アーキテクチャ
- CLI エントリ (`structured_api/demo_qa/cli.py` ※元の `demo_api_qa.py` から分離)
  - `argparse` でクエリや検索モード、ストア設定を受け取る。
  - `.env` を読み込み必要な環境変数（OpenAI、Neo4j、Chroma 等）を検証。
- クエリ前処理レイヤ (`structured_api/demo_qa/query_preprocessor.py`)
  - `ChatOpenAI` を用いたクエリ正規化と多様なクエリ生成（元文／キーワード重視／パラフレーズ）。
  - 既存 `ParameterExtractionTool` による意図・パラメータ抽出でルーティングを支援。
- 検索レイヤ (`structured_api/demo_qa/retrievers/` 以下)
  - **密ベクトル**: LlamaIndex / LangChain API を用いながらも、`structured_api/demo_qa/retrievers/dense.py` で初期化と検索を再実装する。
  - **疎ベクトル**: TF-IDF/BM25 を `structured_api/demo_qa/retrievers/sparse.py` に実装。
  - **全文検索**: Whoosh ラッパーを `structured_api/demo_qa/retrievers/fulltext.py` に実装。
  - **グラフ検索**: Neo4j アクセスを `structured_api/demo_qa/retrievers/graph.py` に実装し、必要に応じて LangChain/LlamaIndex のクラスを内部で利用。
- スコア統合・リランキング (`structured_api/demo_qa/fusion.py`)
  - 各検索結果を正規化スコア化し、ソース種別・一致度を記録。
  - `code_generator.rerank_feature.reranker.ReRanker` でクロスエンコーダーによる再評価。
  - グラフ裏付けの有無をボーナスとして反映。
- 入口統合レイヤ B (`structured_api/demo_qa/pipeline/layer_b.py`)
  - Recall 強化フェーズ。 `QueryFusionRetriever` を中心に、ベクトル / BM25 / Whoosh / Neo4j フルテキスト検索 / LLM シノニム展開を統合して「スロット候補（名前・型・カテゴリ等）」を生成。
  - 生成されるスロット候補の構造は `{name_candidates: [...], type_candidates: [...], category_candidates: [...], score: ...}` を想定。
- 確定取得レイヤ A (`structured_api/demo_qa/pipeline/layer_a.py`)
  - Precision 確保フェーズ。B レイヤーの候補をもとにスロット抽出（軽量辞書＋正規表現）を行い、Cypher テンプレート `T1〜T6` を選択して Neo4j に問い合わせる。
  - フォールバック順序（T2 → T3 → T6）の制御や直接 Cypher への段階的切替（関数名 → パラメータ名 → 型名 → ステータス）を実装。
- 回答生成 (`structured_api/demo_qa/response_builder.py`)
  - 上位候補をクラスタリングし、メタ情報（パラメータ・擬似コードなど）を集約。
  - ベクトル・グラフ結果の整合性チェック、差異があれば両方提示。
  - 参照情報の表形式出力でトレーサビリティを確保。

## ディレクトリ構成とファイル分割（新規）
- `structured_api/demo_qa/`
  - `__init__.py`
  - `cli.py` : CLI エントリポイント。`demo_api_qa.py` から移動し、薄いラッパー構成で保守。
  - `config.py` : 実行時設定のロードとバリデーション。`.env` と YAML をマージするロジックを明確化。
  - `query_preprocessor.py` : クエリ生成・正規化・意図抽出ロジック。LLM 依存部分は極力関数に分割しテスト容易化。
  - `fusion.py` : 検索結果統合、スコア正規化、リランキング制御。ステップごとにユーティリティ関数を用意しリファクタリングしやすくする。
  - `response_builder.py` : 回答テキストと参照情報の整形。フォーマット処理を関数化し再利用性を確保。
  - `retrievers/`
    - `__init__.py`
    - `dense.py` : LlamaIndex / LangChain ベクトル検索の自前実装。
    - `sparse.py` : scikit-learn などを用いた TF-IDF / BM25 の自前実装。
    - `fulltext.py` : Whoosh を `structured_api` 内でセットアップするラッパー。
    - `graph.py` : Neo4j / グラフ検索の自前実装（Cypher 生成とクエリ実行）。
  - `pipeline/`
    - `__init__.py`
    - `layer_b.py` : 入口統合（Recall）ロジック。QueryFusionRetriever を組み込み、スロット候補を生成。
    - `layer_a.py` : 確定取得（Precision）ロジック。スロット抽出と Cypher テンプレート選択、フォールバック制御を担当。
  - `debug.py` : デバッグ補助（ステップごとのログ整形、結果ダンプ）。
- ルートに残す `structured_api/demo_api_qa.py` は CLI 起動用 thin wrapper（`from .demo_qa import cli`）として最小化し、構造を `structured_api` 内で完結。

## 設定ファイル
- `structured_api/demo_qa/config.yaml`
  - `chroma.persist_directory`, `chroma.collection`
  - `neo4j.database`, `neo4j.query_timeout`
  - `retrieval.weights`（dense/sparse/fulltext/graph の重み）
  - `rerank.model_name`, `rerank.thresholds`
  - `debug.level`, `debug.dump_dir`
- `config.py` で YAML を読み込み、`.env` 値とマージ。
- CLI から `--config path/to/config.yaml` で切替可能。

## デバッグ指向の設計
- 共通 `logging` 設定を `config.yaml` の `debug.level` で制御し、`DEBUG` 時は各レイヤの入力・出力を記録。
- `debug.py`
  - クエリ生成結果、各検索モードのスコア、リランキング前後のリストを構造化して出力。
  - `--dump-intermediate` オプションで JSON ファイルに保存し、再現性を確保。
- エラーハンドリング
  - 例外発生時は検索モード別のログを参照できるように追跡 ID を付与。
  - 環境変数・設定不足は CLI 起動時に即座に検出し、修正例を提示。
- 単体テスト向けにモジュール化
  - 各ファイルを関数単位で設計し、依存を注入（API クライアントや retriever を引数で受け取る）。
  - モック容易化によりデバッグ／テストを効率化。

## コンポーネント詳細
- `load_env_and_validate()`
  - `.env` の読み込みと必須キー検証、不足時のガイダンス表示。
- `generate_queries(question: str) -> List[str]`
  - クエリ再生成ロジック。LangChain LLM を通じて多様な検索語を生成。
- `build_vector_qa(...)`
  - LlamaIndex ベースのクエリエンジンを構築。Chroma パス／コレクションは CLI から上書き可。
- `build_langchain_vector_qa(...)`
  - LangChain `RetrievalQA` による密ベクトル検索のフォールバック。
- `build_sparse_searchers(...)`
  - TF-IDF/BM25 の検索器をロードし、クエリごとの結果を返却。
- `build_fulltext_searcher(...)`
  - Whoosh インデックスを使用した全文検索。
- `build_graph_qa(...)`
  - LlamaIndex Graph QueryEngine と LangChain `GraphCypherQAChain` のラッパーを用意。
- `run_layer_b_pipeline(...)`
  - QueryFusionRetriever を中心とした入口統合（Recall）処理。生成クエリごとに retriever を実行し、スロット候補を構造化して返却。
- `run_layer_a_pipeline(...)`
  - layer_b のスロット候補を受け取り、スロット抽出→テンプレート選択→Cypher 実行→結果整形を行う。
  - テンプレート適用順序（T1〜T6）の優先度とフォールバックルールを明記し、最終的な候補の精度を高める。
- `run_hybrid_search(queries, configs)`
  - レイヤーB/Aを統合するオーケストレーション関数として扱い、従来のハイブリッド検索ロジックを段階的に整理。
- `rerank_and_merge(results)`
  - クロスエンコーダーを用いたリランキングとクラスタリング。
- `compare_vector_graph(merged_results)`
  - ベクトル／グラフ候補の一致度をスコア化し、矛盾時に警告メッセージ生成。
- `run_hybrid_search(queries, configs)`
  - 各検索モードを並列実行し、結果を共通フォーマットに変換。
- `rerank_and_merge(results)`
  - クロスエンコーダーを用いたリランキングとクラスタリング。
- `compare_vector_graph(merged_results)`
  - ベクトル／グラフ候補の一致度をスコア化し、矛盾時に警告メッセージ生成。
- `format_response(...)`
  - 最終回答と参照情報、スコア概要を整形して CLI に表示。

## データソースと切替
- Neo4j
  - `.env` の `NEO4J_DATABASE` で demo データベースを指定。
  - 既存 ETL (`structured_api/api_entries_demo_etl.py`) を実行してデータ投入。
- Chroma
  - 既定は `chroma_db_store/demo` 配下に新規コレクション（例: `demo_api_entries`）を作成。
  - CLI オプション `--chroma-dir`/`--chroma-collection` で切替可能。
- 疎ベクトル／全文
  - 元データは `structured_api/data/structured_api.json` を使用。
  - `data/sparse_index/` および `data/whoosh_index/` は未生成のため、専用スクリプトを用意し `demo` コレクション向けに事前ビルドする。
  - インデックス生成手順
    1. `structured_api/data/structured_api.json` から必要フィールド（API 説明、擬似コードなど）を抽出。
    2. `structured_api/demo_qa/tools/build_sparse_index.py`（新規）で TF-IDF/BM25 を構築し `data/sparse_index/demo/` に保存。
    3. `structured_api/demo_qa/tools/build_whoosh_index.py`（新規）で Whoosh インデックスを `data/whoosh_index/demo/` に作成。
  - CLI 起動時、インデックスが存在しなければ警告し、生成コマンドを提示する。

## 実装ステップ
1. 依存モジュール読み込みと環境変数バリデーションの実装。
2. クエリ再生成・意図抽出モジュールを整備。
3. 各検索モードの初期化ラッパーと結果フォーマット共通化。
4. ハイブリッド検索オーケストレーション（並列実行・スコア正規化）。
5. リランキングと結果統合、比較ロジックの実装。
6. CLI 入力・出力整形、詳細表示オプションの実装。
7. コードレビューの度にリファクタリングポイントを洗い出し、読みやすさを改善。
8. 単体・統合テスト、README 追記（必要に応じて）。

## 検証計画
- **ベースライン検証**: 各検索モードが単独で動作し、結果が返ることを手動テスト。
-- **統合検証**: `--mode auto` で複数クエリを実行し、スコア統合・比較・リランキングの挙動を確認。
-- **フォールバック検証**: クロスエンコーダー未導入環境で LLM リランキングに自動切替されることを確認。
- **データ切替検証**: Neo4j/Chroma のデモ用設定を変更し、CLI オプションで上書きできるかをテスト。
- **コード品質検証**: 主要ファイルに対して `uv run black "<ファイル名>"` を実行し、書式／インデントが揃っているか確認。

## 追加検討事項
- 大規模データ対応: 並列検索のタイムアウト設定、結果件数の制限。
- ログ出力: 検索スコアや選択理由を DEBUG ログに記録して解析可能にする。
- 拡張性: Elasticsearch など外部全文検索や追加リランカーを差し替えられる構造を保持。

