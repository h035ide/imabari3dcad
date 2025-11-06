import sys, os, textwrap, config
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain_neo4j.chains.graph_qa.cypher import GraphCypherQAChain
from langchain_neo4j import Neo4jGraph
from langchain_core.prompts import PromptTemplate

# ---------- 共通 LLM ----------
llm = ChatOpenAI(
    model="gpt-5", 
    temperature=0,
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
    return_source_documents=False, # 回答のみを返すように設定
)

# ---------- Graph QA ----------
graph = Neo4jGraph(
    url=config.NEO4J_URI,
    username=config.NEO4J_USER,
    password=config.NEO4J_PASSWORD,
)

CYPHER_GENERATION_TEMPLATE_JP = """
    あなたは、CADアプリケーション「EvoShip」のAPIに関する知識グラフを熟知したエキスパートです。
    ユーザーの質問を解釈し、提供されたグラフスキーマ情報に基づいて、その答えを見つけるための最適なCypherクエリを生成するタスクを担います。

    ## グラフスキーマ情報
    以下に、利用可能なノードラベル、プロパティ、およびリレーションシップタイプの情報を示します。クエリは**必ずこのスキーマ情報に厳密に従って**生成してください。
    {schema}

    ## クエリ生成の指示
    1.  **思考プロセスに従う:** 以下の思考プロセスに従って、最適なクエリを段階的に構築してください。
        -   **Step 1. 意図の理解:** ユーザーが「何を知りたいのか」「何をしたいのか」という根本的な意図を特定します。(例: APIの使い方を知りたい、サンプルコードが欲しい、概念を理解したい、既存コードを修正したい)
        -   **Step 2. キーワード抽出:** 質問から重要なキーワード（API名、操作対象、目的、修正内容など）を抽出します。
        -   **Step 3. スキーマとのマッピング:** 抽出したキーワードを**上記のグラフスキーマ情報**と照らし合わせます。検索の起点となるノードラベル (`Method`, `ScriptExample`等)、検索対象のプロパティ (`name`, `description`, `summary`等)、たどるべきリレーションシップタイプ (`IS_EXAMPLE_OF`, `HAS_PARAMETER`等) を慎重に選択します。スキーマに存在しない要素は絶対に使用しないでください。
        -   **Step 4. クエリ生成:** 上記の考察に基づき、最終的なCypherクエリを生成します。キーワード検索には `toLower()` と `CONTAINS` を活用し、できるだけ多くの関連情報を取得できるよう努めてください。ヒットしない場合は、検索条件を緩和する（例：ANDをORにする、検索対象プロパティを増やす）ことも検討してください。

    2.  **検索戦略のヒント:**
        -   **「方法」「やり方」** に関する質問には、`Method`ノードの `description` や `ScriptExample`ノードの `summary` を検索するのが有効です。
        -   **「サンプルコード」「実装例」** に関する質問には、`ScriptExample`ノードを起点とし、`IS_EXAMPLE_OF`リレーションで関連する`Method`を探します。`ScriptExample`ノードには`code`プロパティにコード全文が格納されています。
        -   **概念や機能**に関する質問には、`Entity` ノードを検索するのが有効です。
        -   質問に複数のキーワードが含まれる場合、それらが異なるノードのプロパティにマッチする可能性を考慮してください。例えば、「プレートを作成するAPIの引数」という質問では、「プレート」「作成」が`Method`や`ScriptExample`に、「引数」が`Parameter`ノードに関連する可能性があります。

    ## Few-shot Examples (質問とクエリの例)
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

    ## 出力要件
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

QA_TEMPLATE = """
    あなたは、CADアプリケーション「EvoShip」に関するエキスパートアシスタントです。
    あなたのタスクは、ユーザーの要求と、ナレッジグラフ（またはベクトル検索）から取得した情報を基に、最適な回答を生成することです。

    ユーザーの要求:
    {question}

    ナレッジグラフ（またはベクトル検索）から取得した関連情報:
    {context}

    ## 回答生成の要件
    - 取得した情報（{context}）を基に、ユーザーの質問（{question}）に対して**自然な日本語の文章で分かりやすく回答してください。**
    - 取得した情報がCypherクエリの結果（例: `method_name`, `method_description`）である場合は、それを読みやすく整形して文章にまとめてください。
    - 関連情報がない場合、または情報が不十分な場合は、その旨を伝えてください。
    """

QA_PROMPT = PromptTemplate(
input_variables=["context", "question"], template=QA_TEMPLATE
)

graph_qa = GraphCypherQAChain.from_llm(
llm=llm,
graph=graph,
verbose=True,
cypher_prompt=CYPHER_GENERATION_PROMPT,
qa_prompt=QA_PROMPT,
allow_dangerous_requests=True,
top_k=10000,
)

# \---------- ルート選択と実行 ----------

def ask(question: str, route: str = "graph") -> str:
    """
    指定されたルート（検索方法）に基づいて質問に回答します。
    """
    route = route.lower()
    final_question = question

    if route == "graph":
        print("--- [Route: graph] Running Graph Search ---")
        result = graph_qa.invoke({"query": final_question})
        return result['result']

    elif route == "vector":
        print("--- [Route: vector] Running Vector Search ---")
        print("Step 1/2: Retrieving context from vector store...")
        retriever = vectordb.as_retriever()
        docs = retriever.get_relevant_documents(question)

        if docs:
            retrieved_context_str = "\n\n".join([f"--- Document ---\n{doc.page_content}" for doc in docs])
            print("\n--- Retrieved Context ---")
            print(retrieved_context_str)
            print("-------------------------\n")
        else:
            print("No relevant context found in vector store.")

        print("Step 2/2: Generating answer based on context...")
        result = vector_qa.invoke({"query": final_question})
        return result['result']

    elif route == "hybrid":
        print("--- [Route: hybrid] Running Hybrid Search (Vector -> Graph) ---")
        
        print("Step 1/3: Retrieving context from vector store using the question...")
        retriever = vectordb.as_retriever()
        docs = retriever.get_relevant_documents(question)
        
        if docs:
            retrieved_context_str = "\n\n".join([f"--- Document ---\n{doc.page_content}" for doc in docs])
            print("\n--- Retrieved Context for Hybrid Search ---")
            print(retrieved_context_str)
            print("-------------------------------------------\n")
        else:
            print("No relevant context found in vector store.")

        vector_context = "\n\n".join([doc.page_content for doc in docs])
        
        if not vector_context:
            print("Step 2/3: No relevant context found. Using original question for graph search.")
            hybrid_question = final_question
        else:
            print("Step 2/3: Augmenting question with retrieved context.")
            hybrid_question = f"""
