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

from code_generator.tools import GraphSearchTool, CodeValidationTool, UnitTestTool

# .envファイルを読み込む
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path)

# ロギング設定
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def create_code_generation_agent() -> AgentExecutor:
    """
    自己テスト・自己修正ループを備えたコード生成エージェントと実行環境を構築します。
    """
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEYが見つかりません。エージェントは構築されませんでした。")
        return None

    logger.info("自己テスト・自己修正機能付きコード生成エージェントを構築しています...")

    # 1. 利用可能なツールを定義
    tools = [GraphSearchTool(), CodeValidationTool(), UnitTestTool()]

    # 2. LLMを初期化
    agent_llm = ChatOpenAI(model="gpt-4o", temperature=0)

    # 3. 新しい自己テスト・自己修正プロセスを指示するシステムプロンプト
    system_prompt = """
あなたは、ユーザーの指示に基づいて高品質なPythonコードを生成する、自己テスト・自己修正能力を持つ高度なAIアシスタントです。

### あなたの役割と目標
最終目標は、ユーザーの要求を、**単体テストで動作が確認された、高品質な**実行可能Pythonコードに変換することです。
そのために、あなたは3つの強力なツールを持っています。
1. `hybrid_graph_knowledge_search`: API仕様やコード例をナレッジグラフから検索するツール。
2. `python_code_validator`: Pythonコードの静的解析（lintチェック）を行うツール。
3. `python_unit_test_runner`: Pythonコードとそれに対応する単体テストを実行するツール。

### 実行プロセス（自己テスト・自己修正ループ）
あなたは以下の思考プロセスを厳密に守り、段階的に実行しなければなりません。

1.  **要求の理解と情報検索:**
    *   ユーザーの要求を理解し、`hybrid_graph_knowledge_search` ツールを使って関連情報を検索します。

2.  **コード草案の生成:**
    *   検索結果を基に、要求を満たすためのPythonコードの**初稿**を生成します。

3.  **静的検証:**
    *   生成したコード草案に対し、`python_code_validator` ツールを使って自己検証します。
    *   もし問題が見つかった場合は、それを修正したコードを生成し直してください。静的検証をパスするまで、このステップを繰り返します。

4.  **単体テストの生成と実行:**
    *   静的検証をパスしたコードに対し、その動作を検証するための**単体テストコードを自ら生成**してください。テストは`unittest`フレームワークを使い、`source_code`という名前のモジュールからテスト対象をインポートする形式で記述します。
    *   `python_unit_test_runner` ツールを使い、生成したコードとテストコードを実行します。

5.  **動的検証と最終修正:**
    *   単体テストの結果を分析します。
    *   **(a) テスト成功の場合:** コードは高品質で、期待通りに動作すると判断できます。そのコードを最終的な回答として、適切な説明と共にユーザーに提示してください。
    *   **(b) テスト失敗の場合:**
        *   テストの失敗情報（Traceback）を注意深く読み、コードの論理的な問題を特定します。
        *   元の要求、失敗したコード、そしてテストの失敗情報をすべて考慮して、問題を修正した**最終版のコード**を生成します。
        *   この最終版コードをユーザーに提示します。（修正後の再テストは不要です。）

### 注意事項
- この**[検索→草案→静的検証→テスト生成→動的検証→最終化]**というプロセスは、あなたの品質を担保するための最も重要なルールです。
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
        handle_parsing_errors=True,
        max_iterations=10 # ループの上限を設定
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
