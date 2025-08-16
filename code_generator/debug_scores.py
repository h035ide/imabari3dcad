#!/usr/bin/env python3
"""
Chromaの類似度スコア分布を簡易的に確認するスクリプト

出力:
 - 各候補のスコア一覧
 - 平均(mean) と 標準偏差(std)

使用例:
  python debug_scores.py --query "球を作成する関数" --k 10
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

try:
    import numpy as np
except Exception:
    np = None

logger = logging.getLogger(__name__)


def build_vectorstore(persist_dir: str, collection: str, api_key: str):
    emb = OpenAIEmbeddings(api_key=api_key)
    vs = Chroma(collection_name=collection, embedding_function=emb, persist_directory=persist_dir)
    return vs


def main():
    parser = argparse.ArgumentParser(description="Chromaスコア分布の簡易確認")
    parser.add_argument("--query", "-q", default="球を作成する関数", help="検索クエリ")
    parser.add_argument("--k", "-k", type=int, default=10, help="取得する候補数")
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

        results = vs.similarity_search_with_score(args.query, k=args.k)
        scores = [s for _, s in results]

        print(f"query= {args.query}")
        print("scores=", scores)

        if np is not None and scores:
            print("mean=", np.mean(scores), "std=", np.std(scores))
        else:
            # numpyが無ければ簡易計算
            if scores:
                mean = sum(scores) / len(scores)
                var = sum((x - mean) ** 2 for x in scores) / len(scores)
                std = var ** 0.5
                print("mean=", mean, "std=", std)
            else:
                print("スコアが取得できませんでした。")

    except Exception as e:
        logger.exception("スコア確認中にエラーが発生しました")
        print(f"ERROR: {e}")


if __name__ == '__main__':
    main()


