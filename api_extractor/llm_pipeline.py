"""LLMベースのAPI抽出パイプライン骨子。

現時点ではモックチェーンを返すスタブ実装のみを提供する。今後、LangChainや
LlamaIndexのコンポーネントを組み合わせ、チャンク生成→LLM呼び出し→構造化
整形を段階的に追加する。
"""

from __future__ import annotations

import json
import logging

from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Set

from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import TextNode
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableSequence
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, ValidationError

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
    chunk_size: int = field(default=512)
    chunk_overlap: int = field(default=64)
    temperature: float = field(default=0.0)
    max_retries: int = field(default=2)
    request_timeout: int = field(default=180)
    response_format: str = "json_object"
    max_chunk_overlap_ratio: float = field(default=0.3, metadata={"ge": 0.0, "le": 0.9})


class LLMParameterPayload(BaseModel):
    """LLMに期待するパラメータのスキーマ。"""

    name: str
    type: Optional[str] = None
    description: Optional[str] = None
    is_required: Optional[bool] = True
    default_value: Optional[str] = None
    array_info: Optional[str] = Field(
        default=None,
        description="When the value is an array, describe the qualifier such as '配列' or 'list'.",
    )


class LLMReturnPayload(BaseModel):
    type: Optional[str] = None
    description: Optional[str] = None
    is_array: Optional[bool] = False


class LLMPropertyPayload(BaseModel):
    name: str
    type: Optional[str] = None
    description: Optional[str] = None
    array_info: Optional[str] = None


class LLMEntryPayload(BaseModel):
    entry_type: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    params: List[LLMParameterPayload] = Field(default_factory=list)
    returns: Optional[LLMReturnPayload] = None
    properties: List[LLMPropertyPayload] = Field(default_factory=list)
    notes: Optional[str] = None
    implementation_status: Optional[str] = None


