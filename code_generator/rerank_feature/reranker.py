import logging
from typing import List
from langchain_core.documents import Document

# 注意：このコードを実行するには、`sentence-transformers`ライブラリが必要です。
# pip install sentence-transformers
#
# 現在の環境ではディスク容量の問題でインストールできないため、
# このモジュールはコード生成のみ行い、直接の実行・テストは行いません。

logger = logging.getLogger(__name__)

class ReRanker:
    """
    sentence-transformersのクロスエンコーダーモデルを使い、
    検索結果のドキュメントリストをクエリとの関連性で並べ替える（Re-Rankする）クラス。
    """
    def __init__(self, model_name: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2'):
        """
        ReRankerを初期化し、クロスエンコーダーモデルをロードします。

        Args:
            model_name: 使用するクロスエンコーダーモデルの名前。
        """
        self.model = None
        self.model_name = model_name
        self._load_model()

    def _load_model(self):
        """モデルをロードします。ライブラリがない場合はスキップします。"""
        try:
            from sentence_transformers import CrossEncoder
            logger.info(f"クロスエンコーダーモデル '{self.model_name}' をロードしています...")
            self.model = CrossEncoder(self.model_name)
            logger.info("モデルのロードが完了しました。")
        except ImportError:
            logger.warning("`sentence-transformers`ライブラリが見つかりません。")
            logger.warning("ReRankerは非アクティブモードで動作します。並べ替えは行われません。")
        except Exception as e:
            logger.error(f"モデルのロード中にエラーが発生しました: {e}")
            logger.warning("ReRankerは非アクティブモードで動作します。")

    def rerank(self, query: str, documents: List[Document]) -> List[Document]:
        """
        与えられたドキュメントのリストを、クエリとの関連性スコアで並べ替えます。

        Args:
            query: ユーザーの元のクエリ文字列。
            documents: 並べ替え対象のLangChainドキュメントのリスト。

        Returns:
            スコアで降順にソートされたドキュメントのリスト。
            モデルがロードされていない場合は、元のリストをそのまま返します。
        """
        if not self.model or not documents:
            return documents

        logger.info(f"{len(documents)}件のドキュメントをRe-Rankします...")

        # クロスエンコーダーは[クエリ, ドキュメント内容]のペアのリストを入力として受け取る
        pairs = [[query, doc.page_content] for doc in documents]

        # スコアを予測
        scores = self.model.predict(pairs)

        # 各ドキュメントにスコアを付与
        for doc, score in zip(documents, scores):
            doc.metadata['rerank_score'] = float(score)

        # スコアに基づいてドキュメントを降順にソート
        sorted_documents = sorted(documents, key=lambda x: x.metadata['rerank_score'], reverse=True)

        logger.info("Re-Rankが完了しました。")
        return sorted_documents

if __name__ == '__main__':
    # このモジュールは直接実行できません（依存関係のため）
    # 以下は、実際の利用方法を示すサンプルコードです。

    print("--- ReRanker 利用サンプル ---")

    # サンプルデータ
    sample_query = "how to create a sphere"
    sample_docs = [
        Document(page_content="A ball can be created using the CreateBall function.", metadata={"id": "doc1"}),
        Document(page_content="To make a spherical object, use the CreateSphere API.", metadata={"id": "doc2"}),
        Document(page_content="The CreateCube function generates a box.", metadata={"id": "doc3"}),
    ]

    print(f"Query: {sample_query}")
    print("\nOriginal documents:")
    for doc in sample_docs:
        print(f"  - {doc.metadata['id']}: {doc.page_content}")

    # ReRankerのインスタンス化と実行
    # 注：実際にこれを動かすにはsentence-transformersのインストールが必要です
    reranker = ReRanker()
    if reranker.model:
        reranked_docs = reranker.rerank(sample_query, sample_docs)

        print("\nReranked documents:")
        for doc in reranked_docs:
            print(f"  - {doc.metadata['id']}: (Score: {doc.metadata['rerank_score']:.4f}) {doc.page_content}")
    else:
        print("\nReRanker is not active. Skipping reranking.")
