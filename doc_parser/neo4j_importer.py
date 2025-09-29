# This script will be used to import the parsed API data into a Neo4j database.
#
# 使用方法:
#   python neo4j_importer.py  # デフォルトでparsed_api_result_def.jsonを使用
#   python neo4j_importer.py --def-file  # parsed_api_result_def.jsonを使用
#   python neo4j_importer.py --original-file  # parsed_api_result.jsonを使用
#   python neo4j_importer.py --file custom.json  # カスタムファイルを使用
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
from typing import Optional, Dict, Any

from neo4j import GraphDatabase
from dotenv import load_dotenv


class Neo4jImporter:
    def __init__(
        self,
        uri,
        user,
        password,
        database="docparser",
        create_llamaindex_format: bool = False,
    ):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database
        self.create_llamaindex_format = create_llamaindex_format

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
                    session.run("CREATE DATABASE docparser")
                    print(f"データベース '{self.database}' を作成しました。")
                else:
                    print(f"データベース '{self.database}' が存在します。")
        except Exception as e:
            print(f"データベース確認・作成中にエラーが発生しました: {e}")
            print("手動でデータベースを作成するか、既存のデータベース名を指定してください。")
            raise

    def import_data(self, data):
        """メインデータインポート処理"""
        try:
            # データベースの確認・作成
            self.check_and_create_database()

            with self.driver.session(database=self.database) as session:
                if self.create_llamaindex_format:
                    print("Clearing existing LlamaIndex data...")
                    self._clear_llamaindex_data(session)

                print("Starting data import process...")
                self._import_type_definitions(
                    session, data.get("type_definitions", [])
                )
                self._import_api_entries(session, data.get("api_entries", []))
                self._create_dependency_links(session)

                if self.create_llamaindex_format:
                    print("Creating LlamaIndex structures...")
                    self._create_llamaindex_structures(session)

            print(f"✅ Data import completed successfully to database: {self.database}")
        except Exception as e:
            print(f"❌ Data import failed: {e}")
            raise

    def _import_type_definitions(self, session, type_definitions):
        """型定義のインポート"""
        if not type_definitions:
            return

        print("Importing type definitions...")
        for type_data in type_definitions:
            # 統一メソッドを使用してTypeノードを作成
            self._ensure_type_node(
                session,
                type_data.get('name', ''),
                type_data.get('description', '')
            )

            # LlamaIndex形式の作成
            if self.create_llamaindex_format:
                self._create_llamaindex_type(session, type_data)

        print(f"  - Imported {len(type_definitions)} type definitions")

    def _import_api_entries(self, session, api_entries):
        """APIエントリーのインポート"""
        if not api_entries:
            return

        print("Importing API entries...")

        # まずObjectDefinitionを先に作成（関数の戻り値で参照されるため）
        object_definitions = [
            entry for entry in api_entries
            if entry.get("entry_type") == "object_definition"
        ]
        functions = [
            entry for entry in api_entries
            if entry.get("entry_type") == "function"
        ]

        print(f"  - Importing {len(object_definitions)} object definitions "
              f"first...")
        for entry in object_definitions:
            self._import_object_definition(session, entry)

        print(f"  - Importing {len(functions)} functions...")
        for entry in functions:
            self._import_function(session, entry)

    def _import_function(self, session, func_data):
        """関数のインポート"""
        # 関数ノードの作成
        combined_description = self._create_function_node(session, func_data)

        # パラメータの処理
        if func_data.get('params'):
            self._create_function_parameters(session, func_data)

        # 戻り値の処理
        if func_data.get('returns'):
            self._create_function_return(session, func_data)

        # LlamaIndex形式のデータ生成
        if self.create_llamaindex_format:
            self._create_llamaindex_function(session, func_data, combined_description)

        print(f"  - Imported function: {func_data['name']}")

    def _create_function_node(self, session, func_data):
        """関数ノードの作成"""
        # 説明に引数定義と戻り値情報を結合して格納
        base_desc = func_data.get('description', '') or ''
        parts = [base_desc.strip()]

        params = func_data.get('params') or []
        if params:
            param_lines = ["引数:"]
            for p in params:
                pname = p.get('name', '')
                ptype = p.get('type', '')
                pdesc = (p.get('description', '') or '').strip()
                required = p.get('is_required', False)
                req_txt = '必須' if required else '任意'
                line = f"- {pname} ({ptype}, {req_txt})"
                if pdesc:
                    line += f": {pdesc}"
                param_lines.append(line)
            parts.append("\n".join(param_lines))

        returns = func_data.get('returns') or {}
        rtype = returns.get('type')
        if rtype:
            parts.append(f"戻り値: {rtype}")

        combined_description = "\n\n".join([s for s in parts if s])

        query = """
        MERGE (f:Function {name: $name})
        SET f.description = $description,
            f.category = $category,
            f.implementation_status = $implementation_status,
            f.notes = $notes
        """
        session.run(
            query,
            name=func_data['name'],
            description=combined_description,
            category=func_data.get('category', ''),
            implementation_status=func_data.get('implementation_status', ''),
            notes=func_data.get('notes', '')
        )

        return combined_description

    def _create_function_parameters(self, session, func_data):
        """関数パラメータの作成"""
        for param_data in func_data['params']:
            self._create_parameter(
                session, func_data['name'], param_data, 'function'
            )
            if self.create_llamaindex_format:
                self._create_llamaindex_parameter(session, func_data['name'], param_data)

    def _create_function_return(self, session, func_data):
        """関数の戻り値の作成"""
        return_type = func_data['returns'].get('type')

        # 戻り値の型がObjectDefinitionとして定義されているかチェック
        # 注意: この時点ではObjectDefinitionはまだ作成されていない可能性がある
        # そのため、parsed_api_result_def.jsonの内容を直接チェックする
        query_check = """
        MATCH (od:ObjectDefinition {name: $return_type})
        RETURN od.name as name
        """
        result = session.run(query_check, return_type=return_type)
        obj_def_exists = result.single() is not None

        if obj_def_exists:
            # ObjectDefinitionが存在する場合は、それを使用
            query = """
            MATCH (f:Function {name: $func_name})
            MATCH (rt:ObjectDefinition {name: $return_type})
            MERGE (f)-[:RETURNS]->(rt)
            """
            print(f"    - Function '{func_data['name']}' returns "
                  f"ObjectDefinition '{return_type}'")
        else:
            # ObjectDefinitionが存在しない場合は、Typeとして作成
            query = """
            MATCH (f:Function {name: $func_name})
            MERGE (rt:Type {name: $return_type})
            MERGE (f)-[:RETURNS]->(rt)
            """
            print(f"    - Function '{func_data['name']}' returns "
                  f"Type '{return_type}'")

        session.run(
            query,
            func_name=func_data['name'],
            return_type=return_type
        )

        if self.create_llamaindex_format and return_type:
            self._create_llamaindex_return_relationship(
                session,
                func_data['name'],
                return_type,
                obj_def_exists,
            )

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
        session.run(
            query,
            name=obj_data['name'],
            description=obj_data.get('description', ''),
            category=obj_data.get('category', ''),
            notes=obj_data.get('notes', '')
        )

        if self.create_llamaindex_format:
            self._create_llamaindex_object_definition(session, obj_data)

    def _create_object_properties(self, session, obj_data):
        """オブジェクトプロパティの作成"""
        for prop_data in obj_data['properties']:
            self._create_parameter(
                session, obj_data['name'], prop_data, 'object'
            )
            if self.create_llamaindex_format:
                self._create_llamaindex_object_property(session, obj_data['name'], prop_data)

    def _create_parameter(self, session, parent_name, param_data, parent_type):
        """パラメータノードの作成（関数とオブジェクトの両方で使用）"""
        if parent_type == 'function':
            query = """
            MATCH (f:Function {name: $parent_name})
            MERGE (p:Parameter {name: $param_name,
               kind: 'function',
               parent_function: $parent_name})
        ON CREATE SET p.description = $param_description
        SET p.description = COALESCE($param_description, p.description)
        MERGE (f)-[r:USES_PARAMETER]->(p)
        SET r.parameter_description = $param_description,
            r.is_required = $param_required,
            r.position = $param_position

            WITH p
            // パラメータの型がObjectDefinitionとして定義されているかチェック
            OPTIONAL MATCH (od:ObjectDefinition {name: $param_type})
            WITH p, od
            // ObjectDefinitionが存在しない場合はTypeノードを確保
            CALL {
                WITH p
                MATCH (od:ObjectDefinition {name: $param_type})
                RETURN od as type_node
                UNION
                WITH p
                WHERE NOT EXISTS((:ObjectDefinition {name: $param_type}))
                MATCH (t:Type {name: $param_type})
                RETURN t as type_node
            }
            MERGE (p)-[:HAS_TYPE]->(type_node)
            """

            # まず統一メソッドでTypeノードを確保
            self._ensure_type_node(session, param_data['type'])

            session.run(
                query,
                parent_name=parent_name,
                param_name=param_data['name'],
                param_description=param_data.get('description', ''),
                param_required=param_data.get('is_required', False),
                param_position=param_data.get('position', 0),
                param_type=param_data['type']
            )
        else:  # object
            # オブジェクトプロパティの型情報処理を改善
            query = """
            MATCH (od:ObjectDefinition {name: $parent_name})
            MERGE (p:Parameter {name: $param_name,
               kind: 'object',
               parent_object: $parent_name})
        ON CREATE SET p.description = $param_description
        SET p.description = COALESCE($param_description, p.description)
        MERGE (od)-[r:USES_PROPERTY_PARAMETER]->(p)
        SET r.parameter_description = $param_description

            WITH p
            // 型情報の作成と関連付けを確実に行う
            MATCH (t:Type {name: $param_type})
            MERGE (p)-[:HAS_TYPE]->(t)
            """

            try:
                # まず統一メソッドでTypeノードを確保
                self._ensure_type_node(session, param_data['type'])
                
                session.run(
                    query,
                    parent_name=parent_name,
                    param_name=param_data['name'],
                    param_description=param_data.get('description', ''),
                    param_type=param_data['type']
                )
                print(f"    - Created parameter '{param_data['name']}' "
                      f"with type '{param_data['type']}' for object "
                      f"'{parent_name}'")
            except Exception as e:
                print(f"    - Error creating parameter '{param_data['name']}' "
                      f"for object '{parent_name}': {e}")
                # エラーが発生した場合でも、基本的なパラメータノードは作成する
                print("    - Fallback: Creating basic parameter node")
                try:
                    # Typeノードを確保してからフォールバック
                    self._ensure_type_node(session, param_data['type'])

                    fallback_query = """
                    MATCH (od:ObjectDefinition {name: $parent_name})
                    MERGE (p:Parameter {name: $param_name,
                           parent_object: $parent_name})
                    SET p.description = $param_description,
                        p.type = $param_type
                    MERGE (od)-[:HAS_PROPERTY]->(p)
                    """
                    session.run(
                        fallback_query,
                        parent_name=parent_name,
                        param_name=param_data['name'],
                        param_description=param_data.get('description', ''),
                        param_type=param_data['type']
                    )
                    print(f"    - Fallback successful for parameter '{param_data['name']}'")
                except Exception as fallback_error:
                    print(f"    - Fallback also failed: {fallback_error}")

    def _create_dependency_links(self, session):
        """関数間の依存関係リンクの作成"""
        print("Creating function dependency links...")
        query = """
        MATCH (func_a:Function)-[:RETURNS]->(obj:ObjectDefinition)
        MATCH (func_b:Function)-[:HAS_PARAMETER]->(param:Parameter)
        -[:HAS_TYPE]->(obj)
        MERGE (func_a)-[r:FEEDS_INTO]->(func_b)
        SET r.via_object = obj.name
        """
        try:
            result = session.run(query)
            summary = result.consume()
            print(f"  - Created {summary.counters.relationships_created} "
                  f"'FEEDS_INTO' relationships.")
        except Exception as e:
            print(f"  - Warning: Could not create dependency links: {e}")

    def _create_llamaindex_structures(self, session):
        """LlamaIndex形式の補助構造（制約・インデックス等）を作成"""
        constraint_queries = [
            """
            CREATE CONSTRAINT IF NOT EXISTS FOR (n:__Node__)
            REQUIRE n.id IS UNIQUE
            """,
            """
            CREATE CONSTRAINT IF NOT EXISTS FOR (n:__Entity__)
            REQUIRE n.id IS UNIQUE
            """,
        ]
        vector_index_query = """
        CREATE VECTOR INDEX entity IF NOT EXISTS
        FOR (m:__Entity__) ON m.embedding
        """

        for query in constraint_queries:
            try:
                session.run(query)
            except Exception as exc:
                print(f"  - Warning: LlamaIndex structure setup skipped ({exc})")

        try:
            session.run(vector_index_query)
        except Exception as exc:
            print(f"  - Warning: Vector index setup skipped ({exc})")

    def _clear_llamaindex_data(self, session):
        """既存のLlamaIndex派生ノードとリレーションを削除"""
        delete_queries = [
            "MATCH (n:__Node__) DETACH DELETE n",
            "MATCH (e:__Entity__) DETACH DELETE e",
        ]
        for query in delete_queries:
            session.run(query)

    def _create_llamaindex_function(
        self,
        session,
        func_data,
        combined_description: str,
    ):
        """LlamaIndex形式のFunctionエンティティとチャンクを作成"""
        name = func_data['name']
        entity_id = self._build_function_entity_id(name)
        chunk_id = self._build_function_chunk_id(name)

        entity_props = {
            'name': name,
            'description': func_data.get('description', ''),
            'category': func_data.get('category', ''),
            'implementation_status': func_data.get('implementation_status', ''),
            'notes': func_data.get('notes', ''),
        }
        self._merge_llamaindex_entity(session, 'Function', entity_id, entity_props)
        self._map_node_to_entity(session, 'Function', {'name': name}, entity_id)
        chunk_text = self._build_function_chunk_text(
            name,
            combined_description,
            entity_props['implementation_status'],
            entity_props['notes'],
        )
        self._merge_chunk_node(
            session,
            chunk_id,
            chunk_text,
            {'function_name': name},
            )
        self._link_chunk_to_entity(session, chunk_id, entity_id, 'MENTIONS')

    def _create_llamaindex_parameter(
        self,
        session,
        parent_function: str,
        param_data,
    ):
        """LlamaIndex形式のParameterエンティティを作成"""
        param_name = param_data.get('name', '')
        entity_id = self._build_parameter_entity_id(parent_function, param_name)
        entity_props = {
            'name': param_name,
            'description': param_data.get('description', ''),
            'parent_function': parent_function,
            'is_required': param_data.get('is_required', False),
            'type': param_data.get('type', ''),
            'position': param_data.get('position', 0),
        }
        self._merge_llamaindex_entity(session, 'Parameter', entity_id, entity_props)
        self._map_node_to_entity(
            session,
            'Parameter',
            {'name': param_name, 'parent_function': parent_function},
            entity_id,
        )

        function_entity_id = self._build_function_entity_id(parent_function)
        self._link_entity_to_entity(
            session,
            function_entity_id,
            entity_id,
            'HAS_PARAMETER_ENTITY',
        )

        chunk_id = self._build_function_chunk_id(parent_function)
        self._link_chunk_to_entity(session, chunk_id, entity_id, 'MENTIONS')

        param_type = param_data.get('type')
        if param_type:
            type_entity_id = self._build_type_entity_id(param_type)
            self._create_llamaindex_type(session, {'name': param_type})
            self._link_entity_to_entity(
                session,
                entity_id,
                type_entity_id,
                'HAS_TYPE_ENTITY',
            )

    def _create_llamaindex_object_property(
        self,
        session,
        parent_object: str,
        prop_data,
    ):
        """LlamaIndex形式のオブジェクトプロパティエンティティを作成"""
        prop_name = prop_data.get('name', '')
        entity_id = self._build_object_property_entity_id(parent_object, prop_name)
        entity_props = {
            'name': prop_name,
            'description': prop_data.get('description', ''),
            'parent_object': parent_object,
            'type': prop_data.get('type', ''),
        }
        self._merge_llamaindex_entity(session, 'ObjectProperty', entity_id, entity_props)
        self._map_node_to_entity(
            session,
            'Parameter',
            {'name': prop_name, 'parent_object': parent_object},
            entity_id,
        )

        object_entity_id = self._build_object_entity_id(parent_object)
        self._link_entity_to_entity(
            session,
            object_entity_id,
            entity_id,
            'HAS_PROPERTY_ENTITY',
        )

        prop_type = prop_data.get('type')
        if prop_type:
            type_entity_id = self._build_type_entity_id(prop_type)
            self._create_llamaindex_type(session, {'name': prop_type})
            self._link_entity_to_entity(
                session,
                entity_id,
                type_entity_id,
                'HAS_TYPE_ENTITY',
            )

    def _create_llamaindex_return_relationship(
        self,
        session,
        function_name: str,
        return_type: str,
        is_object_definition: bool,
    ):
        function_entity_id = self._build_function_entity_id(function_name)
        if is_object_definition:
            target_entity_id = self._build_object_entity_id(return_type)
            self._create_llamaindex_object_definition(session, {'name': return_type})
        else:
            target_entity_id = self._build_type_entity_id(return_type)
            self._create_llamaindex_type(session, {'name': return_type})

        self._link_entity_to_entity(
            session,
            function_entity_id,
            target_entity_id,
            'RETURNS_ENTITY',
        )

    def _create_llamaindex_object_definition(self, session, obj_data):
        """ObjectDefinitionノードのLlamaIndexエンティティ化"""
        name = obj_data['name']
        entity_id = self._build_object_entity_id(name)
        entity_props = {
            'name': name,
            'description': obj_data.get('description', ''),
            'category': obj_data.get('category', ''),
            'notes': obj_data.get('notes', ''),
        }
        self._merge_llamaindex_entity(session, 'ObjectDefinition', entity_id, entity_props)
        self._map_node_to_entity(session, 'ObjectDefinition', {'name': name}, entity_id)

        chunk_text = self._build_object_chunk_text(obj_data)
        if chunk_text.strip():
            chunk_id = self._build_object_chunk_id(name)
            self._merge_chunk_node(
                session,
                chunk_id,
                chunk_text,
                {'object_name': name},
            )
            self._link_chunk_to_entity(session, chunk_id, entity_id, 'MENTIONS')

    def _create_llamaindex_type(self, session, type_data):
        """Type情報をLlamaIndexエンティティとして登録（重複チェック付き）"""
        name = type_data.get('name') if isinstance(type_data, dict) else str(type_data)
        if not name:
            print("警告: Type名が空のため、LlamaIndexエンティティ作成をスキップします")
            return
        entity_id = self._build_type_entity_id(name)
        # 既存エンティティの存在チェック
        existing_check = session.run("""
            MATCH (e:__Entity__:Type {id: $entity_id})
            RETURN count(e) as count
        """, entity_id=entity_id)

        exists = existing_check.single()['count'] > 0
        if exists:
            # 既存エンティティがある場合は説明文のみ更新（空→有り）
            description = (type_data.get('description', '')
                          if isinstance(type_data, dict) else '')
            if description:  # 説明文がある場合のみ更新
                session.run("""
                    MATCH (e:__Entity__:Type {id: $entity_id})
                    SET e.description = CASE
                        WHEN (e.description IS NULL OR e.description = '')
                        THEN $description
                        ELSE e.description
                    END
                """, entity_id=entity_id, description=description)
            return

        # 新規作成
        entity_props = {
            'name': name,
            'description': type_data.get('description', '')
            if isinstance(type_data, dict)
            else '',
        }
        self._merge_llamaindex_entity(session, 'Type', entity_id, entity_props)
        self._map_node_to_entity(session, 'Type', {'name': name}, entity_id)

    def _merge_llamaindex_entity(self, session, label: str, entity_id: str, properties: Dict[str, Any]):
        """__Entity__ノードをマージする"""
        properties = self._sanitize_entity_properties(properties)
        query = f"""
        MERGE (e:__Entity__:{label} {{id: $entity_id}})
        SET e += $properties
        """
        session.run(query, entity_id=entity_id, properties=properties)

    def _ensure_type_node(self, session, type_name: str, description: str = ""):
        """
        Typeノードを安全に作成・更新する統一メソッド
        - 既存ノードがあれば説明文を改善（空→有り）
        - 新規作成の場合は説明文付きで作成
        - 重複を避けてMERGE操作を実行
        
        Args:
            session: Neo4jセッション
            type_name: 型名
            description: 型の説明（空文字列の場合は既存の説明を保持）
        
        Returns:
            作成/更新されたTypeノード
        """
        try:
            query = """
            MERGE (t:Type {name: $type_name})
            ON CREATE SET t.description = $description
            ON MATCH SET t.description = CASE 
                WHEN (t.description IS NULL OR t.description = '') AND $description <> ''
                THEN $description 
                ELSE COALESCE(t.description, $description)
            END
            RETURN t
            """
            result = session.run(query, type_name=type_name, description=description)
            record = result.single()
            if record:
                return record['t']
            else:
                print(f"警告: Type '{type_name}' の作成に失敗しました")
                return None
        except Exception as e:
            print(f"エラー: Type '{type_name}' の作成中にエラーが発生: {e}")
            return None

    @staticmethod
    def _sanitize_entity_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
        sanitized = dict(properties)
        sanitized.pop('id', None)
        return sanitized

    def _merge_chunk_node(self, session, chunk_id: str, text: str, properties: Optional[Dict[str, Any]] = None):
        """__Node__チャンクをマージする"""
        props = {'text': text}
        if properties:
            props.update(properties)

        query = """
        MERGE (c:__Node__:Chunk {id: $chunk_id})
        SET c += $properties
        """
        session.run(query, chunk_id=chunk_id, properties=props)

    def _link_chunk_to_entity(
        self,
        session,
        chunk_id: str,
        entity_id: str,
        relationship: str,
    ):
        query = f"""
        MATCH (c:__Node__ {{id: $chunk_id}})
        MATCH (e:__Entity__ {{id: $entity_id}})
        MERGE (c)-[:{relationship}]->(e)
        """
        session.run(query, chunk_id=chunk_id, entity_id=entity_id)

    def _link_entity_to_entity(
        self,
        session,
        start_id: str,
        end_id: str,
        relationship: str,
    ):
        query = f"""
        MATCH (s:__Entity__ {{id: $start_id}})
        MATCH (t:__Entity__ {{id: $end_id}})
        MERGE (s)-[:{relationship}]->(t)
        """
        session.run(query, start_id=start_id, end_id=end_id)

    def _map_node_to_entity(self, session, label: str, match_props: dict, entity_id: str):
        conditions = [f"n.{key} = ${key}" for key in match_props]
        query = f"""
        MATCH (n:{label})
        WHERE {' AND '.join(conditions)}
        MATCH (e:__Entity__ {{id: $entity_id}})
        MERGE (n)-[:MAPS_TO]->(e)
        """
        params = match_props.copy()
        params['entity_id'] = entity_id
        session.run(query, **params)

    def _build_function_chunk_text(
        self,
        name: str,
        combined_description: str,
        implementation_status: str,
        notes: str,
    ) -> str:
        lines = [f"Function: {name}"]
        if combined_description:
            lines.append(combined_description)
        if implementation_status:
            lines.append(f"実装状況: {implementation_status}")
        if notes:
            lines.append(f"備考: {notes}")
        return "\n\n".join(lines)

    def _build_object_chunk_text(self, obj_data) -> str:
        lines = [f"Object: {obj_data['name']}"]
        description = obj_data.get('description', '')
        if description:
            lines.append(description)
        properties = obj_data.get('properties') or []
        if properties:
            prop_lines = ["プロパティ:"]
            for prop in properties:
                pname = prop.get('name', '')
                ptype = prop.get('type', '')
                pdesc = prop.get('description', '')
                line = f"- {pname} ({ptype})"
                if pdesc:
                    line += f": {pdesc}"
                prop_lines.append(line)
            lines.append("\n".join(prop_lines))
        return "\n\n".join(lines)

    @staticmethod
    def _build_function_entity_id(name: str) -> str:
        return f"function::{name}"

    @staticmethod
    def _build_parameter_entity_id(parent: str, name: str) -> str:
        return f"parameter::{parent}::{name}"

    @staticmethod
    def _build_object_property_entity_id(parent: str, name: str) -> str:
        return f"object_property::{parent}::{name}"

    @staticmethod
    def _build_object_entity_id(name: str) -> str:
        return f"object::{name}"

    @staticmethod
    def _build_type_entity_id(name: str) -> str:
        return f"type::{name}"

    @staticmethod
    def _build_function_chunk_id(name: str) -> str:
        return f"chunk::function::{name}"

    @staticmethod
    def _build_object_chunk_id(name: str) -> str:
        return f"chunk::object::{name}"


