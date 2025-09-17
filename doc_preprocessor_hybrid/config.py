from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PipelineConfig:
    api_doc_path: Path = Path("data/src/api.txt")
    api_arg_path: Path = Path("data/src/api_arg.txt")
    output_dir: Path = Path("doc_preprocessor_hybrid/out")

    @property
    def structured_output(self) -> Path:
        return self.output_dir / "structured_api.json"

    @property
    def graph_output(self) -> Path:
        return self.output_dir / "graph_payload.json"

    @property
    def vector_output(self) -> Path:
        return self.output_dir / "vector_chunks.jsonl"
