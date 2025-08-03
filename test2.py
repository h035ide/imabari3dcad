import json
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
from dotenv import load_dotenv


# .envファイルから環境変数を読み込む
load_dotenv()
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# --- 1. JSONファイルの読み込み ---
try:
    with open('api_functions_data.json', 'r', encoding='utf-8') as f:
        functions_data = json.load(f)
except FileNotFoundError:
    print("エラー: api_functions_data.json が見つかりません。")
    exit()

# --- 2. LangChainコンポーネントの準備 ---

# LLMモデルの定義
# 環境変数 OPENAI_API_KEY が自動的に使用されます
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# 出力パーサーの定義（LLMの出力をJSONとして解釈）
parser = JsonOutputParser()

# プロンプトテンプレートの定義
prompt = ChatPromptTemplate.from_messages([
    ("system", "あなたはAPIドキュメントを分析する専門家です。ユーザーの指示に従い、分析結果を必ず指定されたJSON形式で出力してください。"),
    ("human", """
        以下のAPI引数の説明文を分析してください。

        # 説明文
        {description}

        # 抽出する情報
        1. "summary": 説明文を30字以内で簡潔に要約したもの。
        2. "constraints": 説明文に含まれる制約。"[空文字不可]"は"non-empty"、"[空文字可]"は"optional"として配列に格納する。

        # 出力フォーマット
        {format_instructions}
    """)
]).partial(format_instructions=parser.get_format_instructions())


# --- 3. プロンプト、モデル、パーサーをチェーンとして結合 ---
chain = prompt | model | parser

# --- 4. LLM呼び出しとデータ更新のメイン処理 ---
for func in functions_data:
    if "params" not in func:
        continue
    for param in func["params"]:
        print(f"Processing: {func.get('name', 'N/A')} -> {param.get('name', 'N/A')}")
        try:
            # チェーンを実行してLLMからの応答を取得
            llm_result = chain.invoke({"description": param["description_raw"]})
            
            # 結果を中間データに格納
            param["summary_llm"] = llm_result.get("summary")
            param["constraints_llm"] = llm_result.get("constraints", [])

        except OutputParserException as e:
            print(f"  - エラー: LLMの出力がJSON形式ではありませんでした。スキップします。 Error: {e}")
        except Exception as e:
            print(f"  - エラー: LLMの呼び出し中に予期せぬエラーが発生しました。スキップします。 Error: {e}")


# --- 5. 結果を新しいJSONファイルに保存 ---
output_filename = 'api_functions_data_enriched.json'
with open(output_filename, 'w', encoding='utf-8') as f:
    json.dump(functions_data, f, indent=2, ensure_ascii=False)

print("\n--- 処理完了 ---")
print(f"LLMによる情報が付加されたデータが '{output_filename}' に保存されました。")
print("\n最初の関数の最初のパラメータの処理結果:")
print(json.dumps(functions_data[0]['params'][0], indent=2, ensure_ascii=False))