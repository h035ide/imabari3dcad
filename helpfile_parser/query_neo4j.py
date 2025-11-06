from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import dataclass

from pathlib import Path
from typing import List, Optional, Sequence

from dotenv import load_dotenv

from llama_index.core.indices.property_graph import PropertyGraphIndex
from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.core.prompts import PromptTemplate
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.schema import MetadataMode, NodeWithScore
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore

from .ingest_neo4j import (
    _configure_logging,
    _ensure_default_embedding,
    _resolve_llm,
    _resolve_neo4j_config,
)


@dataclass(slots=True)
class SourceSummary:
    index: int
    title: Optional[str]
    heading: Optional[str]
    source_path: Optional[str]
    chunk_id: Optional[str]
    score: Optional[float]
    text_preview: str


@dataclass(slots=True)
class QueryExecutionResult:
    user_query: str
    retrieval_query: str
    answer: str
    raw_answer: str
    sources: List[SourceSummary]


def _initialize_reranker(model_name: str, top_n: int) -> Optional[SentenceTransformerRerank]:
    if top_n <= 0:
        return None

    try:
        return SentenceTransformerRerank(model=model_name, top_n=top_n)
    except Exception as exc:  # pragma: no cover - external dependency may fail
        logging.warning("SentenceTransformerリランカーの初期化に失敗しました: %s", exc)
        return None


def _rewrite_query_with_langchain(question: str, model: Optional[str]) -> str:
    if not question.strip():
        return question

    try:
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import ChatOpenAI
    except Exception as exc:  # pragma: no cover - optional dependency path
        logging.debug("LangChainの読み込みに失敗したためクエリリライトをスキップします: %s", exc)
        return question

    try:
        llm = ChatOpenAI(model=model or os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0.0)
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "あなたはEVOSHIPドキュメント検索のためのクエリ最適化アシスタントです。"
                    "ユーザー質問を受け取り、Neo4jグラフから関連情報を引き出すための"
                    "短い検索向けキーワード列を日本語で生成してください。",
                ),
                (
                    "human",
                    "元の質問:\n{question}\n\n"
                    "Neo4j向けに焦点を絞った検索キーワード（40文字以内）を出力してください。",
                ),
            ]
        )
        chain = prompt | llm | StrOutputParser()
        rewritten = chain.invoke({"question": question}).strip()
        if rewritten:
            logging.debug("LangChainがクエリをリライトしました: %s -> %s", question, rewritten)
            return rewritten
    except Exception as exc:  # pragma: no cover - runtime guard
        logging.warning("LangChainによるクエリリライトに失敗しました: %s", exc)

    return question


def _refine_answer_with_langchain(
    *,
    question: str,
    preliminary_answer: str,
    context: str,
    model: Optional[str],
) -> str:
    if not preliminary_answer.strip():
        return preliminary_answer

    try:
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import ChatOpenAI
    except Exception as exc:  # pragma: no cover
        logging.debug("LangChainの読み込みに失敗したため最終整形をスキップします: %s", exc)
        return preliminary_answer

    try:
        llm = ChatOpenAI(model=model or os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0.1)
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "あなたはEVOSHIPヘルプデスクのスペシャリストです。"
                    "提供されたコンテキストに基づいて、ユーザーの質問に答えてください。"
                    "回答は敬体の日本語で、箇条書きで主要ポイントを示し、"
                    "参照番号 [S1] の形式で引用を付けてください。",
                ),
                (
                    "human",
                    "ユーザー質問: {question}\n\n"
                    "候補回答:\n{answer}\n\n"
                    "コンテキスト断片:\n{context}\n\n"
                    "回答には存在しない情報を追加しないでください。",
                ),
            ]
        )
        chain = prompt | llm | StrOutputParser()
        refined = chain.invoke(
            {
                "question": question,
                "answer": preliminary_answer,
                "context": context,
            }
        ).strip()
        if refined:
            return refined
    except Exception as exc:  # pragma: no cover
        logging.warning("LangChainによる回答整形に失敗しました: %s", exc)

    return preliminary_answer