以下の【ベクトル検索で得られた関連情報】を最優先の参考情報として活用し、元の質問に答えてください。
この情報は、グラフ検索でどのノードやリレーションシップに着目すべきかの重要なヒントとなります。

## 【ベクトル検索で得られた関連情報】 {vector_context}

【元の質問】
{question}
"""
        print("Step 3/3: Executing graph search with augmented question...")
        result = graph_qa.invoke({"query": hybrid_question})
        return result['result']

    else:
        raise ValueError("route は 'vector', 'graph', 'hybrid' のみ指定できます。")

# \---------- CLI 入口 ----------

if __name__ == "__main__":
    import argparse

    # --- 引数パーサーの設定 ---
    parser = argparse.ArgumentParser(
        description="Ask questions about the EvoShip API.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=textwrap.dedent("""
Usage examples:
  python query1028.py "プレートを作成する方法は？"
  python query1028.py "点群を扱うAPIについて教えて" vector
  python query1028.py "CreatePlate のサンプルコードが見たい" hybrid
""")
    )
    parser.add_argument(
        "question", 
        help="The question to ask in quotes."
    )
    parser.add_argument(
        "route", 
        nargs='?', 
        default="graph", 
        choices=['vector', 'graph', 'hybrid'],
        help="The search route to use. Defaults to 'graph'."
    )
    
    args = parser.parse_args()

    question = args.question
    route = args.route

    # --- 実行 ---
    try:
        answer = ask(question, route)
        print("\n--- Generated Answer ---")
        print(answer)

    except ValueError as e:
        print(f"\nエラー: {e}")
    except Exception as e:
        print(f"\n予期せぬエラーが発生しました: {e}")