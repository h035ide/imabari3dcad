# ハイブリッド前処理パイプライン

このモジュールは、EVO.SHIP の API ドキュメントに対して二段階の前処理フローを構築します。

1. **決定的（ルールベース）抽出**
   - `api.txt` を解析し、パラメータや戻り値のメタデータを伴うオブジェクト／関数定義に変換します。
   - `api_arg.txt` を解析し、正規化された型記述に整えます。
   - 既存の `type_definitions` / `api_entries` スキーマに従うベースライン JSON を生成します。
2. **対象を絞った LLM 補強（任意）**
   - 説明不足や分類が曖昧な項目など、あいまいなエントリのみを LLM に送ります。
   - 変更された断片をトレーサビリティを保ったままベースライン JSON にマージします。
3. **構造化された出力**
 - `structured_api.json`: スキーマに整合した、補強後のビュー。
 - `graph_payload.json`: Neo4j 取り込み用のトリプルとノードメタデータ。
 - `vector_chunks.jsonl`: ベクターデータベース構築用のテキストチャンク。

決定的なレイヤーでは既存パイプラインのルールベースの強みを再利用し、第2段階では LLM の利用範囲を限定して監査可能性を保ちます。

## 使い方

```bash
python -m doc_preprocessor_hybrid.cli --api-doc data/src/api.txt --api-arg data/src/api_arg.txt --output-dir doc_preprocessor_hybrid/out
```

補強ステップを有効にするには、`--llm`（有効な `OPENAI_API_KEY` が必要）を追加してください。
