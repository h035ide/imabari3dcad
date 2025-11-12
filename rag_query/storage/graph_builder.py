"""
グラフ構築モジュール

トリプルデータからLangChainのGraphDocumentを構築します。
"""

from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_community.graphs.graph_document import GraphDocument, Node, Relationship

from ..core.logger import get_logger
from ..core.exceptions import DataProcessingError

logger = get_logger(__name__)


class GraphBuilder:
    """グラフドキュメント構築クラス"""

    def build_graph_documents(
        self, triples: List[Dict[str, Any]], node_props: Dict[str, Dict[str, Any]]
    ) -> List[GraphDocument]:
        """
        トリプルとノードプロパティからGraphDocumentを構築する

        Args:
            triples: トリプルのリスト
            node_props: ノードプロパティ辞書

        Returns:
            GraphDocumentのリスト

        Raises:
            DataProcessingError: グラフ構築エラー時
        """
        try:
            logger.info("GraphDocument構築開始")

            node_map = {}

            # ノードを作成
            for node_id, meta in node_props.items():
                if node_id in node_map:
                    # 既存ノードのプロパティを更新
                    existing_node = node_map[node_id]
                    existing_node.properties.update(meta.get("properties", {}))
                else:
                    # 新しいノードを作成
                    node_type = meta["type"]
                    properties = meta.get("properties", {})
                    node_map[node_id] = Node(
                        id=node_id, type=node_type, properties=properties
                    )

            # リレーションシップを作成
            relationships = []
            for triple in triples:
                source_node = node_map.get(triple["source"])
                if not source_node:
                    # 存在しないノードを作成
                    source_node = Node(id=triple["source"], type=triple["source_type"])
                    node_map[triple["source"]] = source_node

                target_node = node_map.get(triple["target"])
                if not target_node:
                    # 存在しないノードを作成
                    target_node = Node(id=triple["target"], type=triple["target_type"])
                    node_map[triple["target"]] = target_node

                # リレーションシップを作成
                relationships.append(
                    Relationship(
                        source=source_node,
                        target=target_node,
                        type=triple["label"],
                        properties={},
                    )
                )

            # GraphDocumentを作成
            doc = Document(page_content="API Spec and Example graph")
            graph_doc = GraphDocument(
                nodes=list(node_map.values()), relationships=relationships, source=doc
            )

            logger.info(
                f"GraphDocument構築完了: ノード={len(node_map)}件, リレーション={len(relationships)}件"
            )
            return [graph_doc]

        except Exception as e:
            raise DataProcessingError(f"GraphDocument構築エラー", str(e))
