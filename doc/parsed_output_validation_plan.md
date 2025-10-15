### 目的
- 入力データ（`data/src/api.txt`・`data/src/api_arg.txt`）と出力データ（`doc_parser/parsed_api_result.json`）の差異を自動検証し、網羅性・整合性・品質を定量化。欠落と余剰を可視化し、回帰に強いパイプラインにする。

### スコープ
- 対象: `doc_parser/parsed_api_result.json`（生成物）
- 入力: `data/src/api.txt`（API仕様）, `data/src/api_arg.txt`（型仕様）
- 出力: 差分レポート（JSON/テキスト）、検証サマリ（カバレッジ指標）、CI/ローカルでの自動実行

---

## 実装計画（詳細）

### 1. 検証観点の定義
- 型網羅チェック
  - 入力の型集合 S_arg と、出力 `type_definitions[].name` の集合 S_out を比較
  - 結果: 欠落型、余剰型、別名（正規化による吸収）一覧
- API網羅チェック
  - 入力 `api.txt` からエントリ名集合 F_src（関数/オブジェクト）を抽出
  - 出力 `api_entries[].name` の集合 F_out と比較（欠落/余剰）
- 項目整合チェック
  - 各 API について、パラメータの数・順序・名前・型・必須/任意・デフォルト値、戻り値型/配列を照合
  - 型は `DataProcessor.normalize_type_name()` で正規化して比較
- 指標（メトリクス）
  - 型カバレッジ = |S_out ∩ S_arg| / |S_arg|
  - APIカバレッジ = |F_out ∩ F_src| / |F_src|
  - パラメータ一致率 = 一致パラメータ数 / 総パラメータ数
  - 重大差分件数（例: 欠落API、型不一致）

### 2. 実装構成
- 新規スクリプト: `doc_parser/validate_parsed_output.py`
  - 役割: 入力ソースと生成物を読み、差分とメトリクスを出力
  - 引数:
    - `--api-doc data/src/api.txt`
    - `--api-arg data/src/api_arg.txt`
    - `--parsed doc_parser/parsed_api_result.json`
    - `--format json|text`（既定 text）
    - `--fail-on <none|missing|all>`（CI向け閾値）
- 既存CLI統合: `doc_paser.py`
  - 追加フラグ: `--validate-against-src`
  - 解析直後にバリデータ呼び出し（内部関数 or サブプロセス）
  - 失敗条件に応じて非ゼロ終了（CI用途）

### 3. 主要ロジック（擬似仕様）
- 型抽出（入力）: `api_arg.txt` の型名を抽出（正規表現/既知辞書）。コメント/例は除外。
- API抽出（入力）: `api.txt` から関数/オブジェクト名を抽出（見出し/定義パターンの正規表現化）。
- 出力パース: `parsed_api_result.json` の `type_definitions`・`api_entries` を取得。
- 正規化: 型名は両側で `DataProcessor.normalize_type_name()`、配列は `_is_array_type`/`_strip_array_notation`。
- 照合: 型（S_arg vs S_out）、API（F_src vs F_out）、各APIの params/returns 詳細一致。
- 出力: text（サマリ＋差分）、json（欠落/余剰/不一致詳細・メトリクス）。

### 4. CLI/UX
- 解析＋検証一括: `uv run python doc_parser/doc_paser.py --validate-against-src --verbose`
- 生成物のみ検証: `uv run python doc_parser/validate_parsed_output.py --format text`
- JSON レポート: `uv run python doc_parser/validate_parsed_output.py --format json > validation_report.json`

### 5. テスト計画（pytest）
- 型網羅: 入力に含む型がすべて出力されるケース／欠落ケース
- API網羅: 入力関数がすべて出力される／一部欠落
- パラメータ整合: 位置・必須・デフォルト・型の不一致
- 境界: 空配列、戻り値 void、配列型判定

### 6. スケジュール/工数目安
- バリデータ実装: 0.5〜1.0日（入力の正規表現整備次第）
- CLI 統合: 0.5日
- テスト: 0.5日
- 合計: 1.5〜2.0日

---

## アーキテクチャ詳細

### データフロー
- 入力: `api_arg.txt`→型集合 S_arg、`api.txt`→API集合 F_src
- 出力: `parsed_api_result.json`→S_out・F_out・各 API 詳細
- 処理: 正規化→集合比較→詳細比較
- 出力: `stdout`（text）/ JSON レポート（オプションでファイル書き出し）

### エラー処理
- 入力ファイル未発見・エンコーディング問題は `read_file_safely` を流用
- JSON パース失敗は例外＋非ゼロ終了（`--format json` 時はエラーJSONも可）

### 失敗基準（例）
- `--fail-on missing`: 欠落（型/API/主要フィールド）が1つでもあれば非ゼロ終了
- `--fail-on all`: 欠落または不一致・余剰があれば非ゼロ終了

---

## 運用手順（ユーザー向け）

### 使い方（ローカル）
- 解析＋検証一括
  - `uv run python doc_parser/doc_paser.py --validate-against-src --verbose`
- 生成物のみ検証
  - `uv run python doc_parser/validate_parsed_output.py --format text`
- JSON レポート
  - `uv run python doc_parser/validate_parsed_output.py --format json > validation_report.json`

### 出力例（text）
- 型カバレッジ: 26/27 (96.3%)
- 欠落型: 変数単位
- 余剰型: XYZ方向（入力に未記載）
- APIカバレッジ: 115/118 (97.5%)
- 欠落API: Part.CreateSketchEllipse2 ほか2件
- 整合差分（例）
  - OpenDocument.params[1].default_value: expected=false, actual="false"
  - View.GetViews.returns.is_array: expected=true, actual=false

---

## 将来拡張
- 解析段階で `source_refs`（入力の行番号）を `api_entries` に付与
- HTML レポート
- 表記ゆれ辞書の強化（真偽/有無/単位）
- 不一致を自動パッチ提案（LLM による修正候補生成）


