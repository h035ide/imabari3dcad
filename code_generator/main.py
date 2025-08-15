import os
import sys
import logging
import json
from pydantic import ValidationError

# --- [Path Setup] ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- [End Path Setup] ---

from dotenv import load_dotenv
from code_generator.agent import create_code_generation_agent
from code_generator.schemas import FinalAnswer

# .envファイルを読み込む
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path)

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    アプリケーションのメインエントリーポイント。
    コード生成エージェントを初期化し、対話ループを開始します。
    """
    logger.info("アプリケーションを起動しています...")

    agent_executor = create_code_generation_agent()

    if not agent_executor:
        logger.error("エージェントの初期化に失敗しました。")
        logger.error("環境変数（特にOPENAI_API_KEY）が正しく設定されているか確認してください。")
        sys.exit(1)

    print("\n--- AIコード生成アシスタント ---")
    print("AIアシスタントが起動しました。")

    # ツールが設定されているかチェック（LlamaIndexHybridSearchToolの場合のみ）
    search_tool = None
    try:
        # RunnableWithMessageHistoryからAgentExecutorを取得
        if hasattr(agent_executor, 'runnable'):
            tools = agent_executor.runnable.tools
        else:
            tools = agent_executor.tools
            
        for tool in tools:
            if hasattr(tool, '_is_configured'):
                search_tool = tool
                break
    except AttributeError:
        logger.warning("ツール情報にアクセスできません。")
    
    if search_tool and not search_tool._is_configured:
        logger.warning("検索ツールが設定されていません。ナレッジグラフ検索は機能しません。")
    elif search_tool:
        logger.info("検索ツールが正常に設定されています。")
    else:
        logger.info("ツールが正常に設定されています。")

    print("コード生成の要求を日本語で入力してください。（'exit'または'終了'または'q'で終了します）")

    # 対話ループ
    while True:
        try:
            user_input = input("\n👤 あなた: ")
            if user_input.lower() in ["exit", "q", "終了"]:
                print("🤖 アシスタント: ご利用ありがとうございました。")
                break

            response = agent_executor.invoke(
                {"input": user_input}, 
                {"configurable": {"session_id": "default_session"}}
            )
            output = response.get("output", "")

            # --- [構造化出力のパース処理] ---
            try:
                # LLMからの出力がJSON形式の文字列であると仮定してパース
                parsed_output = json.loads(output)
                # Pydanticモデルでバリデーション
                final_answer = FinalAnswer(**parsed_output)
                # 整形して表示
                print(f"🤖 アシスタント:\n{final_answer.to_string()}")
            except (json.JSONDecodeError, ValidationError, TypeError):
                # パースに失敗した場合は、生の出力をそのまま表示
                logger.warning("出力のJSONパースに失敗しました。生のテキストとして表示します。")
                print(f"🤖 アシスタント: {output}")
            # --- [ここまで] ---

        except KeyboardInterrupt:
            print("\n🤖 アシスタント: セッションが中断されました。")
            break
        except Exception as e:
            logger.error(f"対話ループ中に予期せぬエラーが発生しました: {e}", exc_info=True)
            print("🤖 アシスタント: 申し訳ありません、エラーが発生しました。")

if __name__ == "__main__":
    main()
