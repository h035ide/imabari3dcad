"""LLMベースのAPI抽出パイプライン骨子。

現時点ではモックチェーンを返すスタブ実装のみを提供する。今後、LangChainや
LlamaIndexのコンポーネントを組み合わせ、チャンク生成→LLM呼び出し→構造化
整形を段階的に追加する。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import TextNode

from .models import ApiEntry, ApiExtractionResult, TypeDefinition
from .type_parser import parse_type_definitions
from .type_registry import TypeRegistry


@dataclass(slots=True)
class LLMExtractionConfig:
    """LLM抽出設定値。

    本設定は今後、チャンクサイズや並列度、モデル名などをパラメータ化する際に
    拡張する。暫定で `model` のみを保持し、デフォルト値を指定する。
    """

    model: str = "gpt-4.1-mini"
    chunk_size: int = 512
    chunk_overlap: int = 64


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
    ):
        self.type_definitions = list(type_definitions)
        self.config = config or LLMExtractionConfig()
        self.type_registry = TypeRegistry(self.type_definitions)
        self._splitter = SentenceSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
        )
        self._last_chunks: List[TextNode] = []

    def extract(self, api_text: str) -> List[ApiEntry]:
        """LLMを利用してAPIテキストから構造化情報を抽出する。

        TODO: LangChainのStructured Output機能やLlamaIndexのRetrieverを用いた
        実装に置き換える。現時点では既存正規表現実装と同等の処理が未実装のため
        空リストを返す仮実装とする。
        """

        self._last_chunks = self._chunk_api_text(api_text)
        return []

    def _chunk_api_text(self, api_text: str) -> List[TextNode]:
        """`api.txt` のコンテンツをチャンク化してノード列として返す。"""

        document = Document(text=api_text, metadata={"source": "api.txt"})
        nodes = self._splitter.get_nodes_from_documents(
            [document],
            show_progress=False,
        )
        return nodes


def run_llm_extraction(
    api_text: str, type_text: str, config: LLMExtractionConfig | None = None
) -> ApiExtractionResult:
    """APIテキストと型定義テキストからLLMを利用して抽出を実行する。"""

    type_defs = parse_type_definitions(type_text)
    extractor = LLMApiExtractor(type_defs, config)
    entries = extractor.extract(api_text)
    return ApiExtractionResult(type_definitions=type_defs, api_entries=entries)
