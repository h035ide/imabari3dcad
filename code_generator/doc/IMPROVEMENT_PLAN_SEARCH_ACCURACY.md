# 検索精度改善計画（短期・中期の実装手順）

このドキュメントは、`code_generator/` モジュールにおける検索精度低下の疑いに対する調査手順と、優先度順の具体的実装手順をまとめたものです。まず短期で実行すべき診断を行い、原因に応じて中期〜長期の実装を進めます。

作成日: 2025年1月
対象: `code_generator/`（`tools.py`, `llamaindex_integration.py`, `db/ingest_to_chroma.py` など）

---

## 目的
- 現状での検索（Chroma + Neo4j / LlamaIndex）結果の精度が十分でないため、原因を特定し、短期〜中期で改善する。
- データ層（格納・整合性）、検索パイプライン（埋め込み・類似検索・Re-Ranking）、およびプロンプト（LLM側）の観点から改善案を提示する。

---

## 概要フロー（トリアージ）
1. 短期診断（データ存在・整合性、スコア分布の確認）
2. 中期対策（閾値調整、Re-Ranking有効化、プロンプト改善）
3. 長期改善（評価基盤・自動化・テスト）

---

## 優先度: 高 — 今すぐ確認すべき項目（診断）

1) ChromaDBのデータ存在とメタデータ整合性確認
- 目的: ドキュメントが正しく格納され、`neo4j_node_id` と `api_name` が入っているか確認する。
- 実行コマンド（プロジェクトルートで実行）:

```bash
python -c "from langchain_community.vectorstores import Chroma; from langchain_openai import OpenAIEmbeddings; import os
emb=OpenAIEmbeddings(api_key=os.getenv('OPENAI_API_KEY'))
vs=Chroma(collection_name='api_functions', embedding_function=emb, persist_directory='chroma_db_store')
print('doc_count=', len(vs._collection.get()['metadatas']))
" | cat
```

- 推奨（より安全な方法）: 以下の簡易診断スクリプトを作成して実行する。

```python
# debug_chroma.py
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
import os

CHROMA_DIR = 'chroma_db_store'
COL = 'api_functions'
emb = OpenAIEmbeddings(api_key=os.getenv('OPENAI_API_KEY'))
vs = Chroma(collection_name=COL, embedding_function=emb, persist_directory=CHROMA_DIR)

results = vs.similarity_search_with_score('テストクエリ', k=1)
print('サンプル実行:')
for doc, score in results:
    print('score=', score)
    print('metadata=', doc.metadata)
    print(doc.page_content[:200])
```

> 注意: 環境により `vs._collection` の内部APIが変更されている可能性があるため、`similarity_search_with_score` を利用した確認が確実です。


2) Neo4jのノード存在とスキーマ確認
- 目的: Chroma の `neo4j_node_id` が Neo4j に対応しているか確認する。
- 実行例（Neo4j Browser / cypher）:

```cypher
MATCH (n:ApiFunction) RETURN count(n);
MATCH (n:ApiFunction) RETURN elementId(n) AS id, n.name LIMIT 10;
```

- 対応がなければ、`db/ingest_to_chroma.py` の実行ログを確認して再インジェストする。

3) 類似度スコア分布の可視化
- 目的: 上位候補のスコア差が小さい（均一）場合、曖昧判定が多発する。スコア分布を確認して閾値が妥当か判断する。
- 実行スクリプト（例）:

```python
# debug_scores.py
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
import os, numpy as np

emb = OpenAIEmbeddings(api_key=os.getenv('OPENAI_API_KEY'))
vs = Chroma(collection_name='api_functions', embedding_function=emb, persist_directory='chroma_db_store')
query = '球を作成する関数'
results = vs.similarity_search_with_score(query, k=10)
scores = [s for _, s in results]
print('scores=', scores)
print('mean=', np.mean(scores), 'std=', np.std(scores))
```

- 得られた分布をもとに、`AMBIGUITY_ABSOLUTE_THRESHOLD` / `AMBIGUITY_RELATIVE_THRESHOLD` を調整する。

---

## 優先度: 中 — 実装・調整（診断結果に基づき実行）

1) Re-Rankingの一時有効化（比較実験）
- 目的: クロスエンコーダや外部スコアで上位を再評価し、検索精度が改善するか確認する。
- 手順:
  a. 開発環境（ローカル）に `sentence-transformers` をインストールする。

