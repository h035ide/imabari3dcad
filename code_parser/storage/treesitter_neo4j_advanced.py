import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Node
from neo4j import GraphDatabase
import os
import sys
from typing import Dict, List, Any, Optional, Tuple, Set
import json
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from pathlib import Path
import time
import argparse
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# .envファイルを読み込む
load_dotenv()

# LLM関連のインポート
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    print("警告: LangChainまたは関連ライブラリが利用できません。LLM機能は無効化されます。")

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    NUMBER = "Number"
    BOOLEAN = "Boolean"
    OPERATOR = "Operator"
    DECORATOR = "Decorator"
    ANNOTATION = "Annotation"
    EXCEPTION = "Exception"
    LOOP = "Loop"
    CONDITION = "Condition"

class RelationType(Enum):
    """Neo4jリレーションタイプの列挙"""
    CONTAINS = "CONTAINS"
    CALLS = "CALLS"
    USES = "USES"
    IMPORTS = "IMPORTS"
    HAS_PARAMETER = "HAS_PARAMETER"
    RETURNS = "RETURNS"
    ASSIGNS = "ASSIGNS"
    HAS_ATTRIBUTE = "HAS_ATTRIBUTE"
    REFERENCES = "REFERENCES"
    DECLARES = "DECLARES"
    INHERITS = "INHERITS"
    IMPLEMENTS = "IMPLEMENTS"
    DECORATES = "DECORATES"
    THROWS = "THROWS"
    HANDLES = "HANDLES"
    ITERATES = "ITERATES"
    CONDITIONAL = "CONDITIONAL"

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
    complexity_score: float = 0.0
    llm_insights: Optional[Dict[str, Any]] = None

@dataclass
class SyntaxRelation:
    """構文関係の情報を格納するデータクラス"""
    source_id: str
    target_id: str
    relation_type: RelationType
    properties: Dict[str, Any]
    weight: float = 1.0

class CodeComplexityAnalyzer:
    """コードの複雑性を分析するクラス"""
    
    @staticmethod
    def calculate_cyclomatic_complexity(node: Node) -> int:
        """循環複雑度を計算"""
        complexity = 1  # 基本値
        
        def count_decision_points(n: Node):
            nonlocal complexity
            if n.type in ["if_statement", "elif_clause", "else_clause", 
                         "for_statement", "while_statement", "except_clause",
                         "and", "or"]:
                complexity += 1
            for child in n.children:
                count_decision_points(child)
        
        count_decision_points(node)
        return complexity
    
    @staticmethod
    def calculate_cognitive_complexity(node: Node) -> int:
        """認知的複雑度を計算"""
        complexity = 0
        
        def count_cognitive_elements(n: Node, nesting_level: int = 0):
            nonlocal complexity
            if n.type in ["if_statement", "elif_clause", "else_clause"]:
                complexity += 1 + nesting_level
            elif n.type in ["for_statement", "while_statement"]:
                complexity += 1 + nesting_level
            elif n.type in ["try_statement", "except_clause"]:
                complexity += 1 + nesting_level
            elif n.type in ["and", "or"]:
                complexity += 1
            
            for child in n.children:
                count_cognitive_elements(child, nesting_level + 1)
        
        count_cognitive_elements(node)
        return complexity

