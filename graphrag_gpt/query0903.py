# query.py -----------------------------------------------------------
"""
使い方:
    python query.py "<質問文>"  vector   # ベクトル検索を使う
    python query.py "<質問文>"  graph    # グラフ検索を使う
引数を 1 個しか渡さなかった場合は、既定で 'graph' を採用します。
"""
import sys, textwrap, config
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain_neo4j.chains.graph_qa.cypher import GraphCypherQAChain
from langchain_neo4j import Neo4jGraph
from langchain_core.prompts import PromptTemplate

# ---------- 共通 LLM ----------
llm = ChatOpenAI(
    model="gpt-5", # より安定したモデルを推奨
    temperature=1,
    openai_api_key=config.OPENAI_API_KEY,
)

# ---------- Vector QA ----------
vectordb = Chroma(
    persist_directory="data/chroma_db",
    embedding_function=OpenAIEmbeddings(openai_api_key=config.OPENAI_API_KEY),
)
vector_qa = RetrievalQA.from_llm(
    llm=llm,
    retriever=vectordb.as_retriever(),
)

# ---------- Graph QA ----------
graph = Neo4jGraph(
    url=config.NEO4J_URI,
    username=config.NEO4J_USER,
    password=config.NEO4J_PASSWORD,
)

# ▼▼▼ 変更点: プロンプトを2種類に分離 ▼▼▼

# 1. Cypherクエリ生成に特化したプロンプト
#    役割: ユーザーの質問を分析し、Neo4jから情報を取得するためのCypherクエリだけを生成する。
CYPHER_GENERATION_TEMPLATE_JP = """
タスク: グラフデータベースをクエリするためのCypherステートメントを生成してください。
指示:
- スキーマで提供されているリレーションシップタイプとプロパティのみを使用してください。
- 提供されていない他のリレーションシップタイプやプロパティは使用しないでください。
- ユーザーの質問に含まれるキーワードを、パラメータ（例: $term）を使わずに、Cypherクエリ内に直接埋め込んでください。キーワードは大文字と小文字を区別しないように、`toLower()`関数で囲んでください。
注意:
- 回答に説明や謝罪を含めないでください。
- スキーマに関係のない質問には応答しないでください。

スキーマ:
{schema}

質問: {question}
Cypherクエリ:
"""

CYPHER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["schema", "question"], template=CYPHER_GENERATION_TEMPLATE_JP
)

# 2. 最終的な回答（Pythonコード）生成に特化したプロンプト
#    役割: Cypherの実行結果(context)と元の質問を基に、完全なPythonスクリプトを生成する。
QA_TEMPLATE = """
あなたは、CADアプリケーション「EvoShip」をPythonで操作するエキスパートです。
あなたのタスクは、ユーザーの要求とナレッジグラフから取得した情報を基に、単一の完成された実行可能なPythonスクリプトと、そのスクリプトに関する説明を生成することです。

ユーザーの質問:
{question}

ナレッジグラフから取得した関連情報:
{context}

上記の情報を基に、以下の要件と出力形式に従って回答を生成してください。

## スクリプト生成の要件
- 常に `import win32com.client` から始めること。
- アプリケーションを起動する定型コード `evoship = win32com.client.DispatchEx("EvoShip.Application")` を含めること。
- ドキュメントとパートを作成するコード `doc = evoship.Create3DDocument()` と `part = doc.GetPart()` を含めること。
- メソッドの返り値は、後続のメソッドで利用するために変数に格納すること。
- 複数のAPI呼び出しがある場合、それらを論理的な順序で構成すること。
- 取得した情報から最も適切と考えられる単一のスクリプトを作成すること。

## 出力形式
以下のマークダウン形式で回答してください。コードや説明以外の余計な文章は含めないでください。

## 生成されたスクリプト
```python
# ここにPythonスクリプトを記述
スクリプトの説明
ここに、生成したスクリプトが何をするものか、使用されている主要なAPIの目的、そしてユーザーが注意すべき点などを簡潔に解説してください。

"""

QA_PROMPT = PromptTemplate(
    input_variables=["context", "question"], template=QA_TEMPLATE
)

# GraphCypherQAChainを、2種類のカスタムプロンプトで初期化
graph_qa = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph,
    verbose=True,
    cypher_prompt=CYPHER_GENERATION_PROMPT, # Cypher生成用プロンプト
    qa_prompt=QA_PROMPT,                   # 回答(コード)生成用プロンプト
    allow_dangerous_requests=True,
    top_k=10000,
)
# ▲▲▲ 変更ここまで ▲▲▲

# ---------- ルート選択と実行 ----------
def ask(question: str, route: str = "vector") -> str:
    route = route.lower()
    if route == "graph":
        result = graph_qa.invoke({"query": question})
        return result['result']
    elif route == "vector":
        return vector_qa.run({"query": question}) # .runは将来的に非推奨になるため、.invokeを推奨
    else:
        raise ValueError("route は 'vector' または 'graph' のみ指定できます。")

# ---------- CLI 入口 ----------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(textwrap.dedent(__doc__))
        sys.exit(1)

    question = sys.argv[1]
    route    = sys.argv[2].lower() if len(sys.argv) > 2 else "graph"

    try:
        answer = ask(question, route)
        print(f"[route]  {route}")
        print(f"--- Generated Script ---")
        print(answer)
    except ValueError as e:
        print(e)
    except Exception as e:
        print(f"An error occurred: {e}")