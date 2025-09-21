# mycode/ingest_hybrid.py
"""
This script handles the ingestion process for the hybrid RAG system.
It takes the source documents and indexes them into three different search backends:
1. Dense Vector Store (ChromaDB)
2. Sparse Vector Store (TF-IDF)
3. Full-Text Search Index (Whoosh)
"""
import shutil
import sys
from pathlib import Path

from mycode.chunking import get_api_documents
from mycode.fulltext_search import WhooshSearch
from mycode.sparse_vector_db import SparseVectorSearch

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

# It's better to use a centralized config.
# Assuming a config.py exists at the root as in the original project.
try:
    from graphrag_gpt import config
except ImportError:
    print(
        "Error: config.py not found in graphrag_gpt/. "
        "Make sure it exists in the graphrag_gpt package with your OPENAI_API_KEY."
    )
    sys.exit(1)

# --- Constants ---
CHROMA_PERSIST_DIR = Path("data/chroma_db_hybrid")


def main():
    """
    Main function to run the full ingestion pipeline.
    Supports a --static-only flag to skip steps requiring API calls.
    """
    is_static_only = "--static-only" in sys.argv

    if is_static_only:
        print("🚀 Starting hybrid ingestion process in STATIC-ONLY mode...")
    else:
        print("🚀 Starting hybrid ingestion process...")

    # 1. Get documents from the source
    # Our chunking module prepares the documents from the proprietary format.
    num_steps = 3 if is_static_only else 4
    print(f"\n[1/{num_steps}] Parsing documents from source files...")
    documents = get_api_documents()
    if not documents:
        print("No documents found. Exiting.")
        return
    documents_with_ids = [doc for doc in documents if doc.metadata.get("doc_id")]
    missing_doc_ids = len(documents) - len(documents_with_ids)
    if missing_doc_ids:
        print(
            f"⚠ Warning: Skipping {missing_doc_ids} documents without a 'doc_id' "
            "metadata entry."
        )
    documents = documents_with_ids
    if not documents:
        print("No documents with doc_ids available. Exiting.")
        return

    print(f"✔ Found and parsed {len(documents)} documents with doc_ids.")

    # --- Steps requiring API are conditional ---
    if not is_static_only:
        # --- Set up API keys and embeddings ---
        openai_api_key = getattr(config, "OPENAI_API_KEY", None)
        if not openai_api_key:
            print("Error: OPENAI_API_KEY not found in config.py.")
            sys.exit(1)

        embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

        # 2. Index documents in ChromaDB (Dense Vectors)
        print(f"\n[2/{num_steps}] Indexing in ChromaDB (Dense Vectors)...")
        if CHROMA_PERSIST_DIR.exists():
            print(f"Clearing existing ChromaDB at {CHROMA_PERSIST_DIR}")
            shutil.rmtree(CHROMA_PERSIST_DIR)

        Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory=str(CHROMA_PERSIST_DIR),
            ids=[doc.metadata["doc_id"] for doc in documents],
        )
        print(
            f"✔ ChromaDB created and persisted with {len(documents)} documents at: {CHROMA_PERSIST_DIR}"
        )
    else:
        print(
            "\n[SKIPPED] Indexing in ChromaDB (Dense Vectors) due to --static-only flag."
        )

    # 3. Index documents in Whoosh (Full-Text Search)
    print(
        f"\n[{2 if is_static_only else 3}/{num_steps}] Indexing in Whoosh (Full-Text Search)..."
    )
    whoosh_search = WhooshSearch()
    whoosh_search.index_documents(documents)

    # 4. Index documents in Sparse Vector Store (TF-IDF)
    print(
        f"\n[{3 if is_static_only else 4}/{num_steps}] Indexing in Sparse Vector Store (TF-IDF)..."
    )
    sparse_vector_search = SparseVectorSearch()
    sparse_vector_search.index_documents(documents)

    print("\n🎉 Hybrid ingestion complete!")
    if is_static_only:
        print("Static-only backends (Whoosh, TF-IDF) are ready.")
    else:
        print("All search backends are ready.")


if __name__ == "__main__":
    main()
