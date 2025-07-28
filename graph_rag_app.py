import os
from dotenv import load_dotenv
from llama_index.core import (
    KnowledgeGraphIndex, # 知識グラフ用のインデックス
    SimpleDirectoryReader,
    Settings,
    StorageContext,
)
from llama_index.core.graph_stores import SimpleGraphStore # グラフを保存するストア
from llama_index.llms.openai import OpenAI
from pyvis.network import Network # グラフ可視化ライブラリ

# .envファイルから環境変数を読み込む
load_dotenv()

# 🧠 1. LLMの指定
# 構造化データの抽出には高性能なモデルが推奨されるため、gpt-4o を指定
Settings.llm = OpenAI(model="gpt-4o-mini")
# Embeddingモデルも指定（任意）
# Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")

# 2. データの読み込み
print("ドキュメントを読み込んでいます...")
documents = SimpleDirectoryReader("./data/api_doc").load_data()

# 3. グラフストアとストレージコンテキストの準備
graph_store = SimpleGraphStore()
storage_context = StorageContext.from_defaults(graph_store=graph_store)

# 4. 知識グラフインデックスの構築
# この処理の中で、LLMがテキストから知識（エンティティと関係性のタプル）を抽出し、グラフを構築します。
print("知識グラフを構築しています...（時間がかかる場合があります）")
index = KnowledgeGraphIndex.from_documents(
    documents,
    storage_context=storage_context,
    max_triplets_per_chunk=2, # 1チャンクから抽出する知識の最大数
)
print("グラフの構築が完了しました。")

# 5. クエリエンジンの作成と問い合わせ
query_engine = index.as_query_engine()
response = query_engine.query("CreateVariable 関数は何を返しますか？")

print("\n--- 応答 ---")
print(response)
print("------------\n")

# 6. グラフの可視化
print("グラフを 'graph.html' として保存しています...")
g = index.get_networkx_graph()

# --- ↓ここからデバッグコードを追加 ---
print("\n--- グラフ情報 ---")
print(f"ノード数 (エンティティ): {len(g.nodes)}")
print(f"エッジ数 (関係性): {len(g.edges)}")
print("--------------------\n")
# --- ↑ここまでデバッグコード ---

# 1. pyvisのNetworkオブジェクトを初期化
net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white", directed=True)

# 2. net.from_nx(g) を使わずに、手動でノードとエッジを追加
#    これにより、ライブラリ内部の問題を回避します。

# ノード（エンティティ）を手動で追加
for node in g.nodes:
    net.add_node(node, label=node)

# エッジ（関係性）を手動で追加
# g.edges(data=True)でエッジの属性（ラベルなど）も取得
for source, target, data in g.edges(data=True):
    # エッジのラベルを取得（存在しない場合も考慮）
    label = data.get("label", "")
    net.add_edge(source, target, label=label)

# 3. UTF-8を指定して手動でファイルに書き出す
with open("graph.html", mode="w", encoding="utf-8") as fp:
    fp.write(net.html)
print("保存が完了しました。graph.htmlを開いて確認してください。")