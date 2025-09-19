from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from .schemas import ApiBundle, ApiEntry, ReturnSpec, TypeDefinition

from dotenv import load_dotenv

# .envファイルを明示的にロード
load_dotenv()

DEFAULT_MODEL_CONFIG: Dict[str, object] = {
    "model": "gpt-5-mini",
}

PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "You polish EVO.SHIP API metadata. Respond with compact JSON, list only changed fields, "
                "and do not invent values."
            ),
        ),
        (
            "user",
            """
            Current metadata:
            {current_json}

            Documentation excerpt:
            {doc_snippet}

            Update description fields, infer better return type if possible,
            and fill missing parameter descriptions.
            Only include keys you actually change. For params, include only entries
            that require updates with an existing name.
            Output JSON with optional keys: description, returns, params.
            """,
        ),
    ]
)

TYPE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "You revise EVO.SHIP type definitions. Respond with compact JSON, include only modified keys, "
                "and avoid hallucinating values."
            ),
        ),
        (
            "user",
            """
            Current metadata:
            {current_json}

            Definition text:
            {definition_text}

            If the description mixes core meaning with concrete examples, keep the core meaning in description
            and move the examples to an examples array of short strings.
            Only include keys you change (description and/or examples). Return JSON.
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
    # 返り値は raw_return が "なし" などで確定している場合は触らない
    if entry.returns and entry.returns.type in {"不明"} and entry.raw_return:
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
        # 保守的ガード: raw_return が "なし" 等のときは type=void を維持
        raw = (entry.raw_return or "").strip()
        locked_void = raw in {"なし", "None", "void", ""}
        target = entry.returns or ReturnSpec()
        r_type = returns.get("type")
        if isinstance(r_type, str) and r_type and not locked_void:
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
                    # 型上書きは原則禁止（ルール出力優先）。未知型ならば補完を許可
                    inferred_type = update.get("type")
                    if isinstance(inferred_type, str) and inferred_type:
                        if param.type in {"不明", "unknown"}:
                            param.type = inferred_type.strip()
                            param.raw_type = param.raw_type or inferred_type.strip()
                    break


def _apply_type_enrichment(type_def: TypeDefinition, payload: Dict[str, object]) -> bool:
    updated = False
    description = payload.get("description")
    if isinstance(description, str) and description.strip() and description.strip() != type_def.description:
        type_def.description = description.strip()
        updated = True
    examples = payload.get("examples")
    if isinstance(examples, list):
        cleaned = [str(item).strip() for item in examples if str(item).strip()]
        if cleaned and cleaned != type_def.examples:
            type_def.examples = cleaned
            updated = True
    return updated


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
    type_chain = TYPE_PROMPT | llm
    entry_chain = PROMPT | llm

    for type_def in bundle.type_definitions:
        current_json = json.dumps(type_def.to_dict(), ensure_ascii=False)
        try:
            result = type_chain.invoke(
                {
                    "current_json": current_json,
                    "definition_text": type_def.description,
                }
            )
            content = result.content if hasattr(result, "content") else str(result)
            payload = json.loads(content)
            if not isinstance(payload, dict):
                raise ValueError("Type definition payload must be a JSON object")
            if _apply_type_enrichment(type_def, payload):
                audit_log.append({"status": "updated_type", "definition": type_def.name})
        except Exception as exc:  # noqa: BLE001 - bubble up aggregate context
            audit_log.append({"status": "error_type", "definition": type_def.name, "error": str(exc)})

    entries = [entry for entry in bundle.api_entries if _needs_enrichment(entry)]
    for entry in entries:
        current_json = json.dumps(entry.to_dict(), ensure_ascii=False)
        try:
            result = entry_chain.invoke(
                {
                    "current_json": current_json,
                    "doc_snippet": _doc_snippet(entry),
                }
            )
            content = result.content if hasattr(result, "content") else str(result)
            payload = json.loads(content)
            if not isinstance(payload, dict):
                raise ValueError("Entry payload must be a JSON object")
            _apply_enrichment(entry, payload)
            audit_log.append({"status": "updated_entry", "entry": entry.name})
        except Exception as exc:  # noqa: BLE001 - bubble up aggregate context
            audit_log.append({"status": "error_entry", "entry": entry.name, "error": str(exc)})
    return audit_log
