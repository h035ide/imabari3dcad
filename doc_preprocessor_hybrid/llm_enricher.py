from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from .schemas import ApiBundle, ApiEntry, ReturnSpec

DEFAULT_MODEL_CONFIG: Dict[str, object] = {
    "model": "gpt-5-mini",
    "temperature": 0.2,
}

PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You polish EVO.SHIP API metadata. Respond with compact JSON and do not invent fields.",
        ),
        (
            "user",
            """
            Current metadata:
            {current_json}

            Documentation excerpt:
            {doc_snippet}

            Update description fields, infer better return type if possible, and fill missing parameter descriptions.
            Output JSON with keys: description, returns, params.
            """,
        ),
    ]
)


def _doc_snippet(entry: ApiEntry) -> str:
    chunks: List[str] = []
    if entry.title_jp:
        chunks.append(f"タイトル: {entry.title_jp}")
    if entry.raw_return:
        chunks.append(f"返り値: {entry.raw_return}")
    for param in entry.params:
        chunks.append(f"引数 {param.name}: {param.description or '説明なし'}")
    return "\n".join(chunks)


def _needs_enrichment(entry: ApiEntry) -> bool:
    if not entry.description:
        return True
    if entry.returns and entry.returns.type in {"不明", "void"} and entry.raw_return:
        return True
    for param in entry.params:
        if not param.description:
            return True
    return False


def _apply_enrichment(entry: ApiEntry, payload: Dict[str, object]) -> None:
    description = payload.get("description")
    if isinstance(description, str) and description:
        entry.description = description.strip()
    returns = payload.get("returns")
    if isinstance(returns, dict):
        target = entry.returns or ReturnSpec()
        r_type = returns.get("type")
        if isinstance(r_type, str) and r_type:
            target.type = r_type.strip()
        r_desc = returns.get("description")
        if isinstance(r_desc, str):
            target.description = r_desc.strip()
        is_array = returns.get("is_array")
        if isinstance(is_array, bool):
            target.is_array = is_array
        entry.returns = target
    params_payload = payload.get("params")
    if isinstance(params_payload, list):
        for update in params_payload:
            if not isinstance(update, dict):
                continue
            name = update.get("name")
            if not isinstance(name, str):
                continue
            for param in entry.params:
                if param.name == name:
                    desc = update.get("description")
                    if isinstance(desc, str) and desc:
                        param.description = desc.strip()
                    inferred_type = update.get("type")
                    if isinstance(inferred_type, str) and inferred_type:
                        param.type = inferred_type.strip()
                        param.raw_type = param.raw_type or inferred_type.strip()
                    break


def enrich_bundle(
    bundle: ApiBundle,
    enabled: bool = True,
    model_config: Optional[Dict[str, object]] = None,
) -> List[Dict[str, object]]:
    """Enrich bundle entries with LLM hints. Returns audit log."""
    audit_log: List[Dict[str, object]] = []
    if not enabled:
        return audit_log

    if not os.getenv("OPENAI_API_KEY"):
        audit_log.append({"status": "skipped", "reason": "missing_openai_api_key"})
        return audit_log

    config = {**DEFAULT_MODEL_CONFIG, **(model_config or {})}
    llm = ChatOpenAI(**config)
    chain = PROMPT | llm

    entries = [entry for entry in bundle.api_entries if _needs_enrichment(entry)]
    for entry in entries:
        current_json = json.dumps(entry.to_dict(), ensure_ascii=False)
        try:
            result = chain.invoke(
                {
                    "current_json": current_json,
                    "doc_snippet": _doc_snippet(entry),
                }
            )
            content = result.content if hasattr(result, "content") else str(result)
            payload = json.loads(content)
            _apply_enrichment(entry, payload)
            audit_log.append({"status": "updated", "entry": entry.name})
        except Exception as exc:  # noqa: BLE001 - bubble up aggregate context
            audit_log.append({"status": "error", "entry": entry.name, "error": str(exc)})
    return audit_log
