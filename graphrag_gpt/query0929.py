"""
使い方:
[モード1: 新規スクリプト生成]
    python query.py "<質問文>" vector     # ベクトル検索で新規作成
    python query.py "<質問文>" hybrid  

[モード2: 既存スクリプト編集]
    python query.py <ファイルパス> "<編集指示>" vector
    python query.py <ファイルパス> "<編集指示>" graph
    python query0929.py ./board.py "板の四隅に直方体の柱を追加してください。" hybrid

[デフォルトの動作]
- ルートを省略した場合は 'graph' が採用されます。
    例: python query.py "<質問文>"
    例: python query.py <ファイルパス> "<編集指示>"
"""
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
あなたは、CADアプリケーション「EvoShip」をPythonで操作するエキスパートです。
あなたのタスクは、ユーザーの要求とナレッジグラフから取得した情報を基に、単一の完成された実行可能なPythonスクリプトと、そのスクリプトに関する説明を生成することです。

ユーザーの要求:
{question}

ナレッジグラフから取得した関連情報:
{context}

上記の情報を基に、以下の要件と出力形式に従って回答を生成してください。

## スクリプト生成の要件
- **ユーザーの要求に「元のスクリプト」が含まれる場合は、それを基に編集・修正を行ってください。**
- **「元のスクリプト」が含まれない場合は、ゼロから新しいスクリプトを作成してください。**
- 新規作成の場合は、常に `import win32com.client` から始めること。
- 新規作成の場合は、アプリケーションを起動する定型コード `evoship = win32com.client.DispatchEx("EvoShip.Application")` を含めること。
- 新規作成の場合は、ドキュメントとパートを作成するコード `doc = evoship.Create3DDocument()` と `part = doc.GetPart()` を含めること。
- メソッドの返り値は、後続のメソッドで利用するために変数に格納すること。
- 複数のAPI呼び出しがある場合、それらを論理的な順序で構成すること。
- 取得した情報から最も適切と考えられる単一のスクリプトを作成すること。
- ナレッジグラフからの情報にサンプルコードが含まれている場合は、それを最優先で参考にし、必要に応じて質問内容に合わせて修正してください。

## 出力形式
以下のマークダウン形式で回答してください。コードや説明以外の余計な文章は含めないでください。

## 生成されたスクリリプト
```python
# ここにPythonスクリプトを記述
````

### スクリプトの説明

ここに、生成したスクリプトが何をするものか、使用されている主要なAPIの目的、そしてユーザーが注意すべき点などを簡潔に解説してください。
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

def ask(question: str, route: str = "graph", original_code: str = None) -> str:
    """
    指定されたルート（検索方法）に基づいて質問に回答します。
    original_codeが指定された場合は、それを編集するタスクとして扱います。
    """
    route = route.lower()

    # LLMに渡す最終的な質問文を組み立てる
    if original_code:
        final_question = f"""
以下の【元のスクリプト】を【編集指示】に従って修正してください。

【元のスクリプト】

```python
{original_code}
```

-----

【編集指示】
{question}
"""
    else:
        # 新規作成モード
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
        
        print("Step 1/3: Retrieving context from vector store using the instruction...")
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
            print("Step 2/3: No relevant context found. Using original instruction for graph search.")
            hybrid_question = final_question
        else:
            print("Step 2/3: Augmenting instruction with retrieved context.")
            if original_code:
                hybrid_question = f"""
以下の【ベクトル検索で得られた関連情報】を最優先の参考情報として活用し、【元のスクリプト】を【編集指示】に従って修正してください。

【元のスクリプト】

```python
{original_code}
```

## 【ベクトル検索で得られた関連情報】 {vector_context}

【編集指示】
{question}
"""
            else:
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
    import re

    # --- 引数パーサーの設定 ---
    parser = argparse.ArgumentParser(
        description="Generate or edit Python scripts for EvoShip based on user instructions.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=textwrap.dedent(__doc__)
    )
    parser.add_argument(
        "first_arg", 
        help="Either a question in quotes (for new scripts) or a file path (for editing)."
    )
    parser.add_argument(
        "instruction", 
        nargs='?', 
        help="The editing instruction in quotes (required in edit mode)."
    )
    parser.add_argument(
        "route", 
        nargs='?', 
        default="graph", 
        choices=['vector', 'graph', 'hybrid'],
        help="The search route to use. Defaults to 'graph'."
    )
    parser.add_argument(
        "-o", "--output", 
        help="The file path to save the generated Python script."
    )
    
    args = parser.parse_args()

    original_code = None
    question = ""
    
    # --- 引数の解析とモード判定 ---
    # [モード2: 編集モード]
    if os.path.exists(args.first_arg):
        if not args.instruction:
            print("エラー: 編集モードでは<ファイルパス>と<編集指示>の両方が必要です。")
            parser.print_help()
            sys.exit(1)
        
        file_path = args.first_arg
        question = args.instruction
        route = args.route
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_code = f.read()
            print(f"--- [Mode: Edit] Loading script from: {file_path} ---")
        except Exception as e:
            print(f"エラー: ファイル '{file_path}' の読み込み中にエラーが発生しました: {e}")
            sys.exit(1)
            
    # [モード1: 新規作成モード]
    else:
        question = args.first_arg
        route = args.instruction if args.instruction in ['vector', 'graph', 'hybrid'] else args.route
        print("--- [Mode: Create New] ---")

    # --- 実行 ---
    try:
        answer = ask(question, route, original_code=original_code)
        
        # --- 出力処理 ---
        if args.output:
            # スクリプト部分を正規表現で抽出
            script_match = re.search(r"```python\n(.*?)```", answer, re.DOTALL)
            if script_match:
                script_code = script_match.group(1).strip()
                
                # スクリプトをファイルに書き込む
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(script_code)
                print(f"\n--- Script saved to: {args.output} ---")

                # 説明部分を抽出して表示
                explanation_match = re.search(r"### スクリプトの説明\n\n(.*)", answer, re.DOTALL)
                if explanation_match:
                    explanation = explanation_match.group(1).strip()
                    print("\n--- Script Explanation ---")
                    print(explanation)
                else:
                    # スクリプト以外の部分を説明として表示
                    remaining_answer = re.sub(r"```python\n(.*?)```", "", answer, flags=re.DOTALL).strip()
                    print("\n--- Answer ---")
                    print(remaining_answer)

            else:
                print("\n--- Generated Answer (script not found) ---")
                print(answer)
        else:
            # 出力ファイルが指定されていない場合は、従来通り全体を出力
            print("\n--- Generated Answer ---")
            print(answer)

    except ValueError as e:
        print(f"\nエラー: {e}")
    except Exception as e:
        print(f"\n予期せぬエラーが発生しました: {e}")
