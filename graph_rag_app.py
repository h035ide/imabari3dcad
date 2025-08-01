import os
import logging
import sys
from dotenv import load_dotenv

from llama_index.core import (
    SimpleDirectoryReader,
    KnowledgeGraphIndex,
    StorageContext
)
from llama_index.graph_stores.neo4j import Neo4jGraphStore
from llama_index.llms.openai import OpenAI
from langchain.tools import Tool
from llama_index.core.node_parser import MarkdownNodeParser

from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferWindowMemory

# --- 0. 設定とセットアップ ---

# .envファイルから環境変数を読み込む
load_dotenv()

# OpenAI APIキーのチェック
if not os.getenv("OPENAI_API_KEY"):
    logging.error("OPENAI_API_KEY環境変数が設定されていません。")
    sys.exit(1)

# 知識グラフ構築の制御
# SKIP_GRAPH_BUILD=true の場合、既存の知識グラフを使用（高速起動）
# SKIP_GRAPH_BUILD=false の場合、ドキュメントから知識グラフを再構築
SKIP_GRAPH_BUILD = os.getenv("SKIP_GRAPH_BUILD", "false").lower() == "true"

# グラフデータクリアの制御
# CLEAR_GRAPH_DATA=true の場合、起動時に既存のグラフデータをクリア
# CLEAR_GRAPH_DATA=false の場合、既存データを保持
CLEAR_GRAPH_DATA = os.getenv("CLEAR_GRAPH_DATA", "false").lower() == "true"

# 基本的なロギング設定
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

# LangSmithの設定確認
if os.getenv("LANGSMITH_API_KEY"):
    logging.info("✅ LangSmith監視が有効になっています。")
    logging.info(f"プロジェクト名: {os.getenv('LANGSMITH_PROJECT', 'imabari3dcad-api-docs')}")
else:
    logging.warning("⚠️ LANGSMITH_API_KEYが設定されていません。LangSmith監視は無効です。")
    logging.info("LangSmith監視を有効にするには、.envファイルにLANGSMITH_API_KEYを追加してください。")