def _render_context_snippets(nodes: Sequence[NodeWithScore], max_chars: int = 360) -> str:
    snippets: List[str] = []
    for idx, item in enumerate(nodes, start=1):
        node = item.node
        metadata = node.metadata or {}
        heading = metadata.get("section_heading") or metadata.get("title") or "(no heading)"
        text = node.get_content(metadata_mode=MetadataMode.NONE).strip()
        snippet = text[:max_chars].replace("\n", " ")
        snippets.append(
            f"[S{idx}] {metadata.get('title', '(no title)')} / {heading}: {snippet}"
        )
    return "\n".join(snippets)


def _summarize_sources(nodes: Sequence[NodeWithScore], limit: int) -> List[SourceSummary]:
    summaries: List[SourceSummary] = []
    for idx, item in enumerate(nodes[:limit], start=1):
        node = item.node
        metadata = node.metadata or {}
        text = node.get_content(metadata_mode=MetadataMode.NONE).strip()
        summaries.append(
            SourceSummary(
                index=idx,
                title=metadata.get("title"),
                heading=metadata.get("section_heading"),
                source_path=metadata.get("source_path"),
                chunk_id=metadata.get("chunk_id") or node.node_id,
                score=item.score,
                text_preview=text[:280].replace("\n", " "),
            )
        )
    return summaries


def execute_graph_query(
    *,
    question: str,
    database: Optional[str],
    llm_model: Optional[str],
    embedding_model: Optional[str],
    langchain_model: Optional[str],
    similarity_top_k: int,
    rerank_model: str,
    rerank_top_n: int,
    max_sources: int,
    skip_langchain: bool,
) -> QueryExecutionResult:
    load_dotenv()
    if embedding_model:
        _ensure_default_embedding(embedding_model)
    else:
        _ensure_default_embedding()

    llm = _resolve_llm(model=llm_model)
    if llm is None:
        logging.warning("OpenAI LLMの初期化に失敗しました。Settings.llmに設定済みのモデルを利用します。")

    uri, user, password, database_name = _resolve_neo4j_config(database)
    graph_store = Neo4jPropertyGraphStore(
        username=user,
        password=password,
        url=uri,
        database=database_name,
    )

    try:
        index = PropertyGraphIndex.from_existing(
            property_graph_store=graph_store,
            llm=llm,
        )

        qa_prompt = PromptTemplate(
            "あなたはEVOSHIPの公式ヘルプから回答を導くアシスタントです。\n"
            "以下のコンテキストのみを用いて質問に答えてください。\n"
            "情報が不足する場合は、無理に推測せず『グラフから回答を特定できません』と返してください。\n"
            "質問: {query_str}\n\n"
            "コンテキスト:\n{context_str}\n\n"
            "丁寧な日本語で簡潔に回答してください。"
        )
        response_synthesizer = get_response_synthesizer(
            llm=llm,
            text_qa_template=qa_prompt,
            response_mode="tree_summarize",
        )

        node_postprocessors = []
        reranker = _initialize_reranker(rerank_model, rerank_top_n)
        if reranker is not None:
            node_postprocessors.append(reranker)

        query_engine = index.as_query_engine(
            llm=llm,
            include_text=True,
            similarity_top_k=similarity_top_k,
            response_synthesizer=response_synthesizer,
            node_postprocessors=node_postprocessors or None,
        )

        retrieval_query = question
        if not skip_langchain:
            rewritten = _rewrite_query_with_langchain(question, langchain_model or llm_model)
            retrieval_query = rewritten or question

        response = query_engine.query(retrieval_query)
        source_nodes = response.source_nodes or []
        sources = _summarize_sources(source_nodes, max_sources)

        raw_answer = str(response).strip()
        final_answer = raw_answer
        if not skip_langchain and source_nodes:
            context_text = _render_context_snippets(source_nodes)
            final_answer = _refine_answer_with_langchain(
                question=question,
                preliminary_answer=raw_answer,
                context=context_text,
                model=langchain_model or llm_model,
            )

        return QueryExecutionResult(
            user_query=question,
            retrieval_query=retrieval_query,
            answer=final_answer,
            raw_answer=raw_answer,
            sources=sources,
        )
    finally:
        graph_store.close()


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Neo4jに格納されたEVOSHIPヘルプグラフをLlamaIndex/LangChainで検索します。",
    )
    parser.add_argument("query", help="ユーザーからの質問文")
    parser.add_argument(
        "--database",
        type=str,
        help="接続するNeo4jデータベース名 (NEO4J_DATABASE を上書き)",
    )
    parser.add_argument(
        "--llm-model",
        type=str,
        help="LlamaIndex用に利用するOpenAIモデル名 (例: gpt-4o-mini)",
    )
    parser.add_argument(
        "--embedding-model",
        type=str,
        help="LlamaIndexのデフォルト埋め込みモデルを上書きします",
    )
    parser.add_argument(
        "--langchain-model",
        type=str,
        help="LangChainによるクエリリライト/回答整形に利用するモデル名",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="初期検索で取得するチャンク数 (default: 10)",
    )
    parser.add_argument(
        "--rerank-top-n",
        type=int,
        default=4,
        help="SentenceTransformerリランカー後に残すチャンク数 (default: 4)",
    )
    parser.add_argument(
        "--rerank-model",
        type=str,
        default="sentence-transformers/all-mpnet-base-v2",
        help="SentenceTransformerリランカーに使用するモデル",
    )
    parser.add_argument(
        "--max-sources",
        type=int,
        default=5,
        help="出力時に表示するソース数 (default: 5)",
    )
    parser.add_argument(
        "--skip-langchain",
        action="store_true",
        help="LangChainによるクエリリライトと回答整形を無効化します",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="結果をJSON形式で出力します",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
        help="ログファイルに出力するレベル (default: INFO)",
    )
    parser.add_argument(
        "--console-level",
        default="WARNING",
        choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
        help="コンソールに出力するログレベル (default: WARNING)",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        help="詳細ログを保存するファイルパス",
    )
    return parser