def load_environment():
    """環境変数の読み込み"""
    load_dotenv()

    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "docparser")

    if not all([uri, user, password]):
        raise ValueError(
            "NEO4J_URI, NEO4J_USER (or NEO4J_USERNAME), and "
            "NEO4J_PASSWORD must be set in the .env file."
        )

    return uri, user, password, database


def load_api_data(file_path=None, use_def_file=False):
    """APIデータの読み込み

    Args:
        file_path (str, optional): カスタムファイルパス。指定された場合はそのファイルを使用
        use_def_file (bool): Trueの場合はparsed_api_result_def.json、
            Falseの場合はparsed_api_result.jsonを使用

    Returns:
        dict: 読み込まれたAPIデータ
    """
    if file_path is None:
        if use_def_file:
            file_path = 'doc_parser/parsed_api_result_def.json'
        else:
            file_path = 'doc_parser/parsed_api_result.json'

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"Successfully loaded API data from: {file_path}")
            return data
    except FileNotFoundError:
        raise FileNotFoundError(
            f"API data file not found: {file_path}. "
            f"Please run doc_paser.py first."
        )
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in {file_path}: {e}")
    except Exception as e:
        raise Exception(f"Error reading {file_path}: {e}")


def import_to_neo4j(
    uri,
    user,
    password,
    database,
    file_path=None,
    use_def_file=True,
    config=None,
    create_llamaindex_format: Optional[bool] = None,
):
    """Neo4jにデータをインポートする関数"""
    print("Neo4j Importer script started.")

    importer = None
    try:
        print(f"Connecting to Neo4j database: {database}")
        if database == "docparser":
            print("  → APIドキュメント解析データを格納する専用データベースを使用します")

        # ファイル選択の決定
        if file_path:
            # カスタムファイルパスが指定された場合
            api_data = load_api_data(file_path=file_path)
        elif not use_def_file:
            # オリジナルファイルを使用する場合
            api_data = load_api_data(use_def_file=False)
        else:
            # デフォルトでparsed_api_result_def.jsonを使用
            api_data = load_api_data(use_def_file=True)

        if create_llamaindex_format is None:
            if config is not None:
                create_llamaindex_format = getattr(
                    config,
                    "create_llamaindex_format",
                    True,
                )
            else:
                env_flag = os.getenv("CREATE_LLAMAINDEX_FORMAT")
                if env_flag is None:
                    create_llamaindex_format = True
                else:
                    create_llamaindex_format = env_flag.lower() in ("1", "true", "yes")

        # データのインポート
        importer = Neo4jImporter(
            uri,
            user,
            password,
            database,
            create_llamaindex_format=create_llamaindex_format,
        )
        importer.import_data(api_data)
        return True

    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False
    finally:
        if importer is not None:
            importer.close()

    print("Neo4j Importer script finished.")


