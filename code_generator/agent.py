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
from langchain.output_parsers import PydanticOutputParser

from code_generator.tools import GraphSearchTool, CodeValidationTool, UnitTestTool
from code_generator.schemas import FinalAnswer

# .envファイルを読み込む
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path)

# ロギング設定
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def create_code_generation_agent() -> AgentExecutor:
    """
    自己テスト・自己修正ループと構造化出力を備えたコード生成エージェントを構築します。
    """
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEYが見つかりません。エージェントは構築されませんでした。")
        return None

    logger.info("自己テスト・自己修正機能付きコード生成エージェントを構築しています...")

    tools = [GraphSearchTool(), CodeValidationTool(), UnitTestTool()]
    agent_llm = ChatOpenAI(model="gpt-4o", temperature=0)

    # 1. PydanticOutputParserをセットアップ
    parser = PydanticOutputParser(pydantic_object=FinalAnswer)
    format_instructions = parser.get_format_instructions()

    # 2. 新しい自己修正プロセスと構造化出力を指示するシステムプロンプト
    system_prompt = f"""
あなたは、ユーザーの指示に基づいて高品質なPythonコードを生成する、自己テスト・自己修正能力を持つ高度なAIアシスタントです。

### あなたの役割と目標
最終目標は、ユーザーの要求を、**単体テストで動作が確認された、高品質な**実行可能Pythonコードに変換し、指定されたJSON形式で出力することです。
そのために、あなたは3つの強力なツールを持っています。
1. `hybrid_graph_knowledge_search`: API仕様やコード例をナレッジグラフから検索するツール。
2. `python_code_validator`: Pythonコードの静的解析（lintチェック）を行うツール。
3. `python_unit_test_runner`: Pythonコードとそれに対応する単体テストを実行するツール。

### 実行プロセス（自己テスト・自己修正ループ）
あなたは以下の思考プロセスを厳密に守り、段階的に実行しなければなりません。
1.  **要求の理解と情報検索:** ユーザーの要求を理解し、`hybrid_graph_knowledge_search` ツールを使って関連情報を検索します。
2.  **コード草案の生成:** 検索結果を基に、要求を満たすためのPythonコードの**初稿**を生成します。
3.  **静的検証:** 生成したコード草案に対し、`python_code_validator` ツールを使って自己検証します。もし問題が見つかった場合は、それを修正し、静的検証をパスするまで繰り返します。
4.  **単体テストの生成と実行:** 静的検証をパスしたコードに対し、その動作を検証するための**単体テストコードを自ら生成**してください。
5.  **動的検証と最終修正:** `python_unit_test_runner` ツールを使い、生成したコードとテストコードを実行します。テストが失敗した場合は、そのエラー内容を基にコード草案をデバッグ・修正します。
6.  **最終回答のフォーマット:** 全ての検証をパスした最終的なコードと、それに関する説明を、以下のJSON形式で厳密に出力してください。

{{format_instructions}}
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]).partial(format_instructions=format_instructions)

    memory = ConversationBufferWindowMemory(
        memory_key='chat_history',
        k=5,
        return_messages=True
    )

    agent = create_openai_functions_agent(agent_llm, tools, prompt)

    # create_openai_functions_agentはOutputParserを直接サポートしないため、
    # AgentExecutorの戻り値をパースする後処理を考える必要がある。
    # しかし、Function Callingモードでは、LLMがJSON形式で返すように指示すれば、
    # AgentExecutorの'output'キーにJSON文字列が含まれる可能性が高い。
    # main.py側でその文字列をパースする。

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=10
    )

    logger.info("エージェントの構築が完了しました。")
    return agent_executor

if __name__ == '__main__':
    logger.info("エージェントのテストを開始します。")
    agent_executor = create_code_generation_agent()

    if agent_executor:
        logger.info("エージェントの初期化に成功しました。")
    else:
        logger.error("エージェントを構築できませんでした。環境変数を確認してください。")

    logger.info("エージェントのテストが完了しました。")
