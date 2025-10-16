LLM 抽出結果を structured_api 形式へ整合させる修正方針

目的
- LLM 抽出結果（tmp_llm_output.json）をお手本（structured_api.json）に揃える。
- 冗長/誤分類/欠落/英日型混在を解消し、安定した JSON を得る。

対象モジュール
- api_extractor/llm_pipeline.py（プロンプト、Pydantic スキーマ、後処理、ログ）
- api_extractor/type_registry.py（型エイリアスと配列判定拡張）

1) プロンプト修正（llm_pipeline.py::_get_prompt）
- 出力対象を明示: entries には function と object のみを出力。parameter/method/日本語型名などは出力禁止。
- category は必須（例: "Applicationオブジェクト", "Documentオブジェクト"）。未記載は直前セクションを継承。null は不可。
- returns 未記載の function は type=void（"なし" は void とみなす）。
- 配列は必ず is_array:true もしくは array_info: { "qualifier": "配列" } で明示。
- オブジェクト属性は object の properties のみに格納。function に properties は禁止。
- 型名はタイプカタログの日本語名を厳守（number/object/length 等の英語は禁止）。

2) スキーマ制約（llm_pipeline.py の Pydantic）
- LLMEntryPayload.entry_type を Literal["function", "object"] に制約。
- category を必須化（空文字は許容だが null は不可）。
- function で properties が入ってきたら無視（ValidationError にせず後処理で除外）。
- object 以外の entries に properties を許可しない validator を追加。

3) 後処理（正規化・フィルタ）（llm_pipeline.py）
- フィルタ: entry_type ∉ {function,object} は破棄（parameter/method/日本語型名 など）。
- 重複統合: 同一キー（entry_type:name）は内容が充実している方を優先統合。
- 補完: category 欠落は前後文脈から推定、不能時は既定カテゴリで補完。function の returns 欠落は void 付与。
- 型正規化: TypeRegistry で英語→日本語（length→長さ、number→浮動小数点、object→オブジェクト）。
- 配列正規化: 「〜の配列」「(配列)」等を検出し is_array/array_info を設定。複合表現（"Documentオブジェクトの配列"）は type="Documentオブジェクト", is_array=true へ分解。
- オブジェクト統合: CreateSTLOption / CreateLinearSweepParam / ブラケットパラメータ などは entry_type=object として集約し、分散した parameter エントリを properties に吸収。
- 欠落補填: 例）ExporAsSTL の pOpt を追加（type=オブジェクト、説明はタイプカタログ準拠）。

4) 型辞書の拡張（api_extractor/type_registry.py）
- _aliases へ追加: { "length":"長さ", "number":"浮動小数点", "object":"オブジェクト", "array":"配列" }。
- extract_type を拡張:
  - 日本語に「の配列」「(配列)」が付く場合に配列判定し array_info を返す。
  - "<型>の配列" → (type=<型>, is_array/array_info 設定)。
  - 特例: "Documentオブジェクトの配列" を上記ルールで正規化。

5) 具体的差分の是正（代表例）
- entry_type 誤り: method/parameter/日本語型名の entries を破棄。
- category 欠落: Application/Document 等を推定・補完。
- IsActive 重複: function に統一し、category="Documentオブジェクト" を付与。重複片は破棄。
- ExporAsSTL: pOpt パラメータを追加。
- CreateSTLOption.properties.Elements: type を "要素(配列)" に正規化し array_info を保持。
- CreateLinearSweep/… の操作パラメータ群: function の properties から削除し、該当パラメータオブジェクト（object）側の properties として集約。

6) ロギング/可観測性（llm_pipeline.py）
- 後処理で以下を計測・INFO/DEBUG 出力:
  - 破棄件数（entry_type 不正、Validation 失敗）
  - 重複統合件数
  - 補完件数（category/returns）
  - 型正規化・配列正規化件数

7) 導入ステップ（推奨順）
1. 後処理の追加（フィルタ/補完/正規化/統合）
2. 型辞書の拡張（英→日、配列表現）
3. プロンプトの禁止・必須ルールの明記（ノイズ抑制）
4. スキーマ制約の強化（誤出力の早期弾き）
5. 必要なら few-shot（短縮サンプル）をプロンプト末尾に追加

検証観点
- structured_api.json の代表 API（Quit/ShowMainWindow/OpenDocument/CreateSTLOption など）で:
  - entry_type と category の整合
  - params/returns の完全性（position/type/description）
  - 配列表現の統一（is_array/array_info）
  - 型の日本語化と既知型への収束
  - オブジェクト定義の properties 集約

備考
- .env は load_dotenv() で読込済み。実行時は uv run を推奨。
- フォーマットは "uv run black <file>" を使用。

