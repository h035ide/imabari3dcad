import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Node
from neo4j import GraphDatabase
import os
from typing import Dict, List, Any, Optional, Tuple
import json
from dataclasses import dataclass
from enum import Enum

# LLM関連のインポート（必要に応じて）
try:
    import openai
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    print("警告: OpenAIライブラリが利用できません。LLM機能は無効化されます。")

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

@dataclass
class SyntaxRelation:
    """構文関係の情報を格納するデータクラス"""
    source_id: str
    target_id: str
    relation_type: RelationType
    properties: Dict[str, Any]

class TreeSitterNeo4jBuilder:
    """Tree-sitterの構文解析結果をNeo4jに格納するクラス"""
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str, 
                 database_name: str = "treesitter_graph"):
        """初期化
        
        Args:
            neo4j_uri: Neo4jのURI
            neo4j_user: ユーザー名
            neo4j_password: パスワード
            database_name: データベース名
        """
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.database_name = database_name
        
        # Tree-sitterセットアップ
        self.py_language = Language(tspython.language())
        self.parser = Parser()
        self.parser.set_language(self.py_language)
        
        # ノードとリレーションの格納
        self.syntax_nodes: List[SyntaxNode] = []
        self.syntax_relations: List[SyntaxRelation] = []
        self.node_counter = 0
        
        # LLM設定
        self.llm_available = LLM_AVAILABLE
        if self.llm_available:
            self.setup_llm()
    
    def setup_llm(self):
        """LLMの設定"""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                openai.api_key = api_key
                print("LLM機能が有効化されました")
            else:
                self.llm_available = False
                print("警告: OPENAI_API_KEYが設定されていません。LLM機能は無効化されます。")
        except Exception as e:
            self.llm_available = False
            print(f"LLM設定エラー: {e}")
    
    def analyze_file(self, file_path: str) -> None:
        """ファイルを解析してNeo4jに格納
        
        Args:
            file_path: 解析対象のファイルパス
        """
        print(f"ファイル解析開始: {file_path}")
        
        # ファイル読み込み
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()
        
        # Tree-sitter解析
        source_code_bytes = bytes(source_code, "utf8")
        tree = self.parser.parse(source_code_bytes)
        root_node = tree.root_node
        
        # 構文要素の抽出
        self.extract_syntax_elements(root_node, source_code_bytes, file_path)
        
        # LLMによる理解強化
        if self.llm_available:
            self.enhance_with_llm()
        
        # Neo4jへの格納
        self.store_to_neo4j()
        
        print(f"ファイル解析完了: {file_path}")
    
    def extract_syntax_elements(self, node: Node, source_code_bytes: bytes, 
                               file_path: str, parent_id: Optional[str] = None) -> str:
        """構文要素を再帰的に抽出
        
        Args:
            node: Tree-sitterノード
            source_code_bytes: ソースコードのバイトデータ
            file_path: ファイルパス
            parent_id: 親ノードのID
            
        Returns:
            作成されたノードのID
        """
        # ノードテキストの取得
        node_text = source_code_bytes[node.start_byte:node.end_byte].decode('utf8')
        
        # ノードタイプの判定
        node_type = self.determine_node_type(node)
        
        # ノード名の生成
        node_name = self.generate_node_name(node, node_type, node_text)
        
        # ノードIDの生成
        node_id = f"{node_type.value}_{self.node_counter}"
        self.node_counter += 1
        
        # プロパティの作成
        properties = {
            "type": node.type,
            "text": node_text[:200] if len(node_text) > 200 else node_text,  # 長いテキストは切り詰め
            "start_byte": node.start_byte,
            "end_byte": node.end_byte,
            "start_point": {"row": node.start_point[0], "column": node.start_point[1]},
            "end_point": {"row": node.end_point[0], "column": node.end_point[1]},
            "file_path": file_path
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
            parent_id=parent_id
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
        
        # 子ノードの処理
        for child in node.children:
            child_id = self.extract_syntax_elements(child, source_code_bytes, file_path, node_id)
            
            # 特殊な関係の抽出
            self.extract_special_relationships(node, child, node_id, child_id, node_text)
        
        return node_id
    
    def determine_node_type(self, node: Node) -> NodeType:
        """ノードタイプを判定"""
        node_type = node.type
        
        if node_type == "module":
            return NodeType.MODULE
        elif node_type == "class_definition":
            return NodeType.CLASS
        elif node_type == "function_definition":
            return NodeType.FUNCTION
        elif node_type == "import_statement":
            return NodeType.IMPORT
        elif node_type == "call":
            return NodeType.CALL
        elif node_type == "assignment":
            return NodeType.ASSIGNMENT
        elif node_type == "attribute":
            return NodeType.ATTRIBUTE
        elif node_type == "string":
            return NodeType.STRING
        elif node_type == "number":
            return NodeType.NUMBER
        elif node_type == "comment":
            return NodeType.COMMENT
        elif node_type == "identifier":
            return NodeType.VARIABLE
        elif node_type == "parameter":
            return NodeType.PARAMETER
        else:
            return NodeType.VARIABLE  # デフォルト
    
    def generate_node_name(self, node: Node, node_type: NodeType, node_text: str) -> str:
        """ノード名を生成"""
        if node_type == NodeType.FUNCTION:
            # 関数名を抽出
            name_node = node.child_by_field_name("name")
            if name_node:
                return name_node.text.decode('utf8')
        elif node_type == NodeType.CLASS:
            # クラス名を抽出
            name_node = node.child_by_field_name("name")
            if name_node:
                return name_node.text.decode('utf8')
        elif node_type == NodeType.IMPORT:
            # インポート名を抽出
            return self.extract_import_name(node_text)
        elif node_type == NodeType.VARIABLE:
            return node_text
        elif node_type == NodeType.CALL:
            # 関数呼び出し名を抽出
            return self.extract_call_name(node_text)
        
        return node_text[:50] if len(node_text) > 50 else node_text
    
    def extract_function_properties(self, node: Node, node_text: str) -> Dict[str, Any]:
        """関数の追加プロパティを抽出"""
        properties = {}
        
        # パラメータの抽出
        parameters_node = node.child_by_field_name("parameters")
        if parameters_node:
            parameters = []
            for param in parameters_node.children:
                if param.type == "identifier":
                    parameters.append(param.text.decode('utf8'))
            properties["parameters"] = parameters
        
        # 戻り値の型注釈
        return_type_node = node.child_by_field_name("return_type")
        if return_type_node:
            properties["return_type"] = return_type_node.text.decode('utf8')
        
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
        
        return properties
    
    def extract_import_properties(self, node: Node, node_text: str) -> Dict[str, Any]:
        """インポートの追加プロパティを抽出"""
        properties = {}
        
        # インポート名の抽出
        import_name = self.extract_import_name(node_text)
        properties["import_name"] = import_name
        
        return properties
    
    def extract_import_name(self, import_text: str) -> str:
        """インポート名を抽出"""
        # 簡単な実装 - 実際はより複雑な解析が必要
        lines = import_text.split('\n')
        for line in lines:
            if 'import' in line:
                parts = line.split('import')
                if len(parts) > 1:
                    return parts[1].strip().split()[0]
        return import_text
    
    def extract_call_name(self, call_text: str) -> str:
        """関数呼び出し名を抽出"""
        # 簡単な実装
        if '(' in call_text:
            return call_text.split('(')[0].strip()
        return call_text
    
    def extract_special_relationships(self, parent: Node, child: Node, 
                                    parent_id: str, child_id: str, parent_text: str):
        """特殊な関係を抽出"""
        parent_type = parent.type
        child_type = child.type
        
        # 関数呼び出し関係
        if parent_type == "call" and child_type == "identifier":
            # 呼び出し元の関数を特定（簡易版）
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
    
    def enhance_with_llm(self):
        """LLMによるコード理解の強化"""
        if not self.llm_available:
            return
        
        print("LLMによるコード理解強化を開始...")
        
        for node in self.syntax_nodes:
            if node.node_type in [NodeType.FUNCTION, NodeType.CLASS]:
                # LLMによる説明の生成
                description = self.generate_llm_description(node)
                if description:
                    node.properties["llm_description"] = description
    
    def generate_llm_description(self, node: SyntaxNode) -> Optional[str]:
        """LLMによる説明を生成"""
        try:
            prompt = f"""
以下のPythonコードの{node.node_type.value}について説明してください：

```python
{node.text}
```

簡潔で分かりやすい説明を日本語で提供してください。
"""
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "あなたはPythonコードの専門家です。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"LLM説明生成エラー: {e}")
            return None
    
    def store_to_neo4j(self):
        """Neo4jにデータを格納"""
        print("Neo4jへのデータ格納を開始...")
        
        driver = GraphDatabase.driver(self.neo4j_uri, 
                                    auth=(self.neo4j_user, self.neo4j_password))
        
        try:
            # データベースの存在確認
            self._ensure_database_exists(driver)
            
            with driver.session(database=self.database_name) as session:
                # 既存データのクリア
                session.run("MATCH (n) DETACH DELETE n")
                print("既存のグラフをクリアしました。")
                
                # ノードの作成
                self._create_nodes(session)
                
                # リレーションの作成
                self._create_relationships(session)
                
                # 統計情報の表示
                self._display_statistics(session)
        
        finally:
            driver.close()
        
        print("Neo4jへのデータ格納が完了しました。")
    
    def _ensure_database_exists(self, driver):
        """データベースの存在確認と作成"""
        try:
            with driver.session(database="system") as session:
                result = session.run("SHOW DATABASES")
                databases = [record["name"] for record in result]
                
                if self.database_name not in databases:
                    print(f"データベース '{self.database_name}' を作成しています...")
                    session.run(f"CREATE DATABASE {self.database_name}")
                    print(f"データベース '{self.database_name}' が作成されました。")
                else:
                    print(f"データベース '{self.database_name}' は既に存在します。")
        except Exception as e:
            print(f"データベース確認エラー: {e}")
            self.database_name = "neo4j"
    
    def _create_nodes(self, session):
        """ノードを作成"""
        for node in self.syntax_nodes:
            cypher = f"""
            CREATE (n:{node.node_type.value} {{
                id: $id,
                name: $name,
                text: $text,
                start_byte: $start_byte,
                end_byte: $end_byte,
                line_start: $line_start,
                line_end: $line_end,
                file_path: $file_path
            }})
            """
            
            session.run(cypher, {
                "id": node.node_id,
                "name": node.name,
                "text": node.properties["text"],
                "start_byte": node.start_byte,
                "end_byte": node.end_byte,
                "line_start": node.line_start,
                "line_end": node.line_end,
                "file_path": node.properties["file_path"]
            })
        
        print(f"{len(self.syntax_nodes)}個のノードを作成しました。")
    
    def _create_relationships(self, session):
        """リレーションを作成"""
        for relation in self.syntax_relations:
            cypher = f"""
            MATCH (source), (target)
            WHERE source.id = $source_id AND target.id = $target_id
            CREATE (source)-[r:{relation.relation_type.value}]->(target)
            """
            
            session.run(cypher, {
                "source_id": relation.source_id,
                "target_id": relation.target_id
            })
        
        print(f"{len(self.syntax_relations)}個のリレーションを作成しました。")
    
    def _display_statistics(self, session):
        """統計情報を表示"""
        # ノードタイプ別の統計
        result = session.run("""
        MATCH (n)
        RETURN labels(n)[0] as type, count(n) as count
        ORDER BY count DESC
        """)
        
        print("\n=== ノード統計 ===")
        for record in result:
            print(f"{record['type']}: {record['count']}個")
        
        # リレーションタイプ別の統計
        result = session.run("""
        MATCH ()-[r]->()
        RETURN type(r) as type, count(r) as count
        ORDER BY count DESC
        """)
        
        print("\n=== リレーション統計 ===")
        for record in result:
            print(f"{record['type']}: {record['count']}個")

def main():
    """メイン関数"""
    # Neo4j接続情報
    neo4j_uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
    
    # 解析対象ファイル
    target_file = "./evoship/create_test.py"
    
    # Tree-sitter Neo4jビルダーの作成
    builder = TreeSitterNeo4jBuilder(neo4j_uri, neo4j_user, neo4j_password)
    
    # ファイル解析とNeo4j格納
    builder.analyze_file(target_file)
    
    print("処理が完了しました。")

if __name__ == "__main__":
    main() 