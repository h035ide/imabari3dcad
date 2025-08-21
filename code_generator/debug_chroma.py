#!/usr/bin/env python3
"""
簡易的なChromaDBデバッグスクリプト
- ドキュメント数の確認
- 単一クエリでの類似検索とメタデータ表示

使用例:
  python debug_chroma.py --query "球を作成する関数" --k 3
"""
import os
import argparse
import logging
import sys
from dotenv import load_dotenv

# --- [Path Setup] ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# .envファイルを読み込む
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path)
# --- [End Path Setup] ---

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

logger = logging.getLogger(__name__)


def build_vectorstore(persist_dir: str, collection: str, api_key: str):
    emb = OpenAIEmbeddings(api_key=api_key)
    vs = Chroma(collection_name=collection, embedding_function=emb, persist_directory=persist_dir)
    return vs


def main():
    parser = argparse.ArgumentParser(description="ChromaDBの簡易デバッグツール")
    parser.add_argument("--query", "-q", default="テストクエリ", help="検索クエリ（日本語可）")
    parser.add_argument("--k", "-k", type=int, default=1, help="取得する候補数")
    args = parser.parse_args()

    # `project_root` はファイル先頭で設定済みなので再定義しない
    chroma_dir = os.path.join(project_root, "chroma_db_store")
    collection = os.getenv("CHROMA_COLLECTION_NAME", "api_functions")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY が設定されていません。環境変数を確認してください。")
        return

    if not os.path.exists(chroma_dir):
        print(f"ERROR: Chromaの永続化ディレクトリが見つかりません: {chroma_dir}")
        return

    try:
        vs = build_vectorstore(chroma_dir, collection, api_key)

        # ドキュメント数（内部APIを使うため環境依存）
        try:
            coll = vs._collection.get()
            doc_count = len(coll.get("metadatas", []))
        except Exception:
            doc_count = None

        print(f"doc_count= {doc_count}")

        results = vs.similarity_search_with_score(args.query, k=args.k)
        print("サンプル実行:")
        for idx, (doc, score) in enumerate(results):
            print(f"--- candidate:{idx+1} ---")
            print("score=", score)
            print("metadata=", doc.metadata)
            content = (doc.page_content or "").strip()
            print(content[:800])
            print()

    except Exception as e:
        logger.exception("ChromaDBデバッグ中にエラーが発生しました")
        print(f"ERROR: {e}")


if __name__ == '__main__':
    main()