```bash
pip install sentence-transformers
```

  b. `code_generator/rerank_feature/reranker.py` のインポートを `tools.py` で有効化し、オプションのフラグでON/OFFできるようにする。

- 推奨変更（`tools.py` 内の該当箇所）:

```python
# 先頭で
from code_generator.rerank_feature.reranker import ReRanker
USE_RERANKING = os.getenv('USE_RERANKING', '0') == '1'

# ベクトル検索後
results = [doc for doc, score in results_with_scores]
if USE_RERANKING:
    reranker = ReRanker()
    if reranker.model:
        results = reranker.rerank(query, results)
# 続けて neo4j_node_id の抽出
```

  c. Re-Rankingを有効化して、Precision@k を比較する（評価データがあれば定量比較）。

2) 閾値ロジックの改善
- 目的: Chromaのスコア尺度（L2 or cosine）に合わせて閾値判定を正しく行う。
- 実装案:
  - `AMBIGUITY_ABSOLUTE_THRESHOLD` を「スコア差」ではなく「正規化差（max-minで割る）」や「cosineの場合は1 - score」などに調整。

例:
```python
scores = [s for _, s in results_with_scores]
if max(scores) - min(scores) > 0:
    normalized_diff = (scores[1] - scores[0]) / (max(scores) - min(scores))
else:
    normalized_diff = 0
```

3) LlamaIndex側のフォールバック改善
- 目的: `llamaindex_integration.py` が失敗した際の明確なフォールバックを実装する。
- 実装案:

```python
try:
    graph_query_engine = build_graph_engine()
except Exception:
    graph_query_engine = None

if graph_query_engine is None:
    # graphツールを外し、vectorのみでRouterを構築
```

4) プロンプト改善（few-shot + retrieval metadataの利用）
- 目的: LLMに渡す検索結果のフォーマットを改善し、LLM側での判別/選択精度を向上させる。
- 実装要点:
  - 検索結果に `score` と `source_id`（Neo4jノードID）を付与
  - system_promptに「スコアが高い順に例示し、signature を優先する」等のルールを追加
  - 良い/悪いマッチのfew-shot例を2–3組追加

例（format）:
```
[検索結果]
1) api_name: CreateSphere (score: 0.12, node: 1234)
   description: 球を作成する関数。signature: create_sphere(radius)
2) api_name: CreateBall (score: 0.13, node: 5678)
   description: 球体（旧実装）。signature: create_ball(diameter)
```

---

## 優先度: 低 — 評価基盤・自動化（長期）

1) 評価データセット作成
- 数十〜百件の代表クエリと期待解（Neo4jノードID）を作成。
- 指標: Recall@k, Precision@k, MRR を算出して改善の効果を定量化する。

2) CI による差分評価
- Re-Ranking ON/OFF、閾値変更などバリエーションをCIで自動評価する。

3) ログとモニタリング
- 各検索の top-k スコア・candidate list をログとして残し、時系列で解析可能にする。

---

## 具体的なスクリプト・パッチ例（貼付）

1) `debug_chroma.py`（前述） — Chromaの類似度確認
2) `debug_scores.py`（前述） — スコアの統計
3) `tools.py` の小パッチ（Re-Rankingフラグと処理の挿入）

---

## 実行優先順（推奨）
1. `debug_chroma.py` を実行してドキュメント存在とmetadataを確認（所要: 10–30分）
2. `debug_scores.py` でスコア分布を確認し、閾値調整の仮設定（所要: 30–60分）
3. Re-Rankingをdevで一時有効化して比較実験（数時間）
4. LlamaIndexのフォールバック改善とプロンプトのfew-shot追加（1–2日）
5. 評価データセットの整備とCI導入（1–2週間）

---

## 次のアクション（私が支援できること）
- 今すぐ `debug_chroma.py` と `debug_scores.py` を実行するための手順をさらに細かく作成します（あなたの環境で実行してもらう）。
- `tools.py` に対する Re-Ranking 有効化パッチを作成します（差分パッチを用意）。
- LlamaIndex フォールバックのパッチを作成します。
- 評価用の小さなデータセットテンプレート（CSV/JSON）を作成します。

どれを先に進めましょうか？（おすすめ: まず `debug_chroma.py` の実行）
