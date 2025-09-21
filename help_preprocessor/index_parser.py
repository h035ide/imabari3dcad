from __future__ import annotations

"""Parser for EVOSHIP help index definitions."""

from pathlib import Path
from typing import Iterable

from .schemas import HelpCategory


class HelpIndexParser:
    """Build hierarchical category metadata from index.txt files."""

    def __init__(self, index_path: Path, encoding: str = "shift_jis") -> None:
        self.index_path = index_path
        self.encoding = encoding

    # TODO(Phase2): Implement line-by-line parsing with cache integration.
    def parse(self) -> HelpCategory:  # pragma: no cover - placeholder
        """Return the root category parsed from the index file."""

        raise NotImplementedError("Index parsing has not been implemented yet.")

    def iter_errors(self) -> Iterable[str]:  # pragma: no cover - placeholder
        """Yield human readable parsing diagnostics."""

        return []
