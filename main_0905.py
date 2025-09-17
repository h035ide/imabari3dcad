import sys
import os
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv
from main_helper_0905 import Config
from neo4j import GraphDatabase
import re
from typing import Optional

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 環境変数を読み込み
load_dotenv()

# ロギング設定: LOG_LEVEL 環境変数で調整（未設定は INFO）
_log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
_log_level = getattr(logging, _log_level_name, logging.INFO)
logging.basicConfig(
    level=_log_level,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


def run_nollm_doc(config: Config):
    """No LLM ドキュメント処理を実行（ingest0903.pyを使用）"""
    try:
        print("No LLM ドキュメント処理を実行中...")
        # パッケージ化した graphrag_gpt から通常インポートで実行
        from graphrag_gpt.ingest0903 import build_databases
        success = build_databases(config)

        if success:
            print("✅ No LLM ドキュメント処理が完了しました")
        else:
            print("❌ No LLM ドキュメント処理でエラーが発生しました")

        return success

    except Exception as e:
        print(f"エラー: {e}")
        return False


def run_llm_doc(config: Config):
    """LLM ドキュメント処理を実行"""
    try:
        from doc_parser.neo4j_importer import import_to_neo4j

        # Neo4jにデータをインポート
        success = import_to_neo4j(
            uri=config.neo4j_uri,
            user=config.neo4j_user,
            password=config.neo4j_password,
            database=config.neo4j_database,
            file_path=config.parsed_api_result_def_file,
            use_def_file=True,
            config=config
        )

        return success
    except Exception as e:
        print(f"エラー: {e}")
        return False


def run_vectorization(config: Config):
    """LlamaIndexを使用した効率的なベクトル化"""
    try:
        from main_helper_0905 import (
            fetch_data_from_neo4j,
            ingest_data_to_chroma
        )

        print("Neo4jからAPIデータを取得中...")
        # Functionノードを取得（Neo4jのラベルに合わせて調整）
        records = fetch_data_from_neo4j(
            label="Function",
            db_name=config.neo4j_database,
            allow_missing_description=True,
            config=config
        )

        if not records:
            print("ベクトル化するデータが見つかりませんでした。")
            return False

        print(f"{len(records)}件のAPI関数をベクトル化中...")
        # Chromaにベクトル化して保存
        ingest_data_to_chroma(
            records=records,
            collection_name=config.chroma_collection_name,
            persist_dir=config.chroma_persist_directory,
            config=config
        )

        print("✅ Chromaベクトル化完了")
        return True

    except Exception as e:
        print(f"ベクトル化エラー: {e}")
        return False


def run_llamaindex_vectorization(config: Config):
    """LlamaIndexを使用した高度なベクトル化"""
    try:
        from llama_index.core import VectorStoreIndex, StorageContext
        from llama_index.vector_stores.chroma import ChromaVectorStore
        from llama_index.embeddings.openai import OpenAIEmbedding
        import chromadb

        # 呼び出し元から受け取った Config を使用
        # 設定情報を表示
        print("🔧 LlamaIndexベクトル化設定:")
        print(f"  LLMモデル: {config.llm_model}")
        print(f"  埋め込みモデル: {config.embedding_model}")
        print(f"  バッチサイズ: {config.embedding_batch_size}")
        print(f"  Chroma永続化ディレクトリ: {config.chroma_persist_directory}")
        print(f"  Chromaコレクション: {config.chroma_collection_name}")
        if config.is_inference_model:
            print("  推論モデル設定:")
            print(f"    Verbosity: {config.llm_verbosity}")
            print(f"    Reasoning Effort: {config.llm_reasoning_effort}")
        else:
            print("  標準モデル設定:")
            print(f"    Temperature: {config.llm_temperature}")

        # LlamaIndexの埋め込みモデルを初期化（グローバル設定を避ける）
        embed_model = OpenAIEmbedding(
            **config.llamaindex_embedding_config
        )

        print("LlamaIndexを使用したベクトル化を開始...")

        # ChromaDBクライアントを作成
        client = chromadb.PersistentClient(
            path=config.chroma_persist_directory
        )
        chroma_collection = client.get_or_create_collection(
            config.chroma_collection_name
        )

        # LlamaIndexのベクトルストアを作成
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(
            vector_store=vector_store
        )

        # 既存のベクトルストアからインデックスを構築（embed_modelを明示的に指定）
        VectorStoreIndex.from_vector_store(
            vector_store,
            storage_context=storage_context,
            embed_model=embed_model
        )

        print("✅ LlamaIndexベクトル化完了")
        print(f"  → コレクション: {config.chroma_collection_name}")
        print(f"  → 永続化ディレクトリ: "
              f"{config.chroma_persist_directory}")

        return True

    except Exception as e:
        print(f"LlamaIndexベクトル化エラー: {e}")
        return False


def run_clear_database(
    config: Config,
    database: Optional[str] = None,
    force: bool = False,
):
    """Neo4jデータベースをクリアするユーティリティの実行"""
    try:
        from doc_parser.clear_database import clear_database as _clear

        target_db = database or config.neo4j_database or "docparser"
        print(
            f"データベースクリアを実行します: db={target_db}, "
            f"force={force}"
        )
        _clear(database=target_db, force=force)
        return True
    except Exception as e:
        print(f"クリアエラー: {e}")
        return False


def run_qa_system(config: Config):
    """LangChainでラップしたQAシステム（LangSmithでウォッチ可能）"""
    try:
        from main_helper_0905 import build_langchain_wrapped_engines

        # LangChainでラップしたエンジンを取得
        engines = build_langchain_wrapped_engines(config)
        vector_search = engines['vector_search']
        graph_search = engines['graph_search']
        generate_response = engines['generate_response']

        # ユーザーに質問を入力してもらう
        print("\nLangChain統合QAシステム（LangSmith対応）")
        print("=" * 50)
        print("ハイブリッド検索システム:")
        print("  - ベクトル検索: ChromaDB（意味的類似性）")
        print("  - グラフ検索: Neo4j（構造的関係性）")
        print("  - 統合回答: LangChainで生成（LangSmithでウォッチ可能）")
        print("=" * 50)
        question = input("質問を入力してください: ").strip()

        if not question:
            print("❌ 質問が入力されていません。")
            return False

        print(f"\n📝 質問: {question}")
        print("🔍 ハイブリッド検索中...")

        # 質問から関数名らしきキーワードを抽出
        vec_kw = question
        m_vec = re.search(
            r"`([^`]+)`|\"([^\"]+)\"|"
            r"([A-Za-z_][A-Za-z0-9_]*)",
            question,
        )
        if m_vec:
            vec_kw = next((g for g in m_vec.groups() if g), question)

        # 3. ハイブリッド検索実行（LangChainでラップ）
        print("  → ベクトル検索を実行中...")
        vector_response = vector_search(vec_kw)

        print("  → グラフ検索を実行中...")
        # グラフ検索用のプロンプトを具体化（Parameter/Type 関連を辿る）
        graph_question = f"""
        Execute this Cypher to get a function and its parameters:
        MATCH (f:Function)
        WHERE toLower(f.name) CONTAINS toLower('{vec_kw}')
        OPTIONAL MATCH (p:Parameter)
        WHERE toLower(p.parent_function) = toLower(f.name)
        WITH f, collect(p) AS params
        RETURN f.name AS name,
               f.description AS description,
               [q IN params WHERE q IS NOT NULL AND q.name IS NOT NULL |
                {{name:q.name, description:q.description, required:coalesce(q.is_required,false)}}] AS parameters,
               null AS return_value
        LIMIT 5

        Then summarize the results in Japanese, focusing on:
        - Function name and description
        - Parameters (引数) with descriptions and whether required
        - Return value (戻り値) if known; otherwise state 不明
        """
        # コールバックで空結果を検知（ログ/メトリクス等に活用可能）
        def _on_empty(info):
            diag = info.get("diagnosis") if isinstance(info, dict) else None
            print("  → グラフ検索結果が空です。fallbackを検討します...")
            if diag:
                print(
                    "    診断: "
                    f"Function件数={diag.get('function_count')}, "
                    f"keyword一致件数={diag.get('match_count_by_keyword')}, "
                    f"Parameter件数={diag.get('parameter_count')}"
                )
                names = diag.get("sample_function_names") or []
                if names:
                    print("    サンプルFunction名: " + ", ".join(map(str, names)))

        graph_response = graph_search(
            graph_question,
            on_empty=_on_empty,
            diagnose=True,
            keyword=vec_kw,
        )

        # フォールバック: グラフ応答が空の場合はNeo4jを直接検索
        if not graph_response or str(graph_response).strip() in (
            "",
            "Empty Response",
        ):
            try:
                print("  → グラフ結果が空のためNeo4jを直接照会...")
                with GraphDatabase.driver(
                    config.neo4j_uri,
                    auth=(config.neo4j_user, config.neo4j_password),
                ) as driver:
                    with driver.session(
                        database=config.neo4j_database
                    ) as session:
                        cypher = (
                            "MATCH (f:Function) "
                            "WHERE toLower(f.name) CONTAINS toLower($kw) "
                            "OPTIONAL MATCH (p:Parameter) "
                            "WHERE toLower(p.parent_function) = toLower(f.name) "
                            "WITH f, collect(p) AS params "
                            "RETURN f.name AS name, f.description AS description, "
                            "[q IN params WHERE q.name IS NOT NULL | q] AS parameters, null AS return_value "
                            "LIMIT 5"
                        )
                        # ベクトル用に抽出したキーワードをそのまま使用
                        kw = vec_kw
                        rows = list(session.run(cypher, kw=kw))
                        if rows:
                            parts = []
                            for r in rows:
                                nm = r.get("name")
                                desc = r.get("description") or ""
                                params = r.get("parameters") or []
                                retv = r.get("return_value")

                                def _fmt_param(p):
                                    if isinstance(p, dict):
                                        n = p.get("name")
                                        d = p.get("description")
                                        req = p.get("is_required") or p.get("required")
                                        return f"- {n}: {d} (required={req})"
                                    n = getattr(p, "name", None)
                                    d = getattr(p, "description", None)
                                    req = getattr(p, "is_required", None)
                                    return f"- {n}: {d} (required={req})"

                                param_lines = []
                                try:
                                    for p in params:
                                        if p and (isinstance(p, dict) and p.get("name") or getattr(p, "name", None)):
                                            param_lines.append(_fmt_param(p))
                                except Exception:
                                    param_lines = []

                                section = [f"{nm}:", desc]
                                if param_lines:
                                    section.append("parameters:\n" + "\n".join(param_lines))
                                if retv:
                                    section.append(f"return_value: {retv}")
                                parts.append("\n".join(section))
                            graph_response = "\n\n".join(parts)
                        else:
                            graph_response = ""
            except Exception:
                # フォールバック失敗時はそのまま続行
                pass

        # ハイブリッド回答の統合（LangChainで生成）
        print("  → ハイブリッド回答を生成中...")
        final_response = generate_response(vector_response, graph_response, question)

        # 4. 結果を表示
        print("\n" + "=" * 50)
        print("回答:")
        print("=" * 50)
        print(f"ベクトル検索結果: {vector_response}")
        print(f"グラフ検索結果: {graph_response}")
        print(f"ハイブリッド検索結果: {final_response}")
        print("=" * 50)

        return True

    except Exception as e:
        print(f"QAシステムエラー: {e}")
        return False


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="imabari3dcad メイン - ドキュメント解析とハイブリッド検索システム",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        ワークフロー:
        1. ドキュメント解析 → Neo4jデータ格納
        2. ベクトル化 → ChromaDB構築
        3. ハイブリッド検索 → Neo4j + ChromaDB

        使用例:
        python main_0905.py --function full_pipeline  # 完全パイプライン実行
        python main_0905.py --function qa            # ハイブリッド検索
        python main_0905.py --function config        # 設定表示
        """
    )
    parser.add_argument("--function", "-f", help="実行する機能")
    parser.add_argument("--question", "-q", help="QA用の質問（非対話）")
    parser.add_argument("--list", "-l", action="store_true", help="機能一覧表示")
    # クリア機能向け追加引数
    parser.add_argument(
        "--db",
        dest="db",
        help=(
            "クリア対象のデータベース名（未指定時は設定のNEO4J_DATABASE）"
        ),
    )
    parser.add_argument(
        "-y",
        "--yes",
        dest="yes",
        action="store_true",
        help="確認なしで実行（危険操作のため明示指定が必要）",
    )
    args = parser.parse_args()
    # if args.list:
    #     print("利用可能な機能:")
    #     print("  code_generator  - AIコード生成")
    #     print("  test_runner     - テスト実行")
    #     print("  doc_parser      - ドキュメント解析")
    #     print("  all            - 全機能実行")
    #     return

    print(f"実行中: {args.function}")
    config = Config()
    if args.function == "nollm_doc":
        success = run_nollm_doc(config)
    elif args.function == "llm_doc":
        success = run_llm_doc(config)
    elif args.function == "vectorize":
        success = run_vectorization(config)
    elif args.function == "full_pipeline":
        # 完全パイプライン: Neo4j → ChromaDB → LlamaIndex
        print("🚀 完全パイプライン実行中...")
        success = (
            run_llm_doc(config)
            and run_vectorization(config)
            and run_llamaindex_vectorization(config)
        )
    elif args.function == "qa":
        if args.question:
            # 非対話モード
            def _input(prompt: str = ""):
                return args.question or ""
            import builtins
            _orig_input = builtins.input
            try:
                builtins.input = _input  # type: ignore
                success = run_qa_system(config)
            finally:
                builtins.input = _orig_input  # type: ignore
        else:
            success = run_qa_system(config)
    elif args.function == "llamaindex_vectorize":
        success = run_llamaindex_vectorization(config)
    elif args.function == "clear_db":
        success = run_clear_database(
            config,
            database=args.db,
            force=args.yes,
        )
    elif args.function == "config":
        config.print_llm_config()
        success = True
    else:
        print(f"未知の機能: {args.function}")
        success = False
    if success:
        print("✅ 完了")
    else:
        print("❌ エラー")
        sys.exit(1)


if __name__ == "__main__":
    main()
