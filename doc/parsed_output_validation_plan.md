# API抽出検証パイプライン実装計画

## 1. 概要

### 1.1 目的
- 入力データ（`data/src/api.txt`・`data/src/api_arg.txt`）と出力データ（`doc_parser/parsed_api_result.json`）の差異を自動検証し、網羅性・整合性・品質を定量化。
- 欠落や余剰を可視化し、LangGraph ベースの再抽出で回帰に強いパイプラインを構築する。

### 1.2 スコープ
- 対象: `doc_parser/parsed_api_result.json`（生成物）
- 入力: `data/src/api.txt`（API仕様）, `data/src/api_arg.txt`（型仕様）
- 出力: 差分レポート（JSON/テキスト）、検証サマリ（カバレッジ指標）、CI/ローカルでの自動実行

---

## 2. 検証要件とメトリクス

### 2.1 検証観点
- 型網羅チェック
  - 入力の型集合 S_arg と、出力 `type_definitions[].name` の集合 S_out を比較。
  - 結果: 欠落型、余剰型、別名（正規化による吸収）一覧。
- API網羅チェック
  - 入力 `api.txt` からエントリ名集合 F_src（関数/オブジェクト）を抽出。
  - 出力 `api_entries[].name` の集合 F_out と比較（欠落/余剰）。
- 項目整合チェック
  - 各 API について、パラメータの数・順序・名前・型・必須/任意・デフォルト値、戻り値型/配列を照合。
  - 型は `DataProcessor.normalize_type_name()` で正規化して比較。
- リンク一貫性チェック
  - 抽出結果に付与する `source_refs`（チャンク開始/終了行・ファイル名）が入力元と整合しているかを検証。
  - Neo4j/Chroma での同一判定用に生成するキー（例: `canonical_id`、`source_span_hash`）の重複・欠落を確認。
- 設計整合チェック（LangChain/LlamaIndex連携）
  - LangChain Tool 呼び出しログと `graph_state.execution_trace` の整合を確認。
  - LlamaIndex の `Node` メタデータに含めた `doc_source_id`・`span` が抽出結果の `source_refs` と一致しているかを突合。

### 2.2 メトリクス
- 型カバレッジ = |S_out ∩ S_arg| / |S_arg|
- APIカバレッジ = |F_out ∩ F_src| / |F_src|
- パラメータ一致率 = 一致パラメータ数 / 総パラメータ数
- 重大差分件数（例: 欠落API、型不一致）
- リンク完全率 = `source_refs` が有効かつユニークな API 件数 / 総 API 件数
- 自己修正成功率 = LangGraph 再抽出により解消された差分件数 / 再抽出対象件数
- ベースライン比較での回帰指標（後述の基準を満たすこと）

---

## 3. システム構成

### 3.1 LangGraph オーケストレータ (`doc_parser/pipeline_langgraph.py`)
- LangChain の `Runnable` と LangGraph の `StateGraph` を併用し、ノードをクラス実装で提供。
- `GraphState` dataclass に `chunk_stats`, `function_stats`, `retry_queue`, `extraction_outputs`, `validator_report`, `execution_trace` を保持。

### 3.2 LlamaIndex リポジトリ (`doc_parser/index_builder.py`)
- `SimpleDirectoryReader` + `SentenceSplitter` で `api.txt` をチャンク化し、`MetadataExtractor` により `doc_source_id`・`span_start`・`span_end`・`heading_path` を付与。
- 生成した `VectorStoreIndex` を Chroma ストアへ永続化し、LangChain の `Chroma` retriever と共有メタデータ構造を用意。

### 3.3 自己修正エージェント (`doc_parser/self_heal.py`)
- LangChain の `Tool` として `retrieve_source(tool_input)`（LlamaIndex→原文返却）と `call_extractor(tool_input)`（LLM 抽出）を定義。
- LangGraph の `RetryController` ノードから差分項目を受け取り、原文スパンを再取得して再抽出フローにリダイレクト。

### 3.4 バリデータ (`doc_parser/validate_parsed_output.py`)
- 入力ソースと生成物を読み、差分とメトリクスを出力。
- 主な引数: `--api-doc`, `--api-arg`, `--parsed`, `--format`, `--fail-on`, `--baseline`, `--graph-metrics`。

