"""LLMベースのAPI抽出パイプライン骨子。

現時点ではモックチェーンを返すスタブ実装のみを提供する。今後、LangChainや
LlamaIndexのコンポーネントを組み合わせ、チャンク生成→LLM呼び出し→構造化
整形を段階的に追加する。
"""

from __future__ import annotations

import json

import logging

from dataclasses import dataclass
from typing import Iterable, List, Optional, Set

from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import TextNode
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.base import Runnable
from langchain_openai import ChatOpenAI

from .models import (
    ApiEntry,
    ApiExtractionResult,
    ArrayInfo,
    ParameterDefinition,
    PropertyDefinition,
    ReturnDefinition,
    TypeDefinition,
)
from .type_parser import parse_type_definitions
from .type_registry import TypeRegistry


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class LLMExtractionConfig:
    """LLM抽出設定値。

    本設定は今後、チャンクサイズや並列度、モデル名などをパラメータ化する際に
    拡張する。暫定で `model` のみを保持し、デフォルト値を指定する。
    """

    model: str = "gpt-4.1-mini"
    chunk_size: int = 512
    chunk_overlap: int = 64
    temperature: float = 0.0
    max_retries: int = 2
    request_timeout: int = 180
    response_format: str = "json_object"


class LLMApiExtractor:
    """LLM駆動のAPI抽出器。

    現時点では未実装のメソッドが多く、既存コードへの置き換えに備えた雛形
    として提供する。`extract` は後続ステップでチャンク処理やLangChainチェーンを
    呼び出すよう更新する。
    """

    def __init__(
        self,
        type_definitions: Iterable[TypeDefinition],
        config: LLMExtractionConfig | None = None,
        llm: Optional[Runnable] = None,
    ):
        self.type_definitions = list(type_definitions)
        self.config = config or LLMExtractionConfig()
        self.type_registry = TypeRegistry(self.type_definitions)
        self._splitter = SentenceSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
        )
        self._last_chunks: List[TextNode] = []
        self._llm_override: Optional[Runnable] = llm
        self._llm_cached: Optional[Runnable] = None
        self._prompt: ChatPromptTemplate | None = None
        logger.debug(
            "Initialized LLMApiExtractor with %d type definitions (model=%s)",
            len(self.type_definitions),
            self.config.model,
        )

    def extract(self, api_text: str) -> List[ApiEntry]:
        """LLMを利用してAPIテキストから構造化情報を抽出する。

        TODO: LangChainのStructured Output機能やLlamaIndexのRetrieverを用いた
        実装に置き換える。現時点では既存正規表現実装と同等の処理が未実装のため
        空リストを返す仮実装とする。
        """

        self._last_chunks = self._chunk_api_text(api_text)
        prompt = self._get_prompt()
        llm = self._get_llm()
        runnable = prompt | llm
        entries: List[ApiEntry] = []
        seen_ids: Set[str] = set()
        total_chunks = len(self._last_chunks)
        logger.debug("Processing %d chunks for LLM extraction", total_chunks)
        for idx, chunk in enumerate(self._last_chunks, start=1):
            payload = {
                "chunk_text": chunk.get_content(),
                "chunk_metadata": chunk.metadata or {},
            }
            logger.debug(
                "Invoking LLM for chunk %d/%d (len=%d)",
                idx,
                total_chunks,
                len(payload["chunk_text"]),
            )
            try:
                raw = runnable.invoke(payload)
            except Exception:
                logger.exception("LLM invocation failed for chunk %d", idx)
                continue
            parsed_entries = self._parse_llm_response(raw)
            logger.debug(
                "Chunk %d/%d produced %d entries",
                idx,
                total_chunks,
                len(parsed_entries),
            )
            for entry in parsed_entries:
                key = f"{entry.entry_type}:{entry.name}"
                if key in seen_ids:
                    continue
                seen_ids.add(key)
                entries.append(entry)
        logger.info("LLM extraction completed with %d unique entries", len(entries))
        return entries

    def _chunk_api_text(self, api_text: str) -> List[TextNode]:
        """`api.txt` のコンテンツをチャンク化してノード列として返す。"""

        document = Document(text=api_text, metadata={"source": "api.txt"})
        nodes = self._splitter.get_nodes_from_documents(
            [document],
            show_progress=False,
        )
        logger.debug(
            "Chunked API text into %d nodes (chunk_size=%d, overlap=%d)",
            len(nodes),
            self.config.chunk_size,
            self.config.chunk_overlap,
        )
        return nodes

    def _get_llm(self) -> Runnable:
        if self._llm_override is not None:
            return self._llm_override
        if self._llm_cached is None:
            self._llm_cached = ChatOpenAI(
                model=self.config.model,
                temperature=self.config.temperature,
                max_retries=self.config.max_retries,
                timeout=self.config.request_timeout,
                response_format={"type": self.config.response_format},
            )
        return self._llm_cached

    def _get_prompt(self) -> ChatPromptTemplate:
        if self._prompt is None:
            self._prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """あなたはCADソフトのAPI仕様（日本語）から構造化データを抽出するエキスパートです。
                        入力されたチャンクの中に記載されている関数／オブジェクトを過不足なくJSONで出力してください。
                        未記載の情報は null にし、推測は禁止です。""",
                    ),
                    (
                        "human",
                        """以下のテキストから抽出してください。

                        ---
                        {chunk_text}
                        ---

                        返却形式は `entries` 配列を持つJSONです。""",
                    ),
                ]
            )
        return self._prompt

    def _parse_llm_response(self, raw_response: dict) -> List[ApiEntry]:
        data = self._normalize_llm_response(raw_response)
        if not isinstance(data, dict):
            logger.debug(
                "LLM response could not be normalized into dict: %s", type(raw_response)
            )
            return []
        entries_payload = data.get("entries")
        if not isinstance(entries_payload, list):
            logger.debug(
                "LLM response missing 'entries' list: keys=%s", list(data.keys())
            )
            return []
        results: List[ApiEntry] = []
        for item in entries_payload:
            entry = self._build_entry_from_payload(item)
            if entry:
                results.append(entry)
            else:
                logger.debug("Skipping invalid entry payload: %s", item)
        logger.debug("Parsed %d entries from LLM response", len(results))
        return results

    def _normalize_llm_response(self, raw_response: object) -> Optional[dict]:
        if isinstance(raw_response, dict):
            return raw_response
        if isinstance(raw_response, BaseMessage):
            content = raw_response.content
        else:
            content = raw_response
        if isinstance(content, str):
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                logger.debug("Failed to decode JSON from LLM response: %.120s", content)
                return None
        return None

    def _build_entry_from_payload(self, payload: dict) -> Optional[ApiEntry]:
        if not isinstance(payload, dict):
            return None
        entry_type = payload.get("entry_type")
        name = payload.get("name")
        if not entry_type or not name:
            return None
        category = payload.get("category")
        description = payload.get("description")
        params_payload = payload.get("params", [])
        returns_payload = payload.get("returns")
        properties_payload = payload.get("properties", [])
        params = [
            self._build_param_from_payload(param_payload, idx)
            for idx, param_payload in enumerate(params_payload or [])
        ]
        params = [param for param in params if param]
        returns = (
            self._build_return_from_payload(returns_payload)
            if returns_payload
            else None
        )
        properties = [
            prop
            for prop in (
                self._build_property_from_payload(prop_payload)
                for prop_payload in properties_payload or []
            )
            if prop
        ]
        return ApiEntry(
            entry_type=entry_type,
            name=name,
            description=description,
            category=category,
            params=params,
            returns=returns,
            notes=payload.get("notes"),
            implementation_status=payload.get("implementation_status"),
            properties=properties,
        )

    def _build_param_from_payload(
        self, payload: dict, position: int
    ) -> Optional[ParameterDefinition]:
        if not isinstance(payload, dict):
            return None
        name = payload.get("name")
        if not name:
            return None
        raw_type = payload.get("type")
        normalized_type, array_info = self.type_registry.extract_type(raw_type)
        return ParameterDefinition(
            name=name,
            position=position,
            type=normalized_type,
            description=payload.get("description"),
            is_required=payload.get("is_required", True),
            default_value=payload.get("default_value"),
            array_info=array_info,
        )

    def _build_return_from_payload(self, payload: dict) -> Optional[ReturnDefinition]:
        if not isinstance(payload, dict):
            return None
        raw_type = payload.get("type")
        normalized_type, _ = self.type_registry.extract_type(raw_type)
        return ReturnDefinition(
            type=normalized_type,
            description=payload.get("description"),
            is_array=payload.get("is_array", False),
        )

    def _build_property_from_payload(
        self, payload: dict
    ) -> Optional[PropertyDefinition]:
        if not isinstance(payload, dict):
            return None
        name = payload.get("name")
        if not name:
            return None
        raw_type = payload.get("type")
        normalized_type, array_info = self.type_registry.extract_type(raw_type)
        return PropertyDefinition(
            name=name,
            type=normalized_type,
            description=payload.get("description"),
            array_info=array_info,
        )


def run_llm_extraction(
    api_text: str, type_text: str, config: LLMExtractionConfig | None = None
) -> ApiExtractionResult:
    """APIテキストと型定義テキストからLLMを利用して抽出を実行する。"""

    type_defs = parse_type_definitions(type_text)
    extractor = LLMApiExtractor(type_defs, config)
    entries = extractor.extract(api_text)
    return ApiExtractionResult(type_definitions=type_defs, api_entries=entries)
