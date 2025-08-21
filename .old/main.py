import os
from dotenv import load_dotenv
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings
)
from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
from llama_index.llms.openai import OpenAI
import tiktoken
# .envファイルから環境変数を読み込む
load_dotenv()

# 🧠 1. LLMの指定 (gpt-4o)
llm = OpenAI(model="gpt-4o", temperature=0.5)
Settings.llm = llm

# 📊 2. コールバックの準備
token_counter = TokenCountingHandler(
    tokenizer=tiktoken.encoding_for_model("gpt-4o-mini").encode
)

callback_manager = CallbackManager([token_counter])
Settings.callback_manager = callback_manager

# 3. データの読み込み
print("ドキュメントを読み込んでいます...")
documents = SimpleDirectoryReader("./data/api_doc").load_data()

# 4. インデックスの構築 (引数からservice_contextを削除)
# Settingsに設定したコールバックが自動で適用されます
print("インデックスを構築しています...")
index = VectorStoreIndex.from_documents(documents)

# インデックス構築時のトークン使用量を表示
print("\n--- インデックス構築時の使用状況 ---")
print(f"Embeddingトークン数: {token_counter.total_embedding_token_count}")
print("--------------------------------\n")

# カウンターをリセット
token_counter.reset_counts()

# 5. クエリエンジンの作成
print("クエリエンジンを作成しています...")
query_engine = index.as_query_engine()

# 6. 問い合わせと応答の取得
print("問い合わせを実行します...")
question = "CreateVariable 関数は何を返しますか？"
response = query_engine.query(question)

# 応答の表示
print("\n--- 応答 ---")
print(f"質問: {question}")
print(f"応答: {response}")
print("------------")

# 7. クエリ実行後のAPI使用状況を表示
print("\n--- クエリ実行時の使用状況 ---")
print(f"LLMプロンプトトークン数: {token_counter.prompt_llm_token_count}")
print(f"LLM応答トークン数: {token_counter.completion_llm_token_count}")
print(f"LLM合計トークン数: {token_counter.total_llm_token_count}")
print("---------------------------\n")