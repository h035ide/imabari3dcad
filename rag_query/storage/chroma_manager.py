"""
ChromaDBベクトルストア管理モジュール

ChromaDBベクトルデータベースの構築と管理を行います。
"""

import json
import shutil
from pathlib import Path
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.graphs.graph_document import GraphDocument

from ..core.logger import get_logger
from ..core.exceptions import StorageError
from ..utils.file_utils import ensure_directory

logger = get_logger(__name__)


class ChromaManager:
    """ChromaDBベクトルストア管理クラス"""

    def __init__(self, openai_api_key: str, persist_directory: Path):
        """
        初期化

        Args:
            openai_api_key: OpenAI APIキー
            persist_directory: ChromaDB永続化ディレクトリ
        """
        self.openai_api_key = openai_api_key
        self.persist_directory = persist_directory
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

    def build_vectorstore(
        self, graph_docs: List[GraphDocument], save_debug_data: bool = True
    ) -> None:
        """
        GraphDocumentからベクトルストアを構築する

        Args:
            graph_docs: GraphDocumentのリスト
            save_debug_data: デバッグ用JSONファイルを保存するかどうか

        Raises:
            StorageError: ベクトルストア構築エラー時
        """
        try:
            logger.info("ChromaDBベクトルストアの構築を開始")

            if not graph_docs:
                logger.warning("GraphDocumentが空のため、ChromaDB構築をスキップ")
                return

            # 既存のディレクトリをクリア
            self._clear_persist_directory()

            # ベクトル化用のドキュメントを準備
            documents = self._prepare_documents(graph_docs[0])

            if not documents:
                logger.warning("ベクトル化対象のドキュメントがありません")
                return

            # デバッグ用データを保存
            if save_debug_data:
                self._save_debug_data(documents)

            # ChromaDBを構築
            vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=str(self.persist_directory),
            )

            logger.info(
                f"ChromaDBベクトルストア構築完了: {len(documents)}件のドキュメント"
            )

        except Exception as e:
            raise StorageError(f"ChromaDBベクトルストア構築に失敗しました", str(e))

    def load_vectorstore(self) -> Chroma:
        """
        既存のベクトルストアを読み込む

        Returns:
            Chromaベクトルストア

        Raises:
            StorageError: ベクトルストア読み込みエラー時
        """
        try:
            if not self.persist_directory.exists():
                raise StorageError(
                    f"ChromaDBディレクトリが存在しません: {self.persist_directory}"
                )

            vectorstore = Chroma(
                persist_directory=str(self.persist_directory),
                embedding_function=self.embeddings,
            )

            logger.info(
                f"ChromaDBベクトルストアを読み込みました: {self.persist_directory}"
            )
            return vectorstore

        except Exception as e:
            raise StorageError(f"ChromaDBベクトルストア読み込みに失敗しました", str(e))

    def _clear_persist_directory(self) -> None:
        """永続化ディレクトリをクリアする"""
        if self.persist_directory.exists():
            shutil.rmtree(self.persist_directory)
            logger.info(
                f"既存のChromaDBディレクトリを削除しました: {self.persist_directory}"
            )

        ensure_directory(self.persist_directory)

    def _prepare_documents(self, graph_doc: GraphDocument) -> List[Document]:
        """
        GraphDocumentからベクトル化用のDocumentリストを準備する

        Args:
            graph_doc: GraphDocument

        Returns:
            ベクトル化用Documentのリスト
        """
        documents = []

        logger.info(f"ベクトル化対象ノード数: {len(graph_doc.nodes)}")

        for node in graph_doc.nodes:
            content = self._create_node_content(node)
            metadata = self._create_node_metadata(node)

            documents.append(Document(page_content=content.strip(), metadata=metadata))

        return documents

    def _create_node_content(self, node) -> str:
        """
        ノードからベクトル化用のコンテンツを生成する

        Args:
            node: グラフノード

        Returns:
            ベクトル化用テキスト
        """
        props = node.properties

        if node.type == "Method":
            return f"APIメソッド\nメソッド名: {props.get('name', '')}\n説明: {props.get('description', '')}"

        elif node.type == "ScriptExample":
            code = props.get("code", "")
            # コードが長すぎる場合は適切に切り詰める
            if len(code) > 2000:
                code = code[:2000] + "\n... (省略)"
            return f"スクリプト例\nファイル名: {props.get('name', '')}\n全文コード:\n```python\n{code}\n```"

        else:
            # その他のノードタイプ
            prop_text = "\n".join([f"- {key}: {value}" for key, value in props.items()])
            return f"ノードタイプ: {node.type}\nID: {node.id}\nプロパティ:\n{prop_text}"

    def _create_node_metadata(self, node) -> Dict[str, Any]:
        """
        ノードからメタデータを生成する

        Args:
            node: グラフノード

        Returns:
            メタデータ辞書
        """
        return {
            "source": "graph_node",
            "node_id": node.id,
            "node_type": node.type,
        }

    def _save_debug_data(self, documents: List[Document]) -> None:
        """
        デバッグ用にドキュメントデータをJSONファイルに保存する

        Args:
            documents: Documentのリスト
        """
        try:
            debug_data = [
                {"page_content": doc.page_content, "metadata": doc.metadata}
                for doc in documents
            ]

            debug_file = Path("chroma_data.json")
            with open(debug_file, "w", encoding="utf-8") as f:
                json.dump(debug_data, f, indent=2, ensure_ascii=False)

            logger.info(f"ChromaDB投入前のデータを保存しました: {debug_file}")

        except Exception as e:
            logger.warning(f"デバッグデータ保存エラー: {e}")
