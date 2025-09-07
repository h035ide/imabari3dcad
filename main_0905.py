import sys
import argparse
import os
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 環境変数を読み込み
load_dotenv()


class Config:
    """設定クラス - 全ての設定を一元管理"""

    def __init__(self):
        self.project_root = project_root

        # Neo4j設定（環境変数から読み込み）
        self.neo4j_uri = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        self.neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")

        # OpenAI設定（環境変数から読み込み）
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        # ファイルパス設定
        self.parsed_api_result_def_file = (
            "doc_parser/parsed_api_result_def.json"
        )
        self.parsed_api_result_file = "doc_parser/parsed_api_result.json"

        # Chroma設定
        self.chroma_persist_directory = "chroma_db_store"
        self.chroma_collection_name = "api_documentation"

        # LlM設定
        self.setup_llm_config()
        self.setup_embedding_config()
    
    def setup_llm_config(self):
        """LLM設定"""
        # 基本設定
        self.llm_model = "gpt-4o"
        self.response_format = "text"  # "json_object"
        # only for standard models
        self.llm_temperature = 0.1  # or None
        # only for inference models
        self.llm_verbosity = "high"  # "none" or "low" or "medium" or "high"
        self.llm_reasoning_effort = "high"  # "none" or "minimal" or "low" or "medium" or "high"
        
        # モデル判定
        self.is_inference_model = self._is_inference_model()
        
        # 設定辞書を構築
        self._build_llm_configs()
    
    def _is_inference_model(self):
        """推論モデルかどうかを判定"""
        inference_models = [
            "o4-mini", "o4", "gpt-5", "gpt-5-mini", "gpt-5-nano"
        ]
        return any(model in self.llm_model.lower()
                   for model in inference_models)
    
    def _build_llm_configs(self):
        """LLM設定辞書を構築"""
        # 基本設定
        base_config = {
            "api_key": self.openai_api_key
        }
        
        # LangChain用設定
        self.langchain_llm_config = {
            "model_name": self.llm_model,
            **base_config
        }
        
        # LlamaIndex用設定
        self.llamaindex_llm_config = {
            "model": self.llm_model,
            **base_config
        }
        
        # モデル別パラメータを追加
        if self.is_inference_model:
            self._add_inference_model_params()
        else:
            self._add_standard_model_params()
    
    def _add_inference_model_params(self):
        """推論モデル専用パラメータを追加"""
        # 推論モデルではtemperatureは使用しない
        self.llm_temperature = None
        
        inference_params = {
            "reasoning_effort": self.llm_reasoning_effort,
            "output_version": "responses/v1",
            "verbosity": self.llm_verbosity,
            "response_format": self.response_format
        }
        
        for key, value in inference_params.items():
            self.langchain_llm_config[key] = value
            self.llamaindex_llm_config[key] = value
    
    def _add_standard_model_params(self):
        """通常モデルのパラメータを追加"""
        # 通常モデルでは推論モデルパラメータは使用しない
        self.llm_verbosity = None
        self.llm_reasoning_effort = None
        
        # temperatureを追加
        if self.llm_temperature is not None:
            self.langchain_llm_config["temperature"] = self.llm_temperature
            self.llamaindex_llm_config["temperature"] = self.llm_temperature

    def setup_embedding_config(self):
        """埋め込みモデル設定"""
        # 基本設定
        self.embedding_model = "text-embedding-3-small"
        self.embedding_batch_size = 100
        
        # LangChain用設定
        self.langchain_embedding_config = {
            "model": self.embedding_model,
            "api_key": self.openai_api_key
        }
        
        # LlamaIndex用設定
        self.llamaindex_embedding_config = {
            "model": self.embedding_model,
            "batch_size": self.embedding_batch_size,
            "api_key": self.openai_api_key
        }
    
    def print_llm_config(self):
        """LLM設定を表示"""
        print("🤖 LLM設定:")
        print(f"  モデル: {self.llm_model}")
        print(f"  推論モデル: {'✅' if self.is_inference_model else '❌'}")
        print(f"  Temperature: {self.llm_temperature}")
        print(f"  Response Format: {self.response_format}")
        
        if self.is_inference_model:
            print(f"  Verbosity: {self.llm_verbosity}")
            print(f"  Reasoning Effort: {self.llm_reasoning_effort}")
        
        print("\n📋 LangChain設定:")
        for key, value in self.langchain_llm_config.items():
            print(f"  {key}: {value}")
        print("\n📋 LlamaIndex設定:")
        for key, value in self.llamaindex_llm_config.items():
            print(f"  {key}: {value}")


def run_nollm_doc():
    """No LLM ドキュメント処理を実行"""
    try:
        print("No LLM ドキュメント処理を実行中...")
        # ここに実際の処理を実装
        return True
    except Exception as e:
        print(f"エラー: {e}")
        return False


def run_llm_doc():
    """LLM ドキュメント処理を実行"""
    try:
        from doc_parser.neo4j_importer import import_to_neo4j

        # Configから設定を取得
        config = Config()

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


def run_vectorization():
    """LlamaIndexを使用した効率的なベクトル化"""
    try:
        from code_generator.db.ingest_to_chroma import (
            fetch_data_from_neo4j,
            ingest_data_to_chroma
        )

        # Configから設定を取得
        config = Config()

        print("Neo4jからAPIデータを取得中...")
        # Functionノードを取得（Neo4jのラベルに合わせて調整）
        records = fetch_data_from_neo4j(
            label="Function",
            db_name=config.neo4j_database,
            allow_missing_description=True
        )

        if not records:
            print("ベクトル化するデータが見つかりませんでした。")
            return False

        print(f"{len(records)}件のAPI関数をベクトル化中...")
        # Chromaにベクトル化して保存
        ingest_data_to_chroma(
            records=records,
            collection_name=config.chroma_collection_name,
            persist_dir=config.chroma_persist_directory
        )

        print("✅ Chromaベクトル化完了")
        return True

    except Exception as e:
        print(f"ベクトル化エラー: {e}")
        return False


