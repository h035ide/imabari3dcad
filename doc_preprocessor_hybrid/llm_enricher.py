from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from .schemas import ApiBundle, ApiEntry, ReturnSpec, TypeDefinition

from dotenv import load_dotenv

# load environment variables from .env when present
load_dotenv()

DEFAULT_MODEL_CONFIG: Dict[str, object] = {
    "model": "gpt-5-mini",
}

MAX_ENTRY_SOURCE_CHARS = 1200
MAX_TYPE_SOURCE_CHARS = 800
ENTRY_CONTEXT_WINDOW = 12
TYPE_CONTEXT_WINDOW = 8
MAX_TYPE_CONTEXTS_PER_ENTRY = 4

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

            Parsed summary:
            {doc_snippet}

            api.txt excerpt (rule-based):
            {api_source}

            Relevant type definitions from api_arg.txt:
            {type_context}

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

            Raw excerpt from api_arg.txt:
            {source_excerpt}

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
        chunks.append(f"Title JP: {entry.title_jp}")
    if entry.raw_return:
        chunks.append(f"Raw return: {entry.raw_return}")
    for param in entry.params:
        label = param.type or ""
        chunks.append(
            f"Param {param.name} ({label}): {param.description or 'No description'}"
        )
    return "\n".join(chunks)


def _prepare_lines(text: Optional[str]) -> List[str]:
    if not text:
        return []
    return text.splitlines()


def _truncate_text(value: str, limit: int) -> str:
    value = value.strip()
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def _find_line_index(lines: List[str], targets: List[str]) -> Optional[int]:
    for idx, line in enumerate(lines):
        for target in targets:
            if target and target in line:
                return idx
    return None


def _extract_entry_context(entry: ApiEntry, lines: List[str]) -> str:
    if entry.source and entry.source.text:
        return _truncate_text(entry.source.text, MAX_ENTRY_SOURCE_CHARS)
    if not lines:
        return ""
    targets = [f"{entry.name}("]
    if entry.title_jp:
        targets.append(entry.title_jp)
    idx = _find_line_index(lines, targets)
    if idx is None:
        return ""
    start = max(0, idx - ENTRY_CONTEXT_WINDOW)
    end = min(len(lines), idx + ENTRY_CONTEXT_WINDOW)
    snippet = "\n".join(lines[start:end])
    return _truncate_text(snippet, MAX_ENTRY_SOURCE_CHARS)


def _extract_type_context(type_def: TypeDefinition, lines: List[str]) -> str:
    if type_def.source and type_def.source.text:
        return _truncate_text(type_def.source.text, MAX_TYPE_SOURCE_CHARS)
    if not lines:
        return ""

    base_name = type_def.name
    if "(" in base_name:
        base_name = base_name.split("(")[0].strip()

    targets = [
        f"■{type_def.name}",  # 完全一致
        f"■{base_name}",      # 基本名のみ
    ]

    idx = _find_line_index(lines, targets)
    if idx is None:
        return ""
    start_idx = idx
    end_idx = idx + 1
    line_count = len(lines)
    while start_idx > 0 and lines[start_idx - 1].strip() and not lines[start_idx - 1].startswith("■"):
        start_idx -= 1
    while end_idx < line_count and lines[end_idx].strip() and not lines[end_idx].startswith("■"):
        end_idx += 1
    snippet = "\n".join(lines[max(0, start_idx - TYPE_CONTEXT_WINDOW): min(line_count, end_idx + TYPE_CONTEXT_WINDOW)])
    return _truncate_text(snippet, MAX_TYPE_SOURCE_CHARS)



def _normalise_type_token(raw: str) -> List[str]:
    if not raw:
        return []
    tokens = [raw]
    if raw.endswith("[]"):
        tokens.append(raw[:-2])
    if "(" in raw and raw.endswith(")"):
        base = raw.split("(", 1)[0]
        tokens.append(base)
    return tokens


def _collect_entry_type_context(entry: ApiEntry, context_map: Dict[str, str]) -> str:
    seen: List[str] = []
    snippets: List[str] = []
    for param in entry.params:
        for candidate in _normalise_type_token(param.type):
            # 基本名も試す
            base_candidate = candidate
            if "(" in candidate:
                base_candidate = candidate.split("(")[0].strip()
            
            # 完全一致と基本名の両方を試す
            for search_key in [candidate, base_candidate]:
                if search_key in context_map and search_key not in seen:
                    snippet = context_map[search_key]
                    if snippet:
                        snippets.append(f"Type {search_key}:\n{snippet}")
                        seen.append(search_key)
                        break
            if len(snippets) >= MAX_TYPE_CONTEXTS_PER_ENTRY:
                break
    return "\n\n".join(snippets)


def _needs_enrichment(entry: ApiEntry) -> bool:
    if not entry.description:
        return True
    if entry.returns and not entry.returns.description:
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
        # Keep type=void when raw_return already indicates no value
        raw = (entry.raw_return or "").strip()
        normalized = raw.lower()
        locked_void = raw in {"なし", "�Ȃ�"} or normalized in {"", "none", "void"}
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
                if param.name != name:
                    continue
                desc = update.get("description")
                if isinstance(desc, str) and desc:
                    param.description = desc.strip()
                # Only allow type override when parameter type was unknown
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
    api_doc_text: Optional[str] = None,
    api_arg_text: Optional[str] = None,
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

    api_doc_lines = _prepare_lines(api_doc_text)
    api_arg_lines = _prepare_lines(api_arg_text)

    type_context_map: Dict[str, str] = {}
    for definition in bundle.type_definitions:
        context = ""
        if definition.source and definition.source.text:
            context = _truncate_text(definition.source.text, MAX_TYPE_SOURCE_CHARS)
        elif api_arg_lines:
            context = _extract_type_context(definition, api_arg_lines)
        type_context_map[definition.name] = context
        base_name = definition.name.split('(', 1)[0].strip()
        if base_name and base_name not in type_context_map:
            type_context_map[base_name] = context

    for type_def in bundle.type_definitions:
        current_json = json.dumps(type_def.to_dict(), ensure_ascii=False)
        try:
            result = type_chain.invoke(
                {
                    "current_json": current_json,
                    "definition_text": type_def.description,
                    "source_excerpt": type_context_map.get(type_def.name, ""),
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
            if entry.source and entry.source.text:
                api_source = _truncate_text(entry.source.text, MAX_ENTRY_SOURCE_CHARS)
            else:
                api_source = _extract_entry_context(entry, api_doc_lines)
            type_context = _collect_entry_type_context(entry, type_context_map)
            result = entry_chain.invoke(
                {
                    "current_json": current_json,
                    "doc_snippet": _doc_snippet(entry),
                    "api_source": api_source,
                    "type_context": type_context,
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
