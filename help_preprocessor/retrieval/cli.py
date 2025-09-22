"""Command line interface for help retrieval system."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

from .langchain_integration import create_help_langchain_system
from .llamaindex_integration import create_help_llamaindex_system


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for retrieval CLI."""
    parser = argparse.ArgumentParser(description="Help system retrieval interface")
    
    # System selection
    parser.add_argument(
        "--system",
        choices=["langchain", "llamaindex", "hybrid"],
        default="hybrid",
        help="Retrieval system to use"
    )
    
    # Query options
    parser.add_argument(
        "--query", "-q",
        required=True,
        help="Search query"
    )
    
    parser.add_argument(
        "--top-k", "-k",
        type=int,
        default=5,
        help="Number of results to return"
    )
    
    parser.add_argument(
        "--search-types",
        nargs="+",
        choices=["dense", "sparse", "fulltext", "graph"],
        help="Search types to use (default: all)"
    )
    
    parser.add_argument(
        "--fusion-method",
        choices=["rrf", "weighted", "borda", "adaptive"],
        default="adaptive",
        help="Result fusion method"
    )
    
    # Configuration
    parser.add_argument(
        "--config",
        type=Path,
        help="Configuration file path"
    )
    
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Data directory path"
    )
    
    # Output options
    parser.add_argument(
        "--output-format",
        choices=["json", "text", "detailed"],
        default="text",
        help="Output format"
    )
    
    parser.add_argument(
        "--output-file",
        type=Path,
        help="Output file path"
    )
    
    # Mode selection
    parser.add_argument(
        "--mode",
        choices=["search", "rag", "chat"],
        default="search",
        help="Operation mode"
    )
    
    # Interactive mode
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Interactive chat mode"
    )
    
    return parser


def execute_search(system: Dict[str, Any], query: str, args: argparse.Namespace) -> Dict[str, Any]:
    """Execute search using hybrid retriever."""
    from .base import QueryContext
    
    hybrid_retriever = system["hybrid_retriever"]
    
    context = QueryContext(
        query=query,
        top_k=args.top_k,
        search_types=args.search_types,
        fusion_method=args.fusion_method
    )
    
    results = hybrid_retriever.search(context)
    
    return {
        "query": query,
        "results": [
            {
                "id": r.id,
                "content": r.content,
                "score": r.score,
                "source": r.source,
                "metadata": r.metadata
            }
            for r in results
        ],
        "total_results": len(results),
        "method": "hybrid_search"
    }


def execute_rag(system: Dict[str, Any], query: str, args: argparse.Namespace) -> Dict[str, Any]:
    """Execute RAG query."""
    if "rag_chain" in system:
        # LangChain RAG
        rag_chain = system["rag_chain"]
        return rag_chain.query(query)
    elif "query_engine" in system:
        # LlamaIndex RAG
        query_engine = system["query_engine"]
        return query_engine.query(query)
    else:
        raise ValueError("RAG system not available")


def execute_chat(system: Dict[str, Any], message: str, args: argparse.Namespace) -> Dict[str, Any]:
    """Execute chat query."""
    if "conversational_chain" in system:
        # LangChain chat
        chat_chain = system["conversational_chain"]
        return chat_chain.chat(message)
    elif "chat_engine" in system:
        # LlamaIndex chat
        chat_engine = system["chat_engine"]
        return chat_engine.chat(message)
    else:
        raise ValueError("Chat system not available")


def format_output(result: Dict[str, Any], format_type: str) -> str:
    """Format output based on specified format."""
    if format_type == "json":
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    elif format_type == "detailed":
        output_lines = []
        
        # Query info
        if "query" in result:
            output_lines.append(f"Query: {result['query']}")
            output_lines.append("-" * 50)
        
        # Answer (for RAG/chat modes)
        if "answer" in result:
            output_lines.append(f"Answer: {result['answer']}")
            output_lines.append("")
        
        # Results
        if "results" in result:
            output_lines.append(f"Found {result.get('total_results', 0)} results:")
            output_lines.append("")
            
            for i, res in enumerate(result["results"], 1):
                output_lines.append(f"{i}. [{res['source']}] Score: {res['score']:.3f}")
                output_lines.append(f"   ID: {res['id']}")
                output_lines.append(f"   Content: {res['content'][:200]}...")
                if res.get('metadata', {}).get('title'):
                    output_lines.append(f"   Title: {res['metadata']['title']}")
                output_lines.append("")
        
        # Source documents (for RAG/chat modes)
        if "source_documents" in result:
            output_lines.append("Source Documents:")
            for i, doc in enumerate(result["source_documents"], 1):
                output_lines.append(f"{i}. {doc['content'][:200]}...")
                output_lines.append("")
        
        return "\n".join(output_lines)
    
    else:  # text format
        if "answer" in result:
            return result["answer"]
        elif "results" in result and result["results"]:
            return result["results"][0]["content"]
        else:
            return "No results found."


def interactive_chat(system: Dict[str, Any], args: argparse.Namespace):
    """Interactive chat mode."""
    print("Help System Interactive Chat")
    print("Type 'quit' or 'exit' to stop, 'clear' to clear memory")
    print("-" * 40)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ["quit", "exit"]:
                break
            elif user_input.lower() == "clear":
                # Clear memory if available
                if "conversational_chain" in system:
                    system["conversational_chain"].clear_memory()
                elif "chat_engine" in system:
                    system["chat_engine"].reset()
                print("Memory cleared.")
                continue
            elif not user_input:
                continue
            
            # Execute chat
            result = execute_chat(system, user_input, args)
            
            # Format and display response
            response = format_output(result, "text")
            print(f"\nAssistant: {response}")
            
            # Show sources in detailed mode
            if args.output_format == "detailed":
                if "source_documents" in result:
                    print("\nSources:")
                    for i, doc in enumerate(result["source_documents"][:3], 1):
                        title = doc.get("metadata", {}).get("title", "Unknown")
                        print(f"  {i}. {title}")
                        
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as exc:
            print(f"Error: {exc}")


def main(argv=None):
    """Main CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)
    
    try:
        # Create system based on selection
        config_overrides = {
            "data_dir": str(args.data_dir),
            "fusion_method": args.fusion_method
        }
        
        if args.system == "langchain":
            system = create_help_langchain_system(args.config, **config_overrides)
        elif args.system == "llamaindex":
            system = create_help_llamaindex_system(args.config, **config_overrides)
        else:  # hybrid
            # Use LangChain as default for hybrid mode
            system = create_help_langchain_system(args.config, **config_overrides)
        
        # Interactive mode
        if args.interactive:
            interactive_chat(system, args)
            return
        
        # Execute based on mode
        if args.mode == "search":
            result = execute_search(system, args.query, args)
        elif args.mode == "rag":
            result = execute_rag(system, args.query, args)
        elif args.mode == "chat":
            result = execute_chat(system, args.query, args)
        else:
            raise ValueError(f"Unknown mode: {args.mode}")
        
        # Format output
        output = format_output(result, args.output_format)
        
        # Write output
        if args.output_file:
            args.output_file.write_text(output, encoding="utf-8")
            print(f"Results written to {args.output_file}")
        else:
            print(output)
            
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