def run_llamaindex_vectorization():
    """LlamaIndexを使用した高度なベクトル化"""
    try:
        from llama_index.core import VectorStoreIndex, StorageContext, Settings
        from llama_index.vector_stores.chroma import ChromaVectorStore
        from llama_index.embeddings.openai import OpenAIEmbedding
        from llama_index.llms.openai import OpenAI
        import chromadb

        # Configから設定を取得
        config = Config()
        
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

        # LlamaIndexの設定
        Settings.llm = OpenAI(**config.llamaindex_llm_config)
        Settings.embed_model = OpenAIEmbedding(**config.llamaindex_embedding_config)

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

        # 既存のベクトルストアからインデックスを構築
        VectorStoreIndex.from_vector_store(
            vector_store,
            storage_context=storage_context
        )

        print("✅ LlamaIndexベクトル化完了")
        print(f"  → コレクション: {config.chroma_collection_name}")
        print(f"  → 永続化ディレクトリ: "
              f"{config.chroma_persist_directory}")

        return True

    except Exception as e:
        print(f"LlamaIndexベクトル化エラー: {e}")
        return False


def run_qa_system():
    """LlamaIndexを使用した効率的なQAシステム"""
    try:
        from code_generator.llamaindex_integration import (
            build_vector_engine,
            build_graph_engine
        )
        from llama_index.core import Settings
        from llama_index.llms.openai import OpenAI

        # Configから設定を取得
        config = Config()


        # LlamaIndexの設定
        Settings.llm = OpenAI(**config.llamaindex_llm_config)

        # ユーザーに質問を入力してもらう
        print("\n🔍 LlamaIndex統合QAシステム")
        print("=" * 50)
        print("📋 ハイブリッド検索システム:")
        print("  • ベクトル検索: ChromaDB（意味的類似性）")
        print("  • グラフ検索: Neo4j（構造的関係性）")
        print("  • 統合回答: 両方の結果を組み合わせた包括的回答")
        print("=" * 50)
        question = input("質問を入力してください: ").strip()

        if not question:
            print("❌ 質問が入力されていません。")
            return False

        print(f"\n📝 質問: {question}")
        print("🔍 ハイブリッド検索中...")

        # 1. ベクトル検索エンジンを構築
        print("  → ベクトル検索エンジンを構築中...")
        try:
            vector_engine = build_vector_engine(
                persist_dir=config.chroma_persist_directory,
                collection=config.chroma_collection_name
            )
        except Exception as e:
            print(f"❌ ベクトル検索エンジンの構築に失敗: {e}")
            return False

        # 2. グラフ検索エンジンを構築
        print("  → グラフ検索エンジンを構築中...")
        try:
            graph_engine = build_graph_engine()
        except Exception as e:
            print(f"⚠️ グラフ検索エンジンの構築に失敗: {e}")
            print("  → ベクトル検索のみで実行します...")
            graph_engine = None

        # 3. ハイブリッド検索実行
        print("  → ベクトル検索を実行中...")
        vector_response = vector_engine.query(question)

        if graph_engine:
            print("  → グラフ検索を実行中...")
            graph_response = graph_engine.query(question)

            # ハイブリッド回答の統合
            print("  → ハイブリッド回答を生成中...")
            combined_question = f"""
            以下の2つの検索結果を統合して、ユーザーの質問に包括的に回答してください。

            【ベクトル検索結果】
            {vector_response}

            【グラフ検索結果】
            {graph_response}

            【ユーザーの質問】
            {question}

            回答のガイドライン:
            - 両方の検索結果の情報を統合
            - 具体的なAPI関数名とその使用方法を明記
            - パラメータの詳細と戻り値について説明
            - 実用的なコード例があれば提供
            - 不明な点は正直に「不明」と回答
            """
            final_response = vector_engine.query(combined_question)
        else:
            final_response = vector_response

        # 4. 結果を表示
        print("\n" + "=" * 50)
        print("🤖 回答:")
        print("=" * 50)
        print(final_response)
        print("=" * 50)

        return True

    except Exception as e:
        print(f"❌ QAシステムエラー: {e}")
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
    parser.add_argument("--list", "-l", action="store_true", help="機能一覧表示")
    
    args = parser.parse_args()
    
    # if args.list:
    #     print("利用可能な機能:")
    #     print("  code_generator  - AIコード生成")
    #     print("  test_runner     - テスト実行")
    #     print("  doc_parser      - ドキュメント解析")
    #     print("  all            - 全機能実行")
    #     return
    
    print(f"実行中: {args.function}")
    
    if args.function == "nollm_doc":
        success = run_nollm_doc()
    elif args.function == "llm_doc":
        success = run_llm_doc()
    elif args.function == "vectorize":
        success = run_vectorization()
    elif args.function == "llm_doc_and_vectorize":
        success = (run_llm_doc() and run_vectorization())
    elif args.function == "full_pipeline":
        # 完全パイプライン: Neo4j → ChromaDB → LlamaIndex
        print("🚀 完全パイプライン実行中...")
        success = (run_llm_doc() and 
                  run_vectorization() and 
                  run_llamaindex_vectorization())
    elif args.function == "qa":
        success = run_qa_system()
    elif args.function == "llamaindex_vectorize":
        success = run_llamaindex_vectorization()
    elif args.function == "config":
        config = Config()
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
