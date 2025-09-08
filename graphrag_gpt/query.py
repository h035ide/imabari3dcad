# query.py -----------------------------------------------------------
"""
使い方:
    python query.py "<質問文>"  vector   # ベクトル検索を使う
    python query.py "<質問文>"  graph    # グラフ検索を使う
引数を 1 個しか渡さなかった場合は、既定で 'vector' を採用します。
"""
import sys, textwrap, config
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain_neo4j.chains.graph_qa.cypher import GraphCypherQAChain
from langchain_neo4j import Neo4jGraph

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
graph_qa = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph,
    verbose=True,
    # include_raw_results=True,
    # return_intermediate_steps=True,
    top_k=10000,
    allow_dangerous_requests=True,
)

# ---------- ルート選択と実行 ----------
def ask(question: str, route: str = "vector") -> str:
    route = route.lower()
    if route == "graph":
        return graph_qa.run(question)
    elif route == "vector":
        return vector_qa.run(question)
    else:
        raise ValueError("route は 'vector' または 'graph' のみ指定できます。")

# ---------- CLI 入口 ----------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(textwrap.dedent(__doc__))
        sys.exit(1)

    question = sys.argv[1]
    route    = sys.argv[2].lower() if len(sys.argv) > 2 else "vector"

    try:
        answer = ask(question, route)
        print(f"[route]  {route}")
        print(f"[answer] {answer}")
    except ValueError as e:
        print(e)
