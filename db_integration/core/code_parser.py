import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Node
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ロギング設定
logger = logging.getLogger(__name__)

# LLMが利用可能かどうかのフラグ
LLM_AVAILABLE = True
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    LLM_AVAILABLE = False
    logger.warning("LangChainが利用できません。LLM機能は無効化されます。")


class NodeType(Enum):
    """Tree-sitterノードタイプの列挙"""
    MODULE = "Module"
    CLASS = "Class"
    FUNCTION = "Function"
    VARIABLE = "Variable"
    PARAMETER = "Parameter"
    IMPORT = "Import"
    COMMENT = "Comment"
    CALL = "Call"
    ASSIGNMENT = "Assignment"
    ATTRIBUTE = "Attribute"
    STRING = "String"
    DECORATOR = "Decorator"
    # ... 他のノードタイプも必要に応じて追加 ...

class RelationType(Enum):
    """Neo4jリレーションタイプの列挙"""
    CONTAINS = "CONTAINS"
    CALLS = "CALLS"
    USES = "USES"
    IMPORTS = "IMPORTS"
    HAS_PARAMETER = "HAS_PARAMETER"
    INHERITS = "INHERITS"
    DECORATES = "DECORATES"
    # ... 他のリレーションタイプも必要に応じて追加 ...

@dataclass
class SyntaxNode:
    """構文ノードの情報を格納するデータクラス"""
    node_id: str
    node_type: NodeType
    name: str
    text: str
    start_byte: int
    end_byte: int
    line_start: int
    line_end: int
    properties: Dict[str, Any]
    parent_id: Optional[str] = None
    llm_insights: Optional[Dict[str, Any]] = None

@dataclass
class SyntaxRelation:
    """構文関係の情報を格納するデータクラス"""
    source_id: str
    target_id: str
    relation_type: RelationType
    properties: Dict[str, Any]

