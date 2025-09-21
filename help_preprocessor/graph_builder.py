from __future__ import annotations

"""Graph construction pipeline pieces for the help preprocessor."""

from typing import Iterable

from .schemas import HelpCategory


class HelpGraphBuilder:
    """Create Neo4j-ready payloads from help category structures."""

    # TODO(Phase3): Accept cached parse artifacts and emit batched payloads.
    def build_nodes(self, root_category: HelpCategory) -> list[dict]:  # pragma: no cover - placeholder
        """Return graph node dictionaries ready for ingestion."""

        raise NotImplementedError("Graph node construction has not been implemented yet.")

    def build_relationships(self, root_category: HelpCategory) -> list[dict]:  # pragma: no cover
        """Return graph relationship dictionaries ready for ingestion."""

        raise NotImplementedError("Graph relationship construction has not been implemented yet.")
