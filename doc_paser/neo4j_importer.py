# This script will be used to import the parsed API data into a Neo4j database.
#
# 使用方法:
#   python neo4j_importer.py                    # デフォルトでparsed_api_result_def.jsonを使用
#   python neo4j_importer.py --def-file         # parsed_api_result_def.jsonを使用
#   python neo4j_importer.py --original-file    # parsed_api_result.jsonを使用
#   python neo4j_importer.py --file custom.json # カスタムファイルを使用
#
# 環境変数設定 (.envファイル):
#   NEO4J_URI=bolt://localhost:7687
#   NEO4J_USER=neo4j
#   NEO4J_PASSWORD=password
#   NEO4J_DATABASE=docparser (オプション、デフォルトはdocparser)
#
# 注意: Neo4j 4.0以降では、データベース名を明示的に指定する必要があります。
# "docparser"データベースが存在しない場合は、事前に作成してください。

import os
import sys
import json
import argparse
from neo4j import GraphDatabase
from dotenv import load_dotenv

class Neo4jImporter:
    def __init__(self, uri, user, password, database="docparser"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database

    def close(self):
        self.driver.close()

    def check_and_create_database(self):
        """データベースの存在確認と作成"""
        try:
            with self.driver.session(database="system") as session:
                # データベースの存在確認
                result = session.run("SHOW DATABASES")
                databases = [record["name"] for record in result]
                
                if self.database not in databases:
                    print(f"データベース '{self.database}' が存在しません。作成します...")
                    session.run(f"CREATE DATABASE {self.database}")
                    print(f"データベース '{self.database}' を作成しました。")
                else:
                    print(f"データベース '{self.database}' が存在します。")
                    
        except Exception as e:
            print(f"データベース確認・作成中にエラーが発生しました: {e}")
            print("手動でデータベースを作成するか、既存のデータベース名を指定してください。")
            raise

    def import_data(self, data):
        """メインデータインポート処理"""
        # データベースの確認・作成
        self.check_and_create_database()
        
        with self.driver.session(database=self.database) as session:
            self._import_type_definitions(session, data.get("type_definitions", []))
            self._import_api_entries(session, data.get("api_entries", []))
            self._create_dependency_links(session)
        print(f"Data import completed to database: {self.database}")

    def _import_type_definitions(self, session, type_definitions):
        """型定義のインポート"""
        if not type_definitions:
            return
            
        print("Importing type definitions...")
        query = """
        UNWIND $types as type_data
        MERGE (t:Type {name: type_data.name})
        SET t.description = type_data.description
        """
        session.run(query, types=type_definitions)
        print(f"  - Imported {len(type_definitions)} type definitions")

    def _import_api_entries(self, session, api_entries):
        """APIエントリーのインポート"""
        if not api_entries:
            return
            
        print("Importing API entries...")
        for entry in api_entries:
            if entry.get("entry_type") == "function":
                self._import_function(session, entry)
            elif entry.get("entry_type") == "object_definition":
                self._import_object_definition(session, entry)

    def _import_function(self, session, func_data):
        """関数のインポート"""
        # 関数ノードの作成
        self._create_function_node(session, func_data)
        
        # パラメータの処理
        if func_data.get('params'):
            self._create_function_parameters(session, func_data)
        
        # 戻り値の処理
        if func_data.get('returns'):
            self._create_function_return(session, func_data)
        
        print(f"  - Imported function: {func_data['name']}")

    def _create_function_node(self, session, func_data):
        """関数ノードの作成"""
        query = """
        MERGE (f:Function {name: $name})
        SET f.description = $description, 
            f.category = $category,
            f.implementation_status = $implementation_status, 
            f.notes = $notes
        """
        session.run(query, 
                   name=func_data['name'],
                   description=func_data.get('description', ''),
                   category=func_data.get('category', ''),
                   implementation_status=func_data.get('implementation_status', ''),
                   notes=func_data.get('notes', ''))

    def _create_function_parameters(self, session, func_data):
        """関数パラメータの作成"""
        for param_data in func_data['params']:
            self._create_parameter(session, func_data['name'], param_data, 'function')

    def _create_function_return(self, session, func_data):
        """関数の戻り値の作成"""
        query = """
        MATCH (f:Function {name: $func_name})
        MERGE (rt:Type {name: $return_type})
        MERGE (f)-[:RETURNS]->(rt)
        """
        session.run(query, 
                   func_name=func_data['name'], 
                   return_type=func_data['returns'].get('type'))

    def _import_object_definition(self, session, obj_data):
        """オブジェクト定義のインポート"""
        # オブジェクト定義ノードの作成
        self._create_object_definition_node(session, obj_data)
        
        # プロパティの処理
        if obj_data.get('properties'):
            self._create_object_properties(session, obj_data)
        
        print(f"  - Imported object definition: {obj_data['name']}")

    def _create_object_definition_node(self, session, obj_data):
        """オブジェクト定義ノードの作成"""
        query = """
        MERGE (od:ObjectDefinition {name: $name})
        SET od.description = $description, 
            od.category = $category, 
            od.notes = $notes
        """
        session.run(query, 
                   name=obj_data['name'],
                   description=obj_data.get('description', ''),
                   category=obj_data.get('category', ''),
                   notes=obj_data.get('notes', ''))

    def _create_object_properties(self, session, obj_data):
        """オブジェクトプロパティの作成"""
        for prop_data in obj_data['properties']:
            self._create_parameter(session, obj_data['name'], prop_data, 'object')

    def _create_parameter(self, session, parent_name, param_data, parent_type):
        """パラメータノードの作成（関数とオブジェクトの両方で使用）"""
        if parent_type == 'function':
            query = """
            MATCH (f:Function {name: $parent_name})
            MERGE (p:Parameter {name: $param_name, parent_function: $parent_name})
            SET p.description = $param_description, p.is_required = $param_required
            MERGE (f)-[r:HAS_PARAMETER]->(p)
            SET r.position = $param_position
            
            WITH p
            OPTIONAL MATCH (od:ObjectDefinition {name: $param_type})
            MERGE (t:Type {name: $param_type})
            WITH p, COALESCE(od, t) as type_node
            MERGE (p)-[:HAS_TYPE]->(type_node)
            """
            
            session.run(query, 
                      parent_name=parent_name,
                      param_name=param_data['name'],
                      param_description=param_data.get('description', ''),
                      param_required=param_data.get('is_required', False),
                      param_position=param_data.get('position', 0),
                      param_type=param_data['type'])
        else:  # object
            query = """
            MATCH (od:ObjectDefinition {name: $parent_name})
            MERGE (p:Parameter {name: $param_name, parent_object: $parent_name})
            SET p.description = $param_description
            MERGE (od)-[:HAS_PROPERTY]->(p)
            
            WITH p
            OPTIONAL MATCH (prop_od:ObjectDefinition {name: $param_type})
            MERGE (t:Type {name: $param_type})
            WITH p, COALESCE(prop_od, t) as type_node
            MERGE (p)-[:HAS_TYPE]->(type_node)
            """
            
            session.run(query, 
                      parent_name=parent_name,
                      param_name=param_data['name'],
                      param_description=param_data.get('description', ''),
                      param_type=param_data['type'])

    def _create_dependency_links(self, session):
        """関数間の依存関係リンクの作成"""
        print("Creating function dependency links...")
        query = """
        MATCH (func_a:Function)-[:RETURNS]->(obj:ObjectDefinition)
        MATCH (func_b:Function)-[:HAS_PARAMETER]->(param:Parameter)-[:HAS_TYPE]->(obj)
        MERGE (func_a)-[r:FEEDS_INTO]->(func_b)
        SET r.via_object = obj.name
        """
        try:
            result = session.run(query)
            summary = result.consume()
            print(f"  - Created {summary.counters.relationships_created} 'FEEDS_INTO' relationships.")
        except Exception as e:
            print(f"  - Warning: Could not create dependency links: {e}")

def load_environment():
    """環境変数の読み込み"""
    load_dotenv()
    
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "docparser")
    
    if not all([uri, user, password]):
        raise ValueError("NEO4J_URI, NEO4J_USER (or NEO4J_USERNAME), and NEO4J_PASSWORD must be set in the .env file.")
    
    return uri, user, password, database