class CodeParser:
    """
    Tree-sitterを使用してPythonコードを解析し、
    構文ノードとリレーションのリストを生成するクラス。
    """

    def __init__(self, enable_llm: bool = True):
        self.py_language = Language(tspython.language())
        self.parser = Parser()
        self.parser.language = self.py_language
        self.enable_llm = enable_llm and LLM_AVAILABLE
        self.llm_analyzer = None

        if self.enable_llm:
            if os.getenv("OPENAI_API_KEY"):
                self.llm_analyzer = ChatOpenAI(
                    model="gpt-5-nano",
                    reasoning_effort="low",  # 'low', 'medium', 'high' から選択
                )
                logger.info("CodeParserのLLM機能が有効化されました。")
            else:
                logger.warning("OPENAI_API_KEYが見つかりません。LLM機能は無効です。")
                self.enable_llm = False

        self.node_counter = 0
        self.syntax_nodes: List[SyntaxNode] = []
        self.syntax_relations: List[SyntaxRelation] = []

    def _generate_node_id(self, node_type: NodeType) -> str:
        """一意のノードIDを生成する。"""
        self.node_counter += 1
        return f"{node_type.value}_{self.node_counter}"

    def parse_file(self, file_path: str) -> Tuple[List[SyntaxNode], List[SyntaxRelation]]:
        """
        単一のPythonファイルを解析し、ノードとリレーションのリストを返す。

        Args:
            file_path (str): 解析対象のPythonファイルへのパス。

        Returns:
            Tuple[List[SyntaxNode], List[SyntaxRelation]]:
                解析された構文ノードのリストと構文リレーションのリスト。
        """
        logger.info(f"コードファイルの解析を開始します: {file_path}")
        self.syntax_nodes = []
        self.syntax_relations = []
        self.node_counter = 0

        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()

        source_code_bytes = bytes(source_code, "utf8")
        tree = self.parser.parse(source_code_bytes)

        self._extract_elements(tree.root_node, source_code_bytes, file_path)

        if self.enable_llm:
            self._enhance_with_llm()

        logger.info(f"コードファイルの解析が完了しました。{len(self.syntax_nodes)}個のノードと{len(self.syntax_relations)}個のリレーションを抽出しました。")
        return self.syntax_nodes, self.syntax_relations

    def _extract_elements(self, node: Node, source_code: bytes, file_path: str, parent_id: Optional[str] = None):
        """ASTを再帰的に巡回し、要素を抽出する。"""
        node_type_enum = self._determine_node_type(node)
        if node_type_enum is None:
            for child in node.children:
                self._extract_elements(child, source_code, file_path, parent_id)
            return

        node_id = self._generate_node_id(node_type_enum)
        node_text = source_code[node.start_byte:node.end_byte].decode('utf8')
        name = self._get_node_name(node, node_type_enum, node_text)

        properties = {
            "file_path": file_path,
            "raw_type": node.type,
        }
        # 特定のノードタイプに応じたプロパティを追加
        if node_type_enum == NodeType.FUNCTION:
            # パラメータや戻り値の型などの情報を抽出
            pass

        syntax_node = SyntaxNode(
            node_id=node_id,
            node_type=node_type_enum,
            name=name,
            text=node_text,
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            line_start=node.start_point[0],
            line_end=node.end_point[0],
            properties=properties,
            parent_id=parent_id
        )
        self.syntax_nodes.append(syntax_node)

        if parent_id:
            relation = SyntaxRelation(
                source_id=parent_id,
                target_id=node_id,
                relation_type=RelationType.CONTAINS,
                properties={}
            )
            self.syntax_relations.append(relation)

        # 子ノードを再帰的に処理
        for child in node.children:
            self._extract_elements(child, source_code, file_path, node_id)

        # 追加のリレーションを抽出 (例: CALLS)
        if node_type_enum == NodeType.CALL:
            self._extract_call_relations(node, node_id)

    def _determine_node_type(self, node: Node) -> Optional[NodeType]:
        """tree-sitterのノードタイプを内部のNodeTypeにマッピングする。"""
        type_mapping = {
            "module": NodeType.MODULE,
            "class_definition": NodeType.CLASS,
            "function_definition": NodeType.FUNCTION,
            "import_statement": NodeType.IMPORT,
            "call": NodeType.CALL,
            "assignment": NodeType.ASSIGNMENT,
            "attribute": NodeType.ATTRIBUTE,
            "identifier": NodeType.VARIABLE,
        }
        return type_mapping.get(node.type)

    def _get_node_name(self, node: Node, node_type: NodeType, text: str) -> str:
        """ノードの名前を抽出する。"""
        if node_type in [NodeType.FUNCTION, NodeType.CLASS]:
            name_node = node.child_by_field_name("name")
            if name_node:
                return name_node.text.decode('utf8')
        if node_type == NodeType.VARIABLE:
             return text
        if node_type == NodeType.CALL:
             func_node = node.child_by_field_name("function")
             if func_node:
                 return func_node.text.decode('utf8')
        return text.split('\n')[0][:80] # デフォルト名

    def _extract_call_relations(self, call_node: Node, call_node_id: str):
        """関数呼び出しの関係性を抽出する。"""
        func_node = call_node.child_by_field_name("function")
        if func_node:
            target_func_name = func_node.text.decode('utf8')
            # 既に抽出されたFunctionノードを名前で探す
            for existing_node in self.syntax_nodes:
                if existing_node.node_type == NodeType.FUNCTION and existing_node.name == target_func_name:
                    relation = SyntaxRelation(
                        source_id=call_node_id,
                        target_id=existing_node.node_id,
                        relation_type=RelationType.CALLS,
                        properties={}
                    )
                    self.syntax_relations.append(relation)
                    break

    def _enhance_with_llm(self):
        """LLMを使用して主要なノードに説明を追加する。"""
        logger.info("LLMによるコード理解の強化を開始します...")
        for node in self.syntax_nodes:
            if node.node_type in [NodeType.FUNCTION, NodeType.CLASS]:
                try:
                    prompt_template = ChatPromptTemplate.from_messages([
                        ("system", "あなたはPythonコードの専門家です。以下のコード片が何をするものか、その目的と主な役割を日本語で簡潔に説明してください。"),
                        ("human", "{code_text}")
                    ])
                    chain = prompt_template | self.llm_analyzer | StrOutputParser()
                    description = chain.invoke({"code_text": node.text})
                    node.llm_insights = {"description": description.strip()}
                    logger.debug(f"LLMが {node.name} の説明を生成しました。")
                except Exception as e:
                    logger.error(f"LLMで {node.name} の説明生成中にエラー: {e}")