### 3.5 既存CLI統合 (`doc_parser/doc_paser.py`)
- 追加フラグ: `--validate-against-src`, `--use-langgraph`, `--rebuild-index`。
- LangGraph で抽出後、`graph_metrics.json` と `parsed_api_result.json` を生成し、バリデータを同期呼び出し。
- CI向けに `--baseline` を渡し、閾値は `.validationrc` に YAML 形式で保存し共有。

---

## 4. LangGraph & LLM 抽出ワークフロー

### 4.1 データフロー
- 入力: `api_arg.txt`→型集合 S_arg、`api.txt`→API集合 F_src。
- 処理: 正規化→集合比較→詳細比較→リンク生成（`canonical_id`/`source_span_hash`）→ベースライン比較。
- 出力: `parsed_api_result.json`・`graph_metrics.json`・`validation_report.json` を生成し、Neo4j/Chroma 連携で `canonical_id` と `source_span_hash` をキーに格納。

### 4.2 LangGraph ワークフロー詳細
1. **インデックス構築（LlamaIndex + LangChain）**
   - `SimpleDirectoryReader` で原文を読み込み、`SentenceSplitter` による 512 token チャンクを生成。
   - `MetadataExtractor` が `section_hierarchy`, `line_start`, `line_end`, `doc_source_id` を計算し、Chroma 向けに JSON Lines で永続化。
   - `graph_state.chunk_stats.expected` にチャンク数を記録し、`chunk_hash` を計算して再ビルド判定に活用。
2. **ノード定義と遷移**
   - `ChunkLoader`: LlamaIndex の retriever を LangChain `Tool` 化し、チャンクごとに `ChunkPayload`（テキスト+メタデータ）を出力。件数を `chunk_stats.loaded` に記録。
   - `FunctionSplitter`: heading/表形式を解析し `FunctionTask`（ID, span, expected_params, raw_text）を生成。件数を `function_stats.detected` に、予想到達数を `function_stats.expected` に保存。
   - `LLMExtractor`: LangChain の `StructuredChatAgent` + `JsonOutputParser` で厳格スキーマを強制し、LangSmith Trace ID を `execution_trace` に記録。失敗は `retry_queue` へ積む。
   - `PostProcessor`: `normalize_types`→`infer_required`→`format_default`→`assign_positions` の順で整形し、`source_refs` と LlamaIndex ノードIDを照合。欠落があれば `retry_queue` へ返送。
   - `Aggregator`: `graph_state.extraction_outputs` をマージし、`function_stats.extracted` と `type_stats.unique` を更新。件数差異があれば `RetryController` を呼び出し。
   - `Validator`: `validate_parsed_output.py` を実行し `graph_state.validator_report` に格納。欠落差分が残れば `RetryController` へ渡し再抽出を開始。
   - `RetryController`: `retry_queue` と `validator_report` を突合し、原文再取得→再抽出→再検証のループを LangGraph の `While` で管理。
3. **ステージゲートと件数チェック**
   - `chunk_stats.loaded == chunk_stats.expected` を満たさない場合は `DiagnosticReporter` ノードに遷移し CI を失敗させる。
   - `function_stats.extracted / function_stats.expected ≥ 0.95` を閾値に設定し、下回る場合は `RetryController` を継続。
   - `retry_count` が 3 を超過した場合は `HumanReviewQueue` ノードへ分岐し、原文スパンを添えて手動確認チケットを発行。
4. **モニタリングとレポート**
   - LangGraph のトレースログ（node_name, duration, attempt）を `graph_state.execution_trace` として保存し、`graph_metrics.json` に書き出し。
   - 件数チェック結果（`chunk_stats`, `function_stats`, `retry_count`, `self_heal.success_rate`, `type_stats`）を最終レポートに同梱。
5. **最終出力と通知**
   - `parsed_api_result.json`, `graph_metrics.json`, `validation_report.json` を出力。
   - Slack/Teams 通知にはメトリクスサマリと直近差分（欠落 API 名等）を添付。

### 4.3 プロンプト設計（関数用の要点）
- 役割: 仕様→スキーマへの正規化抽出器。
- 制約: JSON のみ、推測禁止、未記載は null、フィールド固定。
- 出力: `entry_type/name/description/category/params[]/returns/is_array/notes/implementation_status/source_refs`。
- Few-shot: 良い例・悪い例→修正例を 1 セット提示し、表記ゆれを抑制。

