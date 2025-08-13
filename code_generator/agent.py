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

from code_generator.tools import GraphSearchTool, CodeValidationTool, UnitTestTool, ParameterExtractionTool
from code_generator.schemas import FinalAnswer

# .envファイルを読み込む
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path)

# ロギング設定
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def create_code_generation_agent() -> AgentExecutor:
    """
    Pre-flight Validationと自己修正ループを備えたコード生成エージェントを構築します。
    """
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEYが見つかりません。エージェントは構築されませんでした。")
        return None

    logger.info("Pre-flight Validation機能付きエージェントを構築しています...")

    # 1. 利用可能なツールを定義
    tools = [ParameterExtractionTool(), GraphSearchTool(), CodeValidationTool(), UnitTestTool()]

    # 2. LLMを初期化
    agent_llm = ChatOpenAI(model="gpt-4o", temperature=0)

    # 3. PydanticOutputParserをセットアップ
    parser = PydanticOutputParser(pydantic_object=FinalAnswer)
    format_instructions = parser.get_format_instructions()

    # 4. 新しい思考プロセスを指示するシステムプロンプト
    system_prompt = f"""
あなたは、ユーザーの指示に基づいて高品質なPythonコードを生成する、自己テスト・自己修正能力を持つ高度なAIアシスタントです。

### あなたの役割と目標
最終目標は、ユーザーの要求を、**単体テストで動作が確認された、高品質な**実行可能Pythonコードに変換し、指定されたJSON形式で出力することです。
あなたは4つの強力なツールを持っています: `user_query_parameter_extractor`, `hybrid_graph_knowledge_search`, `python_code_validator`, `python_unit_test_runner`。

### 実行プロセス
あなたは以下の思考プロセスを厳密に守り、段階的に実行しなければなりません。

**フェーズ1：要求の検証と情報収集（Pre-flight Validation）**

1.  **入力分析:** まず、`user_query_parameter_extractor`ツールを使い、ユーザーの最初の要求から「意図」と「パラメータ」を抽出します。
2.  **API発見:** `hybrid_graph_knowledge_search`ツールを使い、抽出した「意図」に最も関連性の高いAPIを検索します。
3.  **曖昧さの解消:**
    *   ツールの結果が `AMBIGUOUS_RESULTS::` で始まる場合、それは複数の有力な候補が見つかったことを意味します。その場合、**コード生成に進まず、まずユーザーに質問してください。**
    *   候補のリストをユーザーに提示し、「どちらのAPIを使用しますか？」のように明確な選択を求めてください。ユーザーからの回答を次のステップの入力とします。
4.  **情報検証と比較:** 発見した（またはユーザーが選択した）APIが必要とするパラメータと、ユーザーが提供したパラメータを比較します。
5.  **対話による情報補完:**
    *   もしAPIが必要とするパラメータがユーザーの要求に不足している場合、**コード生成に進まず、まずユーザーに質問してください。**（例：「キューブを作成するには辺の長さが必要です。数値を指定してください。」）
    *   ユーザーからの回答を待ち、すべての必須パラメータが揃うまで対話を続けてください。

**フェーズ2：コード生成と自己修正**

5.  **最小コンテキストの構築:** 全ての必須パラメータが揃ったら、コード生成のためだけの最小限のコンテキスト（APIのシグネチャ、確定したパラメータ値など）を内部で整理します。
6.  **コード草案の生成:** 整理したコンテキストを基に、Pythonコードの**初稿**を生成します。
7.  **静的検証:** 生成したコードを`python_code_validator`ツールで検証します。問題があれば修正します。
8.  **単体テストの生成と実行:** 静的検証をパスしたコードに対し、その動作を検証するための**単体テストコードを自ら生成**してください。
9.  **動的検証と最終修正:** `python_unit_test_runner` ツールを使い、生成したコードとテストコードを実行します。テストが失敗した場合、そのエラーを基にコードをデバッグし、最終版のコードを生成します。

**フェーズ3：最終出力**

10. **最終回答のフォーマット:** 全ての検証をパスした最終的なコードと、それに関する説明を、以下のJSON形式で厳密に出力してください。

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

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=15 # ステップが増えたため上限を少し増やす
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
