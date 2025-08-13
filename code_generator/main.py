import os
import sys
import logging

# --- [Path Setup] ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- [End Path Setup] ---

from dotenv import load_dotenv
from code_generator.agent import create_code_generation_agent

# .envファイルをアプリケーションのエントリーポイントで一度だけ読み込む
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

    if not agent_executor.tools[0]._is_configured:
        logger.warning("GraphSearchToolが設定されていません。ナレッジグラフ検索は機能しません。")

    print("コード生成の要求を日本語で入力してください。（'exit'または'終了'で終了します）")

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
            logger.error(f"対話ループ中に予期せぬエラーが発生しました: {e}", exc_info=True)
            print("🤖 アシスタント: 申し訳ありません、エラーが発生しました。もう一度お試しください。")

if __name__ == "__main__":
    main()