### 4.4 リトライ/自動補正
- JSON 破損時は温度を下げて数回リトライ。
- 差分検証（欠落/不一致）が出た関数のみ再抽出し、コストを最小化。

### 4.5 並列化とスループット
- チャンク単位・関数単位で並列実行可（API レート制御のみ配慮）。
- 最終集約とバリデーションは同期ポイントで実施。

---

## 5. 実装手順（番号付きフロー）
1. **準備/設定**
   - `.validationrc` に検証閾値・通知設定を作成し、`requirements.txt` の LangChain・LangGraph・LlamaIndex バージョンを固定。
   - 既存の `doc_parser/doc_paser.py` に `--use-langgraph` などのフラグ定義を追加し、`uv run` コマンドで再利用できるよう CLI を整える。
2. **入力前処理**
   - `doc_parser/index_builder.py` に LlamaIndex チャンク生成とメタデータ整形ロジックを実装し、`graph_state.chunk_stats.expected` を初期化。
   - `api_arg.txt` から S_arg を抽出するヘルパー関数を `validate_parsed_output.py` に追加し、型正規化・別名吸収テーブルを定義。
3. **LangGraph ノード実装**
   - `pipeline_langgraph.py` に `ChunkLoader`→`FunctionSplitter`→`LLMExtractor`→`SelfHealAgent`→`PostProcessor`→`Aggregator`→`Validator` のノードクラスを順次実装。
   - `GraphState` dataclass を定義して `retry_queue` や `execution_trace` などの状態を一元管理し、ノード遷移条件を明示。
4. **自己修正ループの統合**
   - `self_heal.py` に retriever・再抽出ツールを実装し、LangGraph の `RetryController` ノードから呼び出して差分項目を再処理。
   - 再抽出後の結果を `graph_state.extraction_outputs` にマージし、成功件数を `graph_metrics.json` に記録。
5. **検証ロジックの充実**
   - `validate_parsed_output.py` に型/API/パラメータ・リンク整合性チェックとベースライン比較ロジックを実装。
   - `--format`, `--fail-on`, `--baseline`, `--graph-metrics` などの CLI 引数を受け取り、JSON・text 両形式のレポートを生成。
6. **Neo4j/Chroma 連携準備**
   - 検証結果に `canonical_id`・`source_span_hash` を出力し、`db_integration/` のスクリプトから取り込める形で JSON スキーマを固定。
   - 取り込みスクリプトで `source_refs` をキーに原文確認ができることを確認。
7. **CI・通知統合**
   - GitHub Actions（想定）に `uv run python doc_parser/doc_paser.py --use-langgraph --validate-against-src --baseline ...` を追加。
   - CI 失敗時に Slack/Teams 通知を送るスクリプトを `doc_parser/notify_validation.py`（新規）で実装し、メトリクスサマリを投稿。
8. **テストとドキュメント整備**
   - `tests/test_validation.py` などに単体・統合テストを追加し、欠落・不一致・リンクエラーのケースを網羅。
   - README や計画書に実行手順とトリアージ方法を追記し、ベースライン更新手順を `doc/validation_baseline.md` として整理。

---

## 6. 主要ロジック（擬似仕様）
- 型抽出（入力）
  - `api_arg.txt` の型見出し行（先頭`■`）を走査し、`^■\s*(?P<name>[^\s\(]+)` の正規表現で S_arg を構築。
  - 説明文や例 (`例)`, インデント付き行) は無視し、抽出後に `DataProcessor.normalize_type_name()` で正規化。
  - 用語揺れ・別名は `type_alias_map`（例: 「浮動小数点」→`float`）で吸収し、重複を除外した集合として S_arg を確定。
- API抽出（入力）
  - LlamaIndex で構築した `Document` から `heading_path` を辿り、関数ごとに `FunctionMetadata` を生成。
  - 正規表現ベースのフォールバック抽出を併用し、両者の差分を `graph_state.function_stats.expected` に記録。