def load_api_data(file_path=None, use_def_file=True):
    """APIデータの読み込み
    
    Args:
        file_path (str, optional): カスタムファイルパス。指定された場合はそのファイルを使用
        use_def_file (bool): Trueの場合はparsed_api_result_def.json、Falseの場合はparsed_api_result.jsonを使用
    
    Returns:
        dict: 読み込まれたAPIデータ
    """
    if file_path is None:
        if use_def_file:
            file_path = 'doc_paser/parsed_api_result_def.json'
        else:
            file_path = 'doc_paser/parsed_api_result.json'
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"Successfully loaded API data from: {file_path}")
            return data
    except FileNotFoundError:
        raise FileNotFoundError(f"API data file not found: {file_path}. Please run doc_paser.py first.")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in {file_path}: {e}")
    except Exception as e:
        raise Exception(f"Error reading {file_path}: {e}")

def main():
    """メイン処理"""
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(
        description='Neo4jにAPIデータをインポートするスクリプト',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python neo4j_importer.py                    # デフォルトでparsed_api_result_def.jsonを使用
  python neo4j_importer.py --def-file         # parsed_api_result_def.jsonを使用
  python neo4j_importer.py --original-file    # parsed_api_result.jsonを使用
  python neo4j_importer.py --file custom.json # カスタムファイルを使用
        """
    )
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--def-file', action='store_true', 
                      help='parsed_api_result_def.jsonを使用（デフォルト）')
    group.add_argument('--original-file', action='store_true',
                      help='parsed_api_result.jsonを使用')
    group.add_argument('--file', type=str, metavar='FILE',
                      help='指定されたファイルを使用')
    
    args = parser.parse_args()
    
    print("Neo4j Importer script started.")
    
    try:
        # 環境変数の読み込み
        uri, user, password, _ = load_environment()
        database = "docparser"
        print(f"Connecting to Neo4j database: {database}")
        if database == "docparser":
            print("  → APIドキュメント解析データを格納する専用データベースを使用します")
        
        # ファイル選択の決定
        if args.file:
            # カスタムファイルパスが指定された場合
            api_data = load_api_data(file_path=args.file)
        elif args.original_file:
            # オリジナルファイルを使用する場合
            api_data = load_api_data(use_def_file=False)
        else:
            # デフォルトでparsed_api_result_def.jsonを使用
            api_data = load_api_data(use_def_file=True)
        
        # データのインポート
        importer = Neo4jImporter(uri, user, password, database)
        importer.import_data(api_data)
        
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)
    finally:
        if 'importer' in locals():
            importer.close()
    
    print("Neo4j Importer script finished.")

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    print(f"プロジェクトルートパス: {project_root}")
    main()
