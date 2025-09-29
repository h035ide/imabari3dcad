# Parameter ノード再設計計画

## 目的
- パラメータ（Parameter）ノードを関数やオブジェクトに依存しない「名前＋役割」単位の一意構造に変更する
- 関数・オブジェクトとの関連はリレーションシップで表現し、メタデータ（説明、必須/任意、位置など）はリレーション側で管理する
- 既存データ・LlamaIndex変換・QAシナリオを新構造へ移行する

## 対象コンポーネント
- `doc_parser/neo4j_importer.py`
- `main_helper_0905.py`
- `main_0905.py`
- Neo4j 既存データ
- LlamaIndex 変換・ログ

## 現状の課題
- `Parameter` ノードが `name + parent_function`（または `parent_object`）で分割されており、同名パラメータが複数ノードとして存在する
- LlamaIndex 変換でも「関数別パラメータ」が別個の `__Entity__` になり、知識共有・横断検索が難しい
- Type/Parameter の冗長な重複が生じている

## 新構造の概要
1. **Parameterノード**
   - 一意キー: `{name, kind}` （kind は `function_parameter` / `object_property` 等）
   - プロパティ: `name`, `kind`, `description`（任意）
   - 追加情報（位置、必須、関数別説明）はリレーションへ移行
2. **関数との関連**
   - リレーション: `(f:Function)-[:USES_PARAMETER]->(p:Parameter)`
   - リレーション属性: `description`, `is_required`, `position`, `notes` 等
3. **オブジェクトとの関連**
   - リレーション: `(od:ObjectDefinition)-[:USES_PROPERTY_PARAMETER]->(p:Parameter)`
   - リレーション属性: `description`, `type`, `notes` 等（必要に応じて）
4. **Type/Parameter 関連**
   - `(p:Parameter)-[:HAS_TYPE]->(t:Type)` は継続
   - Type ノードは既存どおり一意
5. **LlamaIndex変換**
   - `Parameter` を `__Entity__` 化する際、関数ごとの情報はリレーションメタデータから組み立て
   - `Function` との関係は `USES_PARAMETER_ENTITY` 等のリレーションで表現

## 実施ステップ
1. **設計確認（本ドキュメント）**
   - 主要エンティティ・リレーション・属性を確定
   - 影響範囲（クエリ、コンバージョン、QA）を洗い出す
2. **`neo4j_importer.py` 修正**
   - `Parameter` ノード生成ロジックを `MERGE (p:Parameter {name, kind})` に変更
   - 既存 `parent_function`/`parent_object` プロパティを削除
   - 関数/オブジェクトとの関係を新リレーションで生成し、メタデータをリレーション属性へ移す
   - 旧構造に依存する部分を削除
3. **データクレンジング**
   - 既存グラフから旧 `Parameter` ノードを削除（バックアップ必須）
   - 新インポート実行時に自動クレンジングするオプションを提供（例: フラグで `MATCH (p:Parameter) DETACH DELETE p`）
4. **`main_helper_0905.py` 更新**
   - `_convert_existing_data_to_llamaindex` を新構造対応へ
   - `Parameter` 情報取得時に関係メタデータを参照
   - `__Entity__` 生成ロジックを新構造に合わせる
5. **`main_0905.py`/QAフロー調整**
   - QAで参照するCypher（必要なら）を新リレーションに合わせて更新
6. **検証**
   - Neo4j: `Parameter` 重複が解消され、一意ノード＋複数リレーションになっていることを確認
   - LlamaIndex: `engine.query()` 実行とログで新構造が使用されていることを確認
   - QA: `uv run python main_0905.py -f qa -q 