- LangGraph ノードロジック
  - `ChunkLoader`: LlamaIndex の `Document` チャンクを読み出し、LangChain `Runnable` へ引き渡す辞書構造（`chunk_id`, `text`, `span`）。
  - `FunctionSplitter`: heading/表形式を解析し、関数単位の `TaskPayload` を生成、件数を `graph_state.function_stats.detected` に追記。
  - `LLMExtractor`: LangChain の `ChatPromptTemplate` + `JsonOutputParser` で厳格スキーマを強制、LangSmith トレーシング ID を `execution_trace` に記録。
  - `SelfHealAgent`: 差分付きペイロードを入力すると、LlamaIndex retriever から原文を復元し `LLMExtractor` を再実行。
  - `PostProcessor`: 型正規化、配列判定、必須推定、デフォルト値整形、`position`/`canonical_id` の付与。
  - `Aggregator`: 同名関数のマージ、型集合のユニーク化、`parsed_api_result.json` への集約。
  - `Validator`: 差分検証ロジックを呼び出し、メトリクス計算とベースライン比較を実施。
- 出力パース: `parsed_api_result.json` の `type_definitions`・`api_entries` を取得。
- 正規化: 型名は両側で `DataProcessor.normalize_type_name()`、配列は `_is_array_type`/`_strip_array_notation`。
- リンク生成: `normalized_name` と `source_refs` を元に `canonical_id`・`source_span_hash` を付与し、LlamaIndex ノードIDとも突合。
- 照合: 型（S_arg vs S_out）、API（F_src vs F_out）、各APIの params/returns 詳細一致。
- 出力: text（サマリ＋差分）、json（欠落/余剰/不一致詳細・メトリクス）。JSON には `canonical_id`、`source_span_hash`、`normalized_name` を含め Neo4j/Chroma 取り込み時のキーに利用。

---

## 7. CLI/UX
- LangGraph + LlamaIndex 実行: `uv run python doc_parser/doc_paser.py --use-langgraph --rebuild-index --validate-against-src`
- 解析＋検証一括（既存 pipeline）: `uv run python doc_parser/doc_paser.py --validate-against-src --verbose`
- 生成物のみ検証: `uv run python doc_parser/validate_parsed_output.py --format text`
- JSON レポート: `uv run python doc_parser/validate_parsed_output.py --format json --emit-graph-metrics doc_parser/graph_metrics.json > validation_report.json`
- ベースライン比較: `uv run python doc_parser/validate_parsed_output.py --baseline doc/validation_baseline.json --fail-on all`
- 追加フラグ例: `--extract-parallel N`, `--reconcile-missing-only`, `--emit-graph-metrics`（いずれも LangGraph 実行時に使用）。
- ロギング方針: チャンク/関数の開始・成功・失敗、再抽出回数、検証メトリクス、LangSmith Trace URL を INFO/DEBUG で出力し、`--verbose` 時は各ノードの `graph_state` スナップショットと retriever ヒット件数を表示。

---

## 8. テスト計画（pytest）
- 型網羅: 入力に含む型がすべて出力されるケース／欠落ケース。
- API網羅: 入力関数がすべて出力される／一部欠落。
- パラメータ整合: 位置・必須・デフォルト・型の不一致。
- 境界: 空配列、戻り値 void、配列型判定。
- リンク検証: `source_refs` 欠落・重複、`canonical_id` 衝突、`source_span_hash` 不一致。
- ベースライン回帰: 既存レポートとの差分が閾値に応じて検知されるか。
- LangGraph ノード: `MockRetriever`・`MockLLM` を用いた `RetryController`・`SelfHealAgent` の制御フロー検証。

---

## 9. スケジュール/工数目安
- バリデータ実装: 0.5〜1.0日（入力の正規表現整備次第）。
- CLI 統合: 0.5日。
- テスト: 0.5日。
- LangGraph ノード実装と自己修正: 1.0〜1.5日（プロンプト調整含む）。
- 合計: 2.5〜3.5日。

---

## 10. 運用手順（ユーザー向け）

### 10.1 使い方（ローカル）
- 解析＋検証一括: `uv run python doc_parser/doc_paser.py --validate-against-src --verbose`
- 生成物のみ検証: `uv run python doc_parser/validate_parsed_output.py --format text`
- JSON レポート: `uv run python doc_parser/validate_parsed_output.py --format json > validation_report.json`
- ベースライン比較: `uv run python doc_parser/validate_parsed_output.py --baseline doc/validation_baseline.json --fail-on all`