# --- 1. Neo4jへの接続とGraphStoreの定義 ---
# .envファイルから接続情報を取得
logging.info("Neo4jデータベースに接続しています...")
try:
    # 環境変数の取得とデフォルト値の設定
    neo4j_username = os.getenv("NEO4J_USERNAME", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    if not neo4j_password:
        logging.error("NEO4J_PASSWORD環境変数が設定されていません。")
        sys.exit(1)
    
    graph_store = Neo4jGraphStore(
        username=neo4j_username,
        password=neo4j_password,
        url=neo4j_uri,
        database=neo4j_database,
    )
    storage_context = StorageContext.from_defaults(graph_store=graph_store)
    
    # 既存のグラフデータをクリアするオプション（必要に応じてコメントアウトを解除）
    if CLEAR_GRAPH_DATA:
        try:
            # Neo4jのクエリを直接実行してグラフデータをクリア
            graph_store.query("MATCH (n) DETACH DELETE n")
            logging.info("既存のグラフデータをクリアしました。")
        except Exception as clear_error:
            logging.warning(f"グラフデータのクリアに失敗しました（既存データがない可能性）: {clear_error}")
except Exception as e:
    logging.error(f"Neo4jへの接続に失敗しました: {e}")
    logging.error(f"接続情報: URI={neo4j_uri}, Database={neo4j_database}, Username={neo4j_username}")
    if hasattr(e, '__traceback__'):
        import traceback
        logging.error(f"トレースバック: {traceback.format_exc()}")
    sys.exit(1)

# --- 2. ドキュメントの読み込みと知識グラフの構築 ---
# この処理はリソースを消費するため、ドキュメントが変更された場合のみ実行するのが理想的です。

if SKIP_GRAPH_BUILD:
    logging.info("⚠️ SKIP_GRAPH_BUILDが設定されているため、知識グラフの構築をスキップします。")
    logging.info("既存の知識グラフを使用します。")
    
    # 既存のインデックスを読み込む
    try:
        # 最新のLlamaIndexでは、インデックスの読み込み方法が変更されている
        # まず、Neo4jに既存のデータが存在するかチェック
        try:
            # Neo4jからノード数を確認
            result = graph_store.query("MATCH (n) RETURN count(n) as count")
            node_count = result[0]['count'] if result else 0
            
            if node_count > 0:
                logging.info(f"Neo4jに {node_count} 個のノードが存在します。")
                # 既存のグラフデータがある場合は、最小限のインデックスを作成
                from llama_index.core import Document
                empty_doc = Document(text="placeholder")
                index = KnowledgeGraphIndex(
                    [empty_doc],
                    storage_context=storage_context,
                    max_triplets_per_chunk=0,  # トリプレット抽出を無効化
                    show_progress=False,
                    include_embeddings=False,  # 埋め込みを無効化
                    embed_kg_triplets=False,   # KGトリプレット埋め込みを無効化
                )
                logging.info("✅ 既存の知識グラフを読み込みました。")
            else:
                raise Exception("Neo4jに既存のグラフデータが存在しません。")
                
        except Exception as graph_error:
            logging.error(f"❌ 既存の知識グラフの読み込みに失敗しました: {graph_error}")
            logging.error("知識グラフを構築するには、SKIP_GRAPH_BUILD=falseに設定してください。")
            sys.exit(1)
            
    except Exception as e:
        logging.error(f"❌ 既存の知識グラフの読み込みに失敗しました: {e}")
        logging.error("知識グラフを構築するには、SKIP_GRAPH_BUILD=falseに設定してください。")
        sys.exit(1)
else:
    try:
        logging.info("`./data/api_doc/` からドキュメントを読み込んでいます...")
        documents = SimpleDirectoryReader("./data/api_doc/").load_data()

        logging.info("知識グラフを構築しています... これには時間がかかる場合があります。")
        
        # 1. Markdown対応のNode Parserを初期化
        parser = MarkdownNodeParser()

        # 2. ドキュメントを解析してノード（チャンク）に分割
        nodes = parser.get_nodes_from_documents(documents)

        # 知識抽出には高精度なモデルを使用
        extraction_model = os.getenv("EXTRACTION_LLM_MODEL", "gpt-4.1")
        if not extraction_model:
            logging.error("EXTRACTION_LLM_MODEL環境変数が設定されていません。")
            sys.exit(1)
        extraction_llm = OpenAI(model=extraction_model, temperature=0.1)
        
        # 知識抽出用のカスタムプロンプトを定義
        knowledge_extraction_prompt = """
        与えられたテキストから、APIドキュメントに関連する知識を抽出してください。
        
        抽出する知識は以下の形式で表現してください：
        - エンティティ間の関係は明確で具体的な名前を使用してください
        - 空のリレーション名は使用しないでください
        - リレーション名は英語で記述してください
        
        例：
        - "CreateVariable" HAS_PARAMETER "VariableName"
        - "CreateSketchPlane" RETURNS "SketchPlaneElement"
        - "PartObject" HAS_METHOD "CreateVariable"
        - "String" IS_TYPE_OF "Parameter"
        """
        
        index = KnowledgeGraphIndex(
            nodes, # <--- documentsからnodesに変更
            storage_context=storage_context,
            max_triplets_per_chunk=3,
            llm=extraction_llm,
            show_progress=True,
            include_embeddings=True,
            embed_kg_triplets=True,
            knowledge_extraction_prompt=knowledge_extraction_prompt,
        )
        logging.info("✅ 知識グラフの構築が完了しました。")

    except FileNotFoundError:
        logging.error("❌ ディレクトリ `./data/api_doc/` が見つかりません。作成してドキュメントを追加してください。")
        sys.exit(1)
    except Exception as e:
        logging.error(f"❌ グラフ構築中にエラーが発生しました: {e}")
        logging.error(f"エラーの詳細: {type(e).__name__}")
        if hasattr(e, '__traceback__'):
            import traceback
            logging.error(f"トレースバック: {traceback.format_exc()}")
        sys.exit(1)

# --- 3. クエリエンジンを作成し、LangChainツールとしてラップ ---
logging.info("グラフクエリエンジンを作成しています...")

# SKIP_GRAPH_BUILDがTrueの場合（既存データ使用）は、グラフベースのクエリエンジンを使用
if SKIP_GRAPH_BUILD:
    query_engine = index.as_query_engine(
        include_text=False,  # 既存のグラフデータのみを使用
        response_mode="tree_summarize",
        embedding_mode='hybrid',
        similarity_top_k=5,
    )
else:
    # 新しく構築した場合のクエリエンジン設定
    query_engine = index.as_query_engine(
        include_text=True,
        response_mode="tree_summarize",
        embedding_mode='hybrid',
        similarity_top_k=5,
    )

# descriptionは、エージェントがいつこのツールを使うべきか判断するための重要な指示です。
def query_api_docs(query: str) -> str:
    """APIドキュメントに関する質問に答えるためのツール"""
    try:
        response = query_engine.query(query)
        return str(response)
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"

graph_rag_tool = Tool(
    name="APIDocumentationGraphRAGTool",
    description="APIドキュメントに関する質問に答えるために使用します。特に関数、クラス、パラメータ間の関係性を理解するのに優れています。",
    func=query_api_docs
)

# --- 4. 対話型のLangChainエージェントをセットアップ ---
logging.info("対話メモリを持つLangChainエージェントをセットアップしています...")

# エージェント自体には高速で高性能なモデルを使用
agent_model = os.getenv("AGENT_LLM_MODEL", "gpt-4o")
if not agent_model:
    logging.error("❌ AGENT_LLM_MODEL環境変数が設定されていません。")
    sys.exit(1)
agent_llm = ChatOpenAI(model=agent_model, temperature=0)
tools = [graph_rag_tool]

# システムプロンプトはエージェントへの最も重要な指示書です。
# 役割、能力、期待される振る舞いを日本語で明確に定義します。
system_prompt = """
あなたは専門的な開発者アシスタントです。あなたの主な役割は、非公開APIドキュメントに関する質問に答えることです。
回答を見つけるためには、必ず `APIDocumentationGraphRAGTool` というツールを使用しなければなりません。

### 指示
- 質問に答える前に、ユーザーが何を求めているのか、そしてツールがどのように役立つかを常に考えてください。
- APIの各要素がどのように連携して動作するかについての質問には、このツールが最適です。
- ユーザーが追加の質問をした場合は、会話の履歴を使用して文脈を理解してください。
- ツールを使っても答えが見つからない場合は、その情報がドキュメントに存在しないことを明確に伝えてください。答えを創作してはいけません。
- 回答は簡潔かつ正確にしてください。
- **応答は必ず日本語で行ってください。**
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# エージェントにメモリを追加します。`k=5`は直近5往復の会話を記憶することを意味します。
memory = ConversationBufferWindowMemory(
    memory_key='chat_history',
    k=5,
    return_messages=True
)

agent = create_openai_functions_agent(agent_llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, memory=memory, verbose=True)

# --- 5. 対話ループの開始 ---
logging.info("✅ エージェントの準備が完了しました。対話セッションを開始します。")
print("\n--- APIドキュメントアシスタント ---")
print(f"知識グラフ構築: {'スキップ' if SKIP_GRAPH_BUILD else '実行'}")
print(f"グラフデータクリア: {'実行' if CLEAR_GRAPH_DATA else 'スキップ'}")
print("APIドキュメントに関する質問をどうぞ。「exit」または「終了」と入力するとセッションを終了します。")

while True:
    try:
        user_input = input("\n👤 あなた: ")
        if user_input.lower() in ["exit", "quit", "終了"]:
            print("🤖 アシスタント: ご利用ありがとうございました。")
            break
        
        response = agent_executor.invoke({"input": user_input})
        print(f"🤖 アシスタント: {response['output']}")

    except KeyboardInterrupt:
        print("\n🤖 アシスタント: セッションが中断されました。")
        break
    except Exception as e:
        logging.error(f"予期せぬエラーが発生しました: {e}")
        print("🤖 アシスタント: 申し訳ありません、エラーが発生しました。もう一度お試しください。")