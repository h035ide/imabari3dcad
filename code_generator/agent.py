import os
import sys
import logging

# --- [Path Setup] ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- [End Path Setup] ---

from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferWindowMemory

from code_generator.tools import GraphSearchTool

# .envファイルを読み込む
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path)

# ロギング設定
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def create_code_generation_agent() -> AgentExecutor:
    """
    コード生成のためのLangChainエージェントと実行環境を構築します。
    """
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEYが見つかりません。エージェントは構築されませんでした。")
        return None

    logger.info("コード生成エージェントを構築しています...")
    tools = [GraphSearchTool()]
    agent_llm = ChatOpenAI(model="gpt-4o", temperature=0)
    system_prompt = """
あなたは、ユーザーの指示に基づいて高品質なPythonコードを生成する専門家AIアシスタントです。
### あなたの役割と目標
あなたの最終目標は、ユーザーの自然言語による要求を、実行可能なPythonコードに変換することです。
そのために、あなたは `graph_knowledge_search` という強力なツールを持っています。このツールは、システムのAPI仕様やコード例が格納されたナレッジグラフにアクセスできます。
### 実行プロセス
1. **要求の理解:** まず、ユーザーがどのような機能を持つコードを求めているのかを正確に理解します。
2. **ツールによる情報検索:** 次に、必ず `graph_knowledge_search` ツールを使って、要求に最も関連するAPI関数、クラス、パラメータ、コード例をナレッジグラフから検索します。
3. **情報の統合と分析:** ツールから得られた検索結果（APIの仕様、関数のシグネチャ、実装コード片など）を注意深く分析し、コード生成に必要な情報をすべて整理します。
4. **コードの生成:** 整理した情報に基づいて、最終的なPythonコードを生成します。
5. **回答の提示:** 生成したコードを、適切な説明と共にユーザーに提示します。
### 注意事項
- **ツールの使用は必須です。** 自身の知識だけで回答を創作せず、必ずツールで得た情報に基づいてください。
- ツールから有益な情報が得られなかった場合は、その旨を正直に伝え、「関連情報が見つかりませんでした。」と回答してください。
- **応答は必ず日本語で行ってください。**
"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    memory = ConversationBufferWindowMemory(
        memory_key='chat_history',
        k=5,
        return_messages=True
    )
    agent = create_openai_functions_agent(agent_llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        handle_parsing_errors=True
    )
    logger.info("エージェントの構築が完了しました。")
    return agent_executor

if __name__ == '__main__':
    logger.info("エージェントのテストを開始します。")
    agent_executor = create_code_generation_agent()

    if agent_executor:
        logger.info("対話を開始します。（'exit'または'終了'で終了）")
        if not agent_executor.tools[0]._is_configured:
            logger.warning("GraphSearchToolが設定されていません。API検索は機能しませんが、エージェントの対話テストは可能です。")
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
                logger.error(f"予期せぬエラーが発生しました: {e}", exc_info=True)
                print("🤖 アシスタント: 申し訳ありません、エラーが発生しました。")
    else:
        logger.error("エージェントを構築できませんでした。環境変数を確認してください。")

    logger.info("エージェントのテストが完了しました。")