### 10.2 トリアージ手順
- CI 失敗時は検証レポートのメトリクス差分を確認し、`missing`・`mismatch`・`link_failure` のカテゴリごとに整理。
- `graph_metrics.json` の `function_stats`・`self_heal` を確認し、どのステージで落ちたかをトリアージ。
- 欠落API/型が発生したチャンクを特定し、`--reconcile-missing-only` で再抽出 → 解消しない場合は LlamaIndex retriever で原文を参照。
- 人手レビューが必要な項目はチケット化し、`source_refs` と `canonical_id` を添付して Neo4j/Chroma 上のノードを直接参照。
- 再抽出後はベースラインを更新し、差分承認を記録（`doc/validation_baseline.json` を Pull Request に同梱）。

### 10.3 出力例（text）
- 型カバレッジ: 26/27 (96.3%)
- 欠落型: 変数単位
- 余剰型: XYZ方向（入力に未記載）
- APIカバレッジ: 115/118 (97.5%)
- 欠落API: Part.CreateSketchEllipse2 ほか2件
- 整合差分（例）
  - OpenDocument.params[1].default_value: expected=false, actual="false"
  - View.GetViews.returns.is_array: expected=true, actual=false
- リンク完全率: 114/118 (96.6%) - 欠落: Drawing.Open, Part.CreateSketchEllipse2

---

## 11. アクセプタンス基準とエラー処理

### 11.1 アクセプタンス基準
- 型カバレッジ・APIカバレッジともに 95%以上（閾値は `.validationrc` で管理し共有）。
- `source_refs` 欠落率 0%、`canonical_id` 重複 0 件、`source_span_hash` の衝突なし。
- ベースライン比較で重大差分（欠落API/型不一致/必須フラグ変更）が増えていないこと。
- CI 実行では `--fail-on missing` を既定とし、重大差分検知時に Slack/Teams へレポート送信。

### 11.2 エラー処理
- 入力ファイル未発見・エンコーディング問題は `read_file_safely` を流用。
- JSON パース失敗は例外＋非ゼロ終了（`--format json` 時はエラーJSONも可）。
- ベースラインファイル未指定/未検出時は警告ログを出力し比較をスキップ（CIでは必須）。

### 11.3 失敗基準
- `--fail-on missing`: 欠落（型/API/主要フィールド）が1つでもあれば非ゼロ終了。
- `--fail-on all`: 欠落または不一致・余剰があれば非ゼロ終了。
- ベースライン差分が許容閾値（例: 欠落API 0 件、パラメータ不一致 5 件以内）を超過。
- `source_refs` の欠落/重複が検知された場合。

---

## 12. 多角的評価（中立的視点）

### 12.1 技術的実現性
- LangGraph・LangChain・LlamaIndex の連携構成は既存ライブラリの標準 API を利用しており技術的には実装可能。ただし `doc_parser` 配下に LangGraph オーケストレータや自己修正エージェントを新設する必要があり、既存の `doc_paser.py`（typo あり）との整合性を再確認する必要がある。
- `DataProcessor.normalize_type_name()` など既存ユーティリティを前提にしているため、未実装/非公開の関数がある場合は追加実装が必要。特に `type_alias_map` や `FunctionMetadata` の生成処理は明示されておらず、仕様を再定義する工程が発生する可能性がある。
- `graph_metrics.json` や `validation_report.json` の書き出しはファイル IO と JSON 生成で対応可能だが、LangGraph ノード内での状態共有に型付きデータクラスを使うため、循環参照やシリアライズ不能なオブジェクトに注意が必要。

### 12.2 リスクと制約
- LangGraph を導入することで抽出処理が複雑化し、LLM 呼び出し回数やリトライ制御の設計次第でコストが増大する懸念がある。CI での実行を想定する場合、API トークン制限やタイムアウト対策を事前に決める必要がある。
- `source_refs` の整合性を維持するには、原文の行番号やチャンク境界が再処理時に変化しないことが前提。`api.txt` の改訂が頻繁な場合は差分追跡やチャンク再生成時のハッシュ管理を強化する必要がある。
- ベースライン比較と Slack/Teams 通知は外部サービスの認証情報や Webhook を要求するため、セキュリティ・ネットワーク制限（社内環境など）の影響を受けやすい。

