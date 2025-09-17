# mycode/query_hybrid.py
"""
This script is the entry point for querying the Hybrid RAG system.

It initializes all the search backends, combines them using the HybridRetriever,
and then uses a LangChain QA chain to answer a question from the command line.

Usage:
    python mycode/query_hybrid.py "Your question here"
"""
import sys
import textwrap
from pathlib import Path

# Add root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from mycode.hybrid_retriever import HybridRetriever
from mycode.fulltext_search import WhooshSearch
from mycode.sparse_vector_db import SparseVectorSearch

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA

try:
    from graphrag_gpt import config
except ImportError:
    print("Error: config.py not found in graphrag_gpt/. Make sure it exists in the root directory with your OPENAI_API_KEY.")
    sys.exit(1)

# --- Constants ---
CHROMA_PERSIST_DIR = Path("data/chroma_db_hybrid")

def main():
    """
    Sets up the hybrid RAG pipeline and answers a question.
    """
    # --- 1. Get the question from command-line arguments ---
    if len(sys.argv) < 2:
        print(textwrap.dedent(f"""
        Usage:
            python {sys.argv[0]} "Your question here"
        """))
        sys.exit(1)
    question = sys.argv[1]

    print("🚀 Initializing Hybrid RAG System...")

    # --- 2. Initialize all components ---
    openai_api_key = getattr(config, 'OPENAI_API_KEY', None)
    if not openai_api_key:
        print("Error: OPENAI_API_KEY not found in config.py.")
        sys.exit(1)

    # LLM and Embeddings
    llm = ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=openai_api_key)
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

    # Dense Retriever (Chroma)
    if not CHROMA_PERSIST_DIR.exists():
        print(f"Error: ChromaDB not found at {CHROMA_PERSIST_DIR}. Please run ingest_hybrid.py first.")
        sys.exit(1)
    dense_retriever = Chroma(
        persist_directory=str(CHROMA_PERSIST_DIR),
        embedding_function=embeddings
    )

    # Sparse Retriever (TF-IDF)
    sparse_search = SparseVectorSearch()

    # Full-Text Retriever (Whoosh)
    fulltext_search = WhooshSearch()

    print("✔ All search backends initialized.")

    # --- 3. Instantiate the Hybrid Retriever ---
    hybrid_retriever = HybridRetriever(
        dense_retriever=dense_retriever,
        sparse_search=sparse_search,
        fulltext_search=fulltext_search,
        k=15 # Return 15 documents to the LLM
    )
    print("✔ Hybrid Retriever is ready.")

    # --- 4. Create and run the QA chain ---
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=hybrid_retriever
    )

    print("\n🤔 Processing your question...")
    print(f"Question: {question}")

    answer = qa_chain.run(question)

    print("\n✅ Answer:")
    print(textwrap.fill(answer, width=80))


if __name__ == "__main__":
    main()