class TreeSitterNeo4jAdvancedBuilder:
    """高度なTree-sitter Neo4j統合システム"""
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str, 
                 database_name: str = "treesitter", 
                 enable_llm: bool = True):
        """初期化"""
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.database_name = database_name
        self.enable_llm = enable_llm
        
        # Tree-sitterセットアップ
        self.py_language = Language(tspython.language())
        self.parser = Parser()
        self.parser.language = self.py_language
        
        # データ格納
        self.syntax_nodes: List[SyntaxNode] = []
        self.syntax_relations: List[SyntaxRelation] = []
        self.node_counter = 0
        self.file_metrics: Dict[str, Any] = {}
        
        # 分析ツール
        self.complexity_analyzer = CodeComplexityAnalyzer()
        self.llm_analyzer = None
        
        # LLM設定
        if self.enable_llm and LLM_AVAILABLE:
            if os.getenv("OPENAI_API_KEY"):
                self.setup_llm()
            else:
                logger.warning("OPENAI_API_KEYが設定されていません。LLM機能は無効化されます。")
                self.enable_llm = False
    
    def setup_llm(self):
        """LLMの設定"""
        try:
            # ChatOpenAIは環境変数から自動的にAPIキーを読み込みます
            self.llm_analyzer = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3, max_tokens=200)
            logger.info("LLM機能が有効化されました")
        except Exception as e:
            logger.error(f"LLM設定エラー: {e}")
            self.enable_llm = False
    
    def analyze_file(self, file_path: str) -> None:
        """ファイルを解析"""
        logger.info(f"ファイル解析開始: {file_path}")
        
        # ファイル読み込み
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()
        
        # Tree-sitter解析
        source_code_bytes = bytes(source_code, "utf8")
        tree = self.parser.parse(source_code_bytes)
        root_node = tree.root_node
        
        # ファイルメトリクスの計算
        self.calculate_file_metrics(file_path, root_node, source_code)
        
        # 構文要素の抽出
        self.extract_syntax_elements(root_node, source_code_bytes, file_path)
        
        # LLMによる詳細分析
        if self.enable_llm and self.llm_analyzer:
            self.enhance_with_llm(file_path)
        
        logger.info(f"ファイル解析完了: {file_path}")
    
    def calculate_file_metrics(self, file_path: str, root_node: Node, source_code: str) -> None:
        """ファイルメトリクスを計算"""
        lines = source_code.split('\n')
        
        metrics = {
            "file_path": file_path,
            "total_lines": len(lines),
            "code_lines": len([line for line in lines if line.strip() and not line.strip().startswith('#')]),
            "comment_lines": len([line for line in lines if line.strip().startswith('#')]),
            "blank_lines": len([line for line in lines if not line.strip()]),
            "functions": 0,
            "classes": 0,
            "imports": 0,
            "variables": 0,
            "complexity_score": 0.0
        }
        
        # 構文要素のカウント
        def count_elements(node: Node):
            if node.type == "function_definition":
                metrics["functions"] += 1
                metrics["complexity_score"] += self.complexity_analyzer.calculate_cyclomatic_complexity(node)
            elif node.type == "class_definition":
                metrics["classes"] += 1
            elif node.type == "import_statement":
                metrics["imports"] += 1
            elif node.type == "identifier":
                metrics["variables"] += 1
            
            for child in node.children:
                count_elements(child)
        
        count_elements(root_node)
        
        self.file_metrics[file_path] = metrics
    
    def extract_syntax_elements(self, node: Node, source_code_bytes: bytes, 
                               file_path: str, parent_node: Optional[Node] = None, parent_id: Optional[str] = None) -> str:
        """構文要素を再帰的に抽出"""
        node_text = source_code_bytes[node.start_byte:node.end_byte].decode('utf8')
        node_type = self.determine_node_type(node, parent_node)
        node_name = self.generate_node_name(node, node_type, node_text)
        
        node_id = f"{node_type.value}_{self.node_counter}"
        self.node_counter += 1
        
        # 複雑性スコアの計算
        complexity_score = 0.0
        if node_type in [NodeType.FUNCTION, NodeType.CLASS]:
            complexity_score = self.complexity_analyzer.calculate_cyclomatic_complexity(node)
        
        # プロパティの作成
        properties = {
            "type": node.type,
            "text": node_text[:500] if len(node_text) > 500 else node_text,
            "start_byte": node.start_byte,
            "end_byte": node.end_byte,
            "start_point": {"row": node.start_point[0], "column": node.start_point[1]},
            "end_point": {"row": node.end_point[0], "column": node.end_point[1]},
            "file_path": file_path,
            "complexity_score": complexity_score
        }
        
        # 特殊なノードタイプに応じた追加プロパティ
        if node_type == NodeType.FUNCTION:
            properties.update(self.extract_function_properties(node, node_text))
        elif node_type == NodeType.CLASS:
            properties.update(self.extract_class_properties(node, node_text))
        elif node_type == NodeType.IMPORT:
            properties.update(self.extract_import_properties(node, node_text))
        
        # ノードの作成
        syntax_node = SyntaxNode(
            node_id=node_id,
            node_type=node_type,
            name=node_name,
            text=node_text,
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            line_start=node.start_point[0],
            line_end=node.end_point[0],
            properties=properties,
            parent_id=parent_id,
            complexity_score=complexity_score
        )
        
        self.syntax_nodes.append(syntax_node)
        
        # 親子関係の作成
        if parent_id:
            self.syntax_relations.append(SyntaxRelation(
                source_id=parent_id,
                target_id=node_id,
                relation_type=RelationType.CONTAINS,
                properties={}
            ))
        
        # 子ノードの処理と特殊関係の抽出
        for child in node.children:
            child_id = self.extract_syntax_elements(child, source_code_bytes, file_path, parent_node=node, parent_id=node_id)
            self.extract_advanced_relationships(node, child, node_id, child_id, node_text)
        
        return node_id
    
    def determine_node_type(self, node: Node, parent_node: Optional[Node] = None) -> NodeType:
        """ノードタイプを判定"""
        node_type = node.type

        # コンテキストに応じた判定
        if node_type == "identifier" and parent_node and parent_node.type == "parameters":
            return NodeType.PARAMETER
        
        type_mapping = {
            "module": NodeType.MODULE,
            "class_definition": NodeType.CLASS,
            "function_definition": NodeType.FUNCTION,
            "import_statement": NodeType.IMPORT,
            "call": NodeType.CALL,
            "assignment": NodeType.ASSIGNMENT,
            "attribute": NodeType.ATTRIBUTE,
            "string": NodeType.STRING,
            "number": NodeType.NUMBER,
            "comment": NodeType.COMMENT,
            "identifier": NodeType.VARIABLE,
            "parameter": NodeType.PARAMETER, # Note: This handles cases where the node itself is 'parameter'
            "decorator": NodeType.DECORATOR,
            "annotation": NodeType.ANNOTATION,
            "try_statement": NodeType.EXCEPTION,
            "for_statement": NodeType.LOOP,
            "while_statement": NodeType.LOOP,
            "if_statement": NodeType.CONDITION,
            "elif_clause": NodeType.CONDITION,
            "else_clause": NodeType.CONDITION
        }
        
        return type_mapping.get(node_type, NodeType.VARIABLE)
    
    def generate_node_name(self, node: Node, node_type: NodeType, node_text: str) -> str:
        """ノード名を生成"""
        if node_type == NodeType.FUNCTION:
            name_node = node.child_by_field_name("name")
            if name_node:
                return name_node.text.decode('utf8')
        elif node_type == NodeType.CLASS:
            name_node = node.child_by_field_name("name")
            if name_node:
                return name_node.text.decode('utf8')
        elif node_type == NodeType.IMPORT:
            return self.extract_import_name(node_text)
        elif node_type == NodeType.CALL:
            return self.extract_call_name(node_text)
        elif node_type == NodeType.VARIABLE:
            return node_text
        elif node_type == NodeType.DECORATOR:
            return self.extract_decorator_name(node_text)
        
        return node_text[:50] if len(node_text) > 50 else node_text
    
    def extract_function_properties(self, node: Node, node_text: str) -> Dict[str, Any]:
        """関数の追加プロパティを抽出"""
        properties = {}
        
        # パラメータの詳細抽出
        parameters_node = node.child_by_field_name("parameters")
        if parameters_node:
            parameters = []
            for param in parameters_node.children:
                if param.type == "identifier":
                    param_info = {
                        "name": param.text.decode('utf8'),
                        "type": "unknown",
                        "default": None,
                        "annotation": None
                    }
                    
                    # 型注釈の抽出
                    if hasattr(param, 'child_by_field_name'):
                        type_node = param.child_by_field_name("type")
                        if type_node:
                            param_info["type"] = type_node.text.decode('utf8')
                    
                    parameters.append(param_info)
            properties["parameters"] = parameters
        
        # 戻り値の型注釈
        return_type_node = node.child_by_field_name("return_type")
        if return_type_node:
            properties["return_type"] = return_type_node.text.decode('utf8')
        
        # デコレータの抽出
        decorators = []
        for child in node.children:
            if child.type == "decorator":
                decorators.append(child.text.decode('utf8'))
        if decorators:
            properties["decorators"] = decorators
        
        return properties
    
    def extract_class_properties(self, node: Node, node_text: str) -> Dict[str, Any]:
        """クラスの追加プロパティを抽出"""
        properties = {}
        
        # 継承クラスの抽出
        inheritance_node = node.child_by_field_name("superclasses")
        if inheritance_node:
            superclasses = []
            for superclass in inheritance_node.children:
                if superclass.type == "identifier":
                    superclasses.append(superclass.text.decode('utf8'))
            properties["superclasses"] = superclasses
        
        # クラスメソッドの抽出
        methods = []
        body_node = node.child_by_field_name("body")
        if body_node:
            for child in body_node.children:
                if child.type == "function_definition":
                    name_node = child.child_by_field_name("name")
                    if name_node:
                        methods.append(name_node.text.decode('utf8'))
        properties["methods"] = methods
        
        return properties
    
    def extract_import_properties(self, node: Node, node_text: str) -> Dict[str, Any]:
        """インポートの追加プロパティを抽出"""
        properties = {}
        
        import_name = self.extract_import_name(node_text)
        properties["import_name"] = import_name
        
        # インポートタイプの判定
        if "from" in node_text:
            properties["import_type"] = "from_import"
        else:
            properties["import_type"] = "direct_import"
        
        return properties
    
    def extract_import_name(self, import_text: str) -> str:
        """インポート名を抽出"""
        lines = import_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('import '):
                return line[7:].split()[0]
            elif line.startswith('from '):
                parts = line.split(' import ')
                if len(parts) > 1:
                    return parts[1].split()[0]
        return import_text
    
    def extract_call_name(self, call_text: str) -> str:
        """関数呼び出し名を抽出"""
        if '(' in call_text:
            return call_text.split('(')[0].strip()
        return call_text
    
    def extract_decorator_name(self, decorator_text: str) -> str:
        """デコレータ名を抽出"""
        if decorator_text.startswith('@'):
            return decorator_text[1:].split('(')[0]
        return decorator_text
    
    def extract_advanced_relationships(self, parent: Node, child: Node, 
                                     parent_id: str, child_id: str, parent_text: str):
        """高度な関係を抽出"""
        parent_type = parent.type
        child_type = child.type
        
        # 関数呼び出し関係
        if parent_type == "call" and child_type == "identifier":
            self.syntax_relations.append(SyntaxRelation(
                source_id=parent_id,
                target_id=child_id,
                relation_type=RelationType.CALLS,
                properties={}
            ))
        
        # 変数使用関係
        elif parent_type == "assignment" and child_type == "identifier":
            self.syntax_relations.append(SyntaxRelation(
                source_id=parent_id,
                target_id=child_id,
                relation_type=RelationType.ASSIGNS,
                properties={}
            ))
        
        # 属性アクセス関係
        elif parent_type == "attribute" and child_type == "identifier":
            self.syntax_relations.append(SyntaxRelation(
                source_id=parent_id,
                target_id=child_id,
                relation_type=RelationType.HAS_ATTRIBUTE,
                properties={}
            ))
    
    def enhance_with_llm(self, file_path: str) -> None:
        """LLMによるコード理解の強化"""
        if not self.llm_analyzer:
            return
        
        logger.info("LLMによるコード理解強化を開始...")
        
        for node in self.syntax_nodes:
            if node.properties.get("file_path") == file_path:
                if node.node_type == NodeType.FUNCTION:
                    analysis = self.generate_llm_description(node)
                    if analysis:
                        node.llm_insights = analysis
                        node.properties["llm_analysis"] = analysis
                elif node.node_type == NodeType.CLASS:
                    analysis = self.generate_llm_description(node)
                    if analysis:
                        node.llm_insights = analysis
                        node.properties["llm_analysis"] = analysis
    
    def generate_llm_description(self, node: SyntaxNode) -> Optional[Dict[str, Any]]:
        """LLMによる説明を生成"""
        try:
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", "あなたはPythonコードの専門家です。"),
                ("human", "以下のPythonコードの{node_type}について分析してください：\n\n```python\n{code_text}\n```\n\n簡潔で分かりやすい説明を日本語で提供してください。")
            ])
            
            chain = prompt_template | self.llm_analyzer | StrOutputParser()

            response_content = chain.invoke({
                "node_type": node.node_type.value,
                "code_text": node.text
            })
            
            return {"description": response_content.strip()}
        
        except Exception as e:
            logger.error(f"LLM説明生成エラー: {e}")
            return None
    
    def store_to_neo4j(self) -> None:
        """Neo4jにデータを格納（最適化版）"""
        logger.info("Neo4jへのデータ格納を開始...")
        
        driver = GraphDatabase.driver(self.neo4j_uri, 
                                    auth=(self.neo4j_user, self.neo4j_password))
        
        try:
            with driver.session(database=self.database_name) as session:
                # 既存データのクリア
                session.run("MATCH (n) DETACH DELETE n")
                logger.info("既存のグラフをクリアしました。")
                
                # ノードの作成（バッチ処理）
                self._create_advanced_nodes_optimized(session)
                
                # リレーションの作成（最適化版）
                self._create_advanced_relationships(session)
                
                # クエリ最適化のための統計情報更新
                self._optimize_queries(session)
                
                # 統計情報の表示
                self._display_advanced_statistics(session)
        
        except Exception as e:
             logger.error(f"Neo4jへの格納中にエラーが発生しました: {e}")
             logger.error(f"データベース '{self.database_name}' が存在し、Neo4jが実行されていることを確認してください。")
             raise

        finally:
            driver.close()
        
        logger.info("Neo4jへのデータ格納が完了しました。")
    
    def _create_advanced_nodes_optimized(self, session):
        """高度なノードを作成（最適化版）"""
        # ノードタイプ別にグループ化
        nodes_by_type = {}
        for node in self.syntax_nodes:
            node_type = node.node_type.value
            if node_type not in nodes_by_type:
                nodes_by_type[node_type] = []
            nodes_by_type[node_type].append(node)
        
        total_nodes = len(self.syntax_nodes)
        logger.info(f"ノード作成開始: {total_nodes}個")
        
        # タイプ別にバッチ処理
        for node_type, nodes in nodes_by_type.items():
            logger.info(f"{node_type}ノード作成中: {len(nodes)}個")
            
            # バッチサイズを設定（ノードタイプに応じて調整）
            batch_size = 50 if node_type in ["Variable", "Comment"] else 100
            
            for i in range(0, len(nodes), batch_size):
                batch = nodes[i:i + batch_size]
                self._create_nodes_batch(session, batch, node_type)
        
        logger.info(f"{total_nodes}個のノードを作成しました。")
    
    def _create_nodes_batch(self, session, nodes, node_type):
        """ノードのバッチ作成"""
        batch_params = []
        
        for node in nodes:
            # 基本プロパティ
            properties = {
                "id": node.node_id,
                "name": node.name,
                "text": node.properties["text"],
                "start_byte": node.start_byte,
                "end_byte": node.end_byte,
                "line_start": node.line_start,
                "line_end": node.line_end,
                "file_path": node.properties["file_path"],
                "complexity_score": node.complexity_score
            }
            
            # LLM分析結果の追加
            if node.llm_insights:
                properties["llm_analysis"] = json.dumps(node.llm_insights, ensure_ascii=False)
            
            # 追加プロパティの統合
            for key, value in node.properties.items():
                if key not in ["text", "file_path"]:
                    if isinstance(value, (list, dict)):
                        properties["llm_analysis"] = json.dumps(value, ensure_ascii=False)
                    else:
                        properties[key] = value
            
            batch_params.append(properties)
        
        # バッチ処理用のCypherクエリ
        cypher = f"""
        UNWIND $batch AS node
        CREATE (n:{node_type} {{
            id: node.id,
            name: node.name,
            text: node.text,
            start_byte: node.start_byte,
            end_byte: node.end_byte,
            line_start: node.line_start,
            line_end: node.line_end,
            file_path: node.file_path,
            complexity_score: node.complexity_score
        }})
        """
        
        try:
            session.run(cypher, {"batch": batch_params})
        except Exception as e:
            logger.error(f"バッチノード作成エラー ({node_type}): {e}")
            # 個別作成にフォールバック
            for node in nodes:
                self._create_single_node(session, node)
    
    def _create_single_node(self, session, node):
        """単一ノードを作成（フォールバック用）"""
        try:
            properties = {
                "id": node.node_id,
                "name": node.name,
                "text": node.properties["text"],
                "start_byte": node.start_byte,
                "end_byte": node.end_byte,
                "line_start": node.line_start,
                "line_end": node.line_end,
                "file_path": node.properties["file_path"],
                "complexity_score": node.complexity_score
            }
            
            # LLM分析結果の追加
            if node.llm_insights:
                properties["llm_analysis"] = json.dumps(node.llm_insights, ensure_ascii=False)
            
            # 追加プロパティの統合
            for key, value in node.properties.items():
                if key not in ["text", "file_path"]:
                    if isinstance(value, (list, dict)):
                        properties[key] = json.dumps(value, ensure_ascii=False)
                    else:
                        properties[key] = value
            
            cypher = f"""
            CREATE (n:{node.node_type.value} {{
                {', '.join([f'{k}: ${k}' for k in properties.keys()])}
            }})
            """
            
            session.run(cypher, properties)
        except Exception as e:
            logger.error(f"単一ノード作成エラー: {node.node_id}: {e}")
    
    def _create_advanced_relationships(self, session):
        """高度なリレーションを作成"""
        for relation in self.syntax_relations:
            cypher = f"""
            MATCH (source), (target)
            WHERE source.id = $source_id AND target.id = $target_id
            CREATE (source)-[r:{relation.relation_type.value} {{
                weight: $weight
            }}]->(target)
            """
            
            session.run(cypher, {
                "source_id": relation.source_id,
                "target_id": relation.target_id,
                "weight": relation.weight
            })
        
        logger.info(f"{len(self.syntax_relations)}個のリレーションを作成しました。")
    
    def _optimize_queries(self, session):
        """クエリ最適化のための統計情報更新"""
        # ノードタイプ別の統計を更新
        session.run("""
        MATCH (n)
        WITH labels(n)[0] as type, count(n) as count
        MERGE (t:NodeType {{name: type}})
        SET t.count = count
        """)
        
        # リレーションタイプ別の統計を更新
        session.run("""
        MATCH ()-[r]->()
        WITH type(r) as type, count(r) as count
        MERGE (rt:RelationType {{name: type}})
        SET rt.count = count
        """)
        
        # 複雑性スコアの統計を更新
        session.run("""
        MATCH (n)
        WHERE n.complexity_score > 0
        WITH avg(n.complexity_score) as avg_complexity, 
               max(n.complexity_score) as max_complexity,
               min(n.complexity_score) as min_complexity
        MERGE (cs:ComplexityScore {{name: "Average"}})
        SET cs.avg = avg_complexity, cs.max = max_complexity, cs.min = min_complexity
        """)
    
    def _display_advanced_statistics(self, session):
        """高度な統計情報を表示"""
        # ノードタイプ別の統計
        result = session.run("""
        MATCH (n)
        RETURN labels(n)[0] as type, count(n) as count
        ORDER BY count DESC
        """)
        
        logger.info("=== ノード統計 ===")
        for record in result:
            logger.info(f"{record['type']}: {record['count']}個")
        
        # リレーションタイプ別の統計
        result = session.run("""
        MATCH ()-[r]->()
        RETURN type(r) as type, count(r) as count
        ORDER BY count DESC
        """)
        
        logger.info("=== リレーション統計 ===")
        for record in result:
            logger.info(f"{record['type']}: {record['count']}個")
        
        # 複雑性スコアの統計
        result = session.run("""
        MATCH (n)
        WHERE n.complexity_score > 0
        RETURN avg(n.complexity_score) as avg_complexity, 
               max(n.complexity_score) as max_complexity,
               min(n.complexity_score) as min_complexity
        """)
        
        for record in result:
            logger.info(f"=== 複雑性統計 ===")
            logger.info(f"平均複雑性: {record['avg_complexity']:.2f}")
            logger.info(f"最大複雑性: {record['max_complexity']}")
            logger.info(f"最小複雑性: {record['min_complexity']}")

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Pythonコードを解析してNeo4jに格納します。")
    parser.add_argument("file_path", help="解析対象のPythonファイルへのパス")
    parser.add_argument("--db-name", default="treesitter", help="使用するNeo4jデータベース名")
    parser.add_argument("--no-llm", action="store_true", help="LLMによる分析を無効にする")
    args = parser.parse_args()

    # Neo4j接続情報
    neo4j_uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
    # 環境変数は NEO4J_USER と NEO4J_USERNAME の両方に対応
    neo4j_user = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME") or "neo4j"
    neo4j_password = os.getenv("NEO4J_PASSWORD")

    if not neo4j_password:
        logger.error("NEO4J_PASSWORD環境変数が設定されていません。")
        return

    # 高度なTree-sitter Neo4jビルダーの作成
    builder = TreeSitterNeo4jAdvancedBuilder(
        neo4j_uri, neo4j_user, neo4j_password,
        database_name=args.db_name,
        enable_llm=not args.no_llm
    )
    
    # ファイル解析
    if not os.path.exists(args.file_path):
        logger.error(f"指定されたファイルが見つかりません: {args.file_path}")
        return

    builder.analyze_file(args.file_path)
    
    # Neo4jへの格納
    builder.store_to_neo4j()
    
    logger.info("処理が完了しました。")

if __name__ == "__main__":
    main() 