### 12.3 運用・保守観点
- `graph_metrics.json` のメトリクスをダッシュボード化するまでの導線が未記載のため、運用チームが参照する仕組み（可視化ツールや集計スクリプト）を追加検討する必要がある。
- LangGraph のリトライ上限を超えたケースを「人手レビュー」に回すとあるが、実際に誰がどのツールでレビューするのか、SLA やチケットテンプレートを文書化しておくと運用が安定する。
- `.validationrc` に設定した閾値のバージョン管理と承認フローを整備しないと、無自覚な閾値変更による誤検知/見逃しが発生しうる。

### 12.4 代替案・改善案
- LangGraph を導入せずとも LangChain の `RunnableSequence` と再帰的な再抽出処理で簡易的な実装は可能。初期段階ではシンプルな制御フローで検証し、必要に応じて LangGraph へ移行する段階的アプローチも選択肢となる。
- `graph_metrics.json` に依存せず、バリデータ内で直接件数チェックやメトリクス算出を行い、単一 CLI で完結させることでワークフローを簡素化できる。
- LlamaIndex のみならず、`RapidOCR` など別の前処理や PDF 解析基盤と差し替え可能な抽象化層を用意することで、将来的な入力ソース拡張に柔軟に対応できる。

### 12.5 想定追加タスク
- LangGraph ノード実装に合わせたユニットテストや統合テストの新設（Mock retriever/LLM を使った検証）。
- CI パイプラインへの組み込みと、Slack/Teams 通知機能のシークレット管理・テスト。
- Neo4j/Chroma 取り込みスクリプトで `canonical_id` と `source_span_hash` を利用する実装の整備（既存スクリプトが無い場合）。

---

## 13. 完成度評価と今後の進め方

### 13.1 現状評価
- **実装計画の詳細度**: LangGraph/LlamaIndex/自己修正/バリデータ/CLI まで具体化されており、主要な設計要素と役割分担は明確。
- **検証観点**: 型/API/リンク整合性に加え、メトリクス・ベースライン比較・LangGraph 実行トレースが定義済みで、品質基準を判断できる。
- **運用フロー**: CLI 実行手順、トリアージ、Slack/Teams 通知の想定を記述済みで、導入後の流れを把握可能。

### 13.2 未確定/要対応項目
- LangGraph ノード群や LlamaIndex メタデータ整形の実コードは未実装であり、擬似仕様を実装仕様に落とす際に細部調整が必要。
- `.validationrc` の閾値設計や Slack/Teams 通知のワークフロー（責任者・通知テンプレート）は別途ドキュメント化が必要。
- Neo4j/Chroma 連携で `canonical_id`・`source_span_hash` を利用する周辺スクリプトが未定義の場合は、追加の設計と実装を行う必要がある。

### 13.3 未対応項目への対応計画
- **LangGraph ノード実装**
  - `doc_parser/pipeline_langgraph.py` に `ChunkLoader` から `RetryController` までの各ノードを Python クラスとして実装し、`BaseNode` インタフェース（`run(graph_state: GraphState) -> GraphState`）を統一。
  - 先にユニットテスト用の `MockRetriever`・`MockLLM` を `tests/langgraph_fixtures.py` に用意し、ノードごとに入出力の契約テストを作成。
  - LangGraph の `StateGraph` 生成コードを CLI から呼び出せるようにし、`graph_state` のデフォルト初期化を `GraphStateFactory` に切り出す。
- **LlamaIndex メタデータ整形**
  - `doc_parser/index_builder.py` に `build_index(config: IndexConfig) -> IndexArtifacts` を追加し、チャンクごとに `line_start/line_end`, `section_hierarchy`, `doc_source_id` を JSON Lines として保存。
  - `IndexConfig` にはチャンクサイズ・オーバーラップ・出力先パスを含め、LangGraph 側で再利用できるよう `graph_state.chunk_catalog_path` を渡す。
- **`.validationrc` 設計**
  - リポジトリ直下に YAML テンプレート `doc/validationrc.example` を追加し、`thresholds`（型/API/リンク）、`notifications`（Slack Webhook, Teams Connector URL, mention 先）、`owner`（担当者 Slack ID）を定義。
  - CLI 起動時に `--config .validationrc` を受け取れるよう `validate_parsed_output.py` に設定ローダーを実装し、閾値が欠落している場合はテンプレートを参照するフォールバックを設ける。