def _print_text_result(result: QueryExecutionResult) -> None:
    print("=== User Query ===")
    print(result.user_query)
    print()
    print("=== Retrieval Query ===")
    print(result.retrieval_query)
    print()
    print("=== Answer ===")
    print(result.answer)
    if result.answer != result.raw_answer:
        print()
        print("--- LlamaIndex Raw Answer ---")
        print(result.raw_answer)

    if not result.sources:
        print()
        print("(関連ソースが見つかりませんでした)")
        return

    print()
    print("--- Sources ---")
    for summary in result.sources:
        heading = summary.heading or "(no heading)"
        title = summary.title or "(no title)"
        score = f"{summary.score:.3f}" if summary.score is not None else "-"
        print(
            f"[S{summary.index}] {title} > {heading}"
            f" | score={score} | chunk_id={summary.chunk_id}"
        )
        if summary.source_path:
            print(f"        path: {summary.source_path}")
        if summary.text_preview:
            print(f"        text: {summary.text_preview}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    _configure_logging(
        log_level=args.log_level,
        console_level=args.console_level,
        log_file=args.log_file,
    )

    logging.getLogger(__name__).info("Neo4jクエリを実行します。")

    try:
        result = execute_graph_query(
            question=args.query,
            database=args.database,
            llm_model=args.llm_model,
            embedding_model=args.embedding_model,
            langchain_model=args.langchain_model,
            similarity_top_k=args.top_k,
            rerank_model=args.rerank_model,
            rerank_top_n=args.rerank_top_n,
            max_sources=args.max_sources,
            skip_langchain=args.skip_langchain,
        )
    except Exception as exc:
        logging.exception("Neo4jクエリ実行中にエラーが発生しました: %s", exc)
        return 1

    if args.json:
        payload = {
            "user_query": result.user_query,
            "retrieval_query": result.retrieval_query,
            "answer": result.answer,
            "raw_answer": result.raw_answer,
            "sources": [
                {
                    "index": item.index,
                    "title": item.title,
                    "heading": item.heading,
                    "source_path": item.source_path,
                    "chunk_id": item.chunk_id,
                    "score": item.score,
                    "text_preview": item.text_preview,
                }
                for item in result.sources
            ],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        _print_text_result(result)

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
