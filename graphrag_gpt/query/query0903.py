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
    model="gpt-5", 
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

CYPHER_GENERATION_TEMPLATE_JP = """
あなたは、CADアプリケーション「EvoShip」のAPIに関する知識グラフを熟知したエキスパートです。ユーザーの質問を解釈し、その答えを見つけるための最適なCypherクエリを生成するタスクを担います。

## 指示
1.  **思考プロセスに従う:** 以下の思考プロセスに従って、最適なクエリを段階的に構築してください。
    -   **Step 1. 意図の理解:** ユーザーが「何を知りたいのか」「何をしたいのか」という根本的な意図を特定します。 (例: APIの使い方を知りたい、サンプルコードが欲しい、概念を理解したい)
    -   **Step 2. キーワード抽出:** 質問から重要なキーワード（API名、操作対象、目的など）を抽出します。
    -   **Step 3. ノードとリレーションの選択:** 抽出したキーワードとスキーマを基に、検索の起点となるノードタイプ (`Method`, `ScriptExample`, `Entity`等) と、たどるべきリレーション (`IS_EXAMPLE_OF`, `HAS_PARAMETER`, `CALLS`等) を選択します。
    -   **Step 4. クエリ生成:** 上記の考察に基づき、最終的なCypherクエリを生成します。

2.  **検索戦略のヒント:**
    -   **「方法」「やり方」** に関する質問には、`Method`ノードの `description` プロパティや、`ScriptExample`ノードの `summary` プロパティを検索するのが有効です。
    -   **「サンプルコード」「実装例」** に関する質問には、`ScriptExample`ノードを検索し、`IS_EXAMPLE_OF`リレーションで関連する`Method`を探します。`ScriptExample`ノードには`code`プロパティにコード全文が格納されています。
    -   **概念や機能**に関する質問には、HTMLから抽出した `Entity` ノードを検索するのが有効です。
    -   キーワード検索の際は、大文字と小文字を区別しないように `toLower()` 関数を使用してください。

3.  **スキーマ:**
    {schema}

4.  **Few-shot Examples (質問とクエリの例):**
    -   **質問:** 「プレートを作成するサンプルコードはありますか？」
    -   **Cypherクエリ:**
        ```cypher
        MATCH (s:ScriptExample)-[:IS_EXAMPLE_OF]->(m:Method)
        WHERE (toLower(s.summary) CONTAINS 'プレート' AND toLower(s.summary) CONTAINS '作成')
           OR (toLower(m.description) CONTAINS 'プレート' AND toLower(m.description) CONTAINS '作成')
        RETURN s.name AS script_name, s.code AS script_code, s.summary AS script_summary
        ```
    -   **質問:** 「点群を扱うAPIには何がありますか？」
    -   **Cypherクエリ:**
        ```cypher
        MATCH (m:Method)-[:HAS_PARAMETER|HAS_RETURNS]->(:Parameter|ReturnValue)-[:HAS_TYPE]->(t:DataType)
        WHERE toLower(t.name) CONTAINS '点'
        RETURN DISTINCT m.name AS method_name, m.description AS method_description
        ```

 5.**出力:**
    -   生成されたCypherクエリのみを、` ```cypher ... ``` ` のようなコードブロックなしで、**文字列としてそのまま出力してください。**
    -   説明、前置き、括弧、謝罪は一切含めないでください。
    -   **クエリは必ず `MATCH` や `RETURN` などのキーワードから開始してください。**
---
**質問:** {question}
**Cypherクエリ:**
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
- ナレッジグラフからの情報にサンプルコードが含まれている場合は、それを最優先で参考にし、必要に応じて質問内容に合わせて修正してください。

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
        return vector_qa.invoke({"query": question})
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