def main():
    """メイン処理（コマンドライン用）"""
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(
        description='Neo4jにAPIデータをインポートするスクリプト',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
    使用例:
    python neo4j_importer.py  # デフォルトでparsed_api_result_def.jsonを使用
    python neo4j_importer.py --def-file  # parsed_api_result_def.jsonを使用
    python neo4j_importer.py --original-file  # parsed_api_result.jsonを使用
    python neo4j_importer.py --file custom.json  # カスタムファイルを使用
            """
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--def-file', action='store_true',
        help='parsed_api_result_def.jsonを使用（デフォルト）'
    )
    group.add_argument(
        '--original-file', action='store_true',
        help='parsed_api_result.jsonを使用'
    )
    group.add_argument(
        '--file', type=str, metavar='FILE',
        help='指定されたファイルを使用'
    )

    parser.set_defaults(create_llamaindex_format=True)
    parser.add_argument(
        '--llamaindex-format',
        dest='create_llamaindex_format',
        action='store_true',
        help='LlamaIndex形式の補助ノード/リレーションを生成する',
    )
    parser.add_argument(
        '--no-llamaindex-format',
        dest='create_llamaindex_format',
        action='store_false',
        help='LlamaIndex形式の生成を無効化する',
    )

    args = parser.parse_args()

    # 環境変数の読み込み
    uri, user, password, database = load_environment()

    # ファイル選択の決定
    file_path = args.file if args.file else None
    use_def_file = not args.original_file

    success = import_to_neo4j(
        uri,
        user,
        password,
        database,
        file_path,
        use_def_file,
        create_llamaindex_format=args.create_llamaindex_format,
    )

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    print(f"プロジェクトルートパス: {project_root}")
    main()