class LLMChunkResponse(BaseModel):
    entries: List[LLMEntryPayload] = Field(default_factory=list)


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
        resolved_overlap = self._resolve_chunk_overlap(
            self.config.chunk_size, self.config.chunk_overlap
        )
        self._splitter = SentenceSplitter(
            chunk_size=int(self.config.chunk_size),
            chunk_overlap=int(resolved_overlap),
        )
        self._last_chunks: List[TextNode] = []
        self._llm_override: Optional[Runnable] = llm
        self._llm_cached: Optional[Runnable] = None
        self._prompt: Optional[ChatPromptTemplate] = None
        self._parser: Optional[JsonOutputParser] = None
        self._chain: Optional[RunnableSequence] = None
        self._type_catalog_text = self._build_type_catalog()
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
        chain = self._get_chain()
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
                raw = chain.invoke(payload)
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

    def _resolve_chunk_overlap(self, chunk_size: int, overlap: int) -> int:
        chunk_size = int(chunk_size)
        overlap = int(overlap)
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        max_allowed = int(chunk_size * self.config.max_chunk_overlap_ratio)
        resolved_overlap = min(max(overlap, 0), max_allowed)
        if resolved_overlap != overlap:
            logger.debug(
                "Adjusted chunk_overlap from %d to %d based on chunk_size=%d and ratio %.2f",
                overlap,
                resolved_overlap,
                chunk_size,
                self.config.max_chunk_overlap_ratio,
            )
        return resolved_overlap

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

    def _get_parser(self) -> JsonOutputParser:
        if self._parser is None:
            self._parser = JsonOutputParser(pydantic_object=LLMChunkResponse)
        return self._parser

    def _get_chain(self) -> RunnableSequence:
        if self._chain is None:
            self._chain = self._get_prompt() | self._get_llm() | self._get_parser()
        return self._chain

    def _get_prompt(self) -> ChatPromptTemplate:
        if self._prompt is None:
            format_instructions = self._get_parser().get_format_instructions()
            self._prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """あなたはCADソフトのAPI仕様から厳密な構造化データを抽出するエキスパートです。
                        JSONスキーマに従い、チャンク内に記載されている関数／オブジェクトを漏れなく抽出してください。
                        原文に無い情報は推測せず null を使用し、値の単位や説明は日本語のまま保持してください。""",
                    ),
                    (
                        "human",
                        """# 出力仕様
                        {format_instructions}

                        # 型候補の参考
                        {type_catalog}

                        # チャンクテキスト
                        ---
                        {chunk_text}
                        ---

                        # メタデータ (参考)
                        {chunk_metadata}
                        """,
                    ),
                ]
            ).partial(type_catalog=self._type_catalog_text)
        return self._prompt

    def _parse_llm_response(self, raw_response: object) -> List[ApiEntry]:
        response = self._coerce_chunk_response(raw_response)
        if response is None:
            return []
        entries_payload = response.entries
        results: List[ApiEntry] = []
        for item in entries_payload:
            entry = self._build_entry_from_payload(item)
            if entry:
                results.append(entry)
            else:
                logger.debug("Skipping invalid entry payload: %s", item)
        logger.debug("Parsed %d entries from LLM response", len(results))
        return results

    def _coerce_chunk_response(
        self, raw_response: object
    ) -> Optional[LLMChunkResponse]:
        if isinstance(raw_response, LLMChunkResponse):
            return raw_response
        if isinstance(raw_response, dict):
            try:
                return LLMChunkResponse(**raw_response)
            except ValidationError:
                logger.debug("Failed to validate response dict: %s", raw_response)
                return None
        if isinstance(raw_response, BaseMessage):
            content = raw_response.content
        else:
            content = raw_response
        if isinstance(content, str):
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                logger.debug("Failed to decode JSON from LLM response: %.120s", content)
                return None
            try:
                return LLMChunkResponse(**data)
            except ValidationError:
                logger.debug("Failed to validate JSON content: %s", data)
                return None
        return None

    def _build_entry_from_payload(
        self, payload: LLMEntryPayload | dict
    ) -> Optional[ApiEntry]:
        if isinstance(payload, LLMEntryPayload):
            data = payload
        elif isinstance(payload, dict):
            try:
                data = LLMEntryPayload(**payload)
            except ValidationError:
                logger.debug("Invalid entry payload: %s", payload)
                return None
        else:
            return None
        entry_type = data.entry_type
        name = data.name
        if not entry_type or not name:
            return None
        category = data.category
        description = data.description
        params_payload = data.params or []
        returns_payload = data.returns
        properties_payload = data.properties or []
        params = [
            self._build_param_from_payload(param_payload, idx)
            for idx, param_payload in enumerate(params_payload)
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
                for prop_payload in properties_payload
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
            notes=data.notes,
            implementation_status=data.implementation_status,
            properties=properties,
        )

    def _build_param_from_payload(
        self, payload: LLMParameterPayload | dict, position: int
    ) -> Optional[ParameterDefinition]:
        if isinstance(payload, LLMParameterPayload):
            data = payload
        elif isinstance(payload, dict):
            try:
                data = LLMParameterPayload(**payload)
            except ValidationError:
                logger.debug("Invalid parameter payload: %s", payload)
                return None
        else:
            return None
        name = data.name
        if not name:
            return None
        raw_type = data.type
        normalized_type, array_info = self.type_registry.extract_type(raw_type)
        return ParameterDefinition(
            name=name,
            position=position,
            type=normalized_type,
            description=data.description,
            is_required=data.is_required if data.is_required is not None else True,
            default_value=data.default_value,
            array_info=array_info,
        )

    def _build_return_from_payload(
        self, payload: LLMReturnPayload | dict
    ) -> Optional[ReturnDefinition]:
        if isinstance(payload, LLMReturnPayload):
            data = payload
        elif isinstance(payload, dict):
            try:
                data = LLMReturnPayload(**payload)
            except ValidationError:
                logger.debug("Invalid return payload: %s", payload)
                return None
        else:
            return None
        raw_type = data.type
        normalized_type, _ = self.type_registry.extract_type(raw_type)
        return ReturnDefinition(
            type=normalized_type,
            description=data.description,
            is_array=data.is_array or False,
        )

    def _build_property_from_payload(
        self, payload: LLMPropertyPayload | dict
    ) -> Optional[PropertyDefinition]:
        if isinstance(payload, LLMPropertyPayload):
            data = payload
        elif isinstance(payload, dict):
            try:
                data = LLMPropertyPayload(**payload)
            except ValidationError:
                logger.debug("Invalid property payload: %s", payload)
                return None
        else:
            return None
        name = data.name
        if not name:
            return None
        raw_type = data.type
        normalized_type, array_info = self.type_registry.extract_type(raw_type)
        return PropertyDefinition(
            name=name,
            type=normalized_type,
            description=data.description,
            array_info=array_info,
        )

    def _build_type_catalog(self) -> str:
        if not self.type_definitions:
            return "(型定義が未取得)"
        # 文字数制限で過度なトークン使用を防ぐ
        max_chars = 1200
        lines: List[str] = []
        current_len = 0
        for definition in self.type_definitions:
            line = f"- {definition.name}: {definition.description}"
            if current_len + len(line) > max_chars:
                lines.append("- ... (省略) ...")
                break
            lines.append(line)
            current_len += len(line)
        return "\n".join(lines)


def run_llm_extraction(
    api_text: str, type_text: str, config: LLMExtractionConfig | None = None
) -> ApiExtractionResult:
    """APIテキストと型定義テキストからLLMを利用して抽出を実行する。"""

    type_defs = parse_type_definitions(type_text)
    extractor = LLMApiExtractor(type_defs, config)
    entries = extractor.extract(api_text)
    return ApiExtractionResult(type_definitions=type_defs, api_entries=entries)
