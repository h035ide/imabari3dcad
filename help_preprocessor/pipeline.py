from __future__ import annotations

"""High-level orchestration for the help preprocessor pipeline."""

from dataclasses import dataclass
from typing import Optional

from .config import HelpPreprocessorConfig


@dataclass(slots=True)
class HelpPreprocessorPipeline:
    """Coordinate parsing, graph building, and storage steps."""

    config: HelpPreprocessorConfig

    # TODO(Phase2): Introduce caching hooks to avoid repeated HTML/index parsing.
    def run(self, dry_run: bool = False) -> None:  # pragma: no cover - placeholder
        """Execute the end-to-end pipeline."""

        raise NotImplementedError("Pipeline execution has not been implemented yet.")

    def build_only(self) -> None:  # pragma: no cover - placeholder
        """Perform parsing and transformation without writing to storage."""

        raise NotImplementedError("Partial pipeline execution has not been implemented yet.")