- **通知ワークフロー整備**
  - `doc/validation_notifications.md` を新設し、Slack/Teams のメッセージフォーマット（成功/失敗時のフィールド、添付するメトリクス、担当者メンション）と運用手順（誰が初動対応・レビュー）を記載。
  - CI（GitHub Actions 予定）で `VALIDATION_WEBHOOK_URL` 等のシークレットを読み込み、検証結果 JSON を整形して送信するスクリプトを `scripts/post_validation_result.py` に配置。
- **Neo4j/Chroma 連携スクリプト**
  - `db_integration/push_validation_results.py` を追加し、`parsed_api_result.json` と `validation_report.json` を読み込み `canonical_id`, `source_span_hash`, `coverage_metrics` を Neo4j/Chroma のノード/ドキュメントメタデータに書き戻す。
  - 既存の `chroma_data.json` や `neo4j_data.json` を参照し、差分状態（例: `status=missing|mismatch|ok`）を属性として付与、長期モニタリング用の `doc/coverage_history.csv` に追記するジョブを設計。

### 13.4 改善提案
- LangGraph のステージごとに `graph_state` のダンプを `doc/debug/graph_state_<timestamp>.json` として保存し、障害発生時の再現性を高める運用を推奨。
- LLM 抽出プロンプトに「原文に無いフィールドは null で出力する」旨を明記し、空文字列や推測値が混入しないようスキーマを `pydantic` で厳格検証する実装を検討。
- ベースライン更新時に自動で Pull Request コメントへメトリクス差分を投稿する GitHub Action（`comment_validation_diff.yml`）を追加し、レビューアーが差分を素早く把握できるよう支援。
- Neo4j/Chroma 側で `source_refs` の行番号リンクを Grafana などの可視化に連携し、低カバレッジ領域の発見を容易にするダッシュボード整備を長期計画に含める。
- API 仕様更新の検知のために `data/src/api.txt` の Git 差分から変更チャンクのみを再抽出する `--changed-only` フラグを LangGraph CLI に導入し、運用コストと LLM コール数を削減。

### 13.5 推奨アクション
1. LangGraph ノード・self-heal・バリデータを優先実装し、ミニマムデータセットで end-to-end テストを実施。
2. `.validationrc` と Slack/Teams 通知の詳細運用設計を別ドキュメントで整備し、CI 連携時の責務分担を明文化。
3. Neo4j/Chroma 連携スクリプト（もしくは既存ツール）の対応可否を確認し、必要なら API 仕様を更新して取り込みテストを追加。

### 13.6 最終確認チェックリスト
- [ ] LangGraph ノード実装と自己修正ループのユニットテストが `tests/langgraph_*.py` でグリーン。
- [ ] `doc_parser/index_builder.py` が `line_start/line_end/section_hierarchy` を出力し、`graph_state.chunk_catalog_path` が生成されている。
- [ ] `.validationrc`（または `.validationrc.local`）がリポジトリルートに配置され、CI から閾値・通知設定を読み込める。
- [ ] `scripts/post_validation_result.py` が CI で動作し、Slack/Teams への通知テストを完了。
- [ ] `db_integration/push_validation_results.py` が Neo4j/Chroma へのメタデータ反映を成功（スタブ環境で検証済み）。
- [ ] `doc/validation_baseline.json` を最新の検証結果で更新し、PR でレビューを受けたログが残っている。

上記チェックが完了していれば、実装計画書は完成版として扱って差し支えない。未完了項目がある場合は、チケット化してフォローアップのスケジュールを明記すること。

---

## 14. 将来拡張
- 解析段階で `source_refs`（入力の行番号）を `api_entries` に付与。
- HTML レポートの生成。
- 表記ゆれ辞書の強化（真偽/有無/単位）。
- 不一致を自動パッチ提案（LLM による修正候補生成）。
- Neo4j/Chroma への格納時に差分状態・カバレッジ指標をメタデータ保存し、長期トレンドをダッシュボードで可視化。
- 低カバレッジ関数を優先度付きで人手レビューに回すフロー（レビューフィードバックの自動取込）。

