#!/usr/bin/env python3
"""
Neo4j包括的重複解消スクリプト

問題:
- Type:boolが複数のelementIdを持つ
- __Entity__:Type:boolが複数のidを持つ
- Parameter（Function/Object）の重複

解決策:
1. 全種別の重複を診断
2. APOCを使用して一括統合
3. 制約・インデックスを強化
4. 再発防止の確認
"""

import os
import sys
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv
from typing import List, Dict, Any, Tuple

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

load_dotenv()


class Neo4jComprehensiveDeduplicator:
    def __init__(self, uri: str, user: str, password: str, database: str = "docparser"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database

    def close(self):
        self.driver.close()

    def diagnose_duplicates(self) -> Dict[str, List[Dict]]:
        """全種別の重複を診断"""
        with self.driver.session(database=self.database) as session:
            results = {}
            
            # Type重複診断
            print("1. Type重複診断中...")
            type_result = session.run("""
                MATCH (t:Type)
                WITH t.name AS name, collect(elementId(t)) AS ids, count(*) AS c
                WHERE name IS NOT NULL AND c > 1
                RETURN name, c, ids
                ORDER BY c DESC
            """)
            results['types'] = [dict(record) for record in type_result]
            print(f"   Type重複: {len(results['types'])}件")
            
            # __Entity__重複診断
            print("2. __Entity__重複診断中...")
            entity_result = session.run("""
                MATCH (e:__Entity__)
                WITH e.id AS id, collect(elementId(e)) AS ids, count(*) AS c
                WHERE id IS NOT NULL AND c > 1
                RETURN id, c, ids
                ORDER BY c DESC
            """)
            results['entities'] = [dict(record) for record in entity_result]
            print(f"   __Entity__重複: {len(results['entities'])}件")
            
            # Function Parameter重複診断
            print("3. Function Parameter重複診断中...")
            func_param_result = session.run("""
                MATCH (p:Parameter {kind:'function'})
                WITH p.name AS name, p.parent_function AS parent, collect(elementId(p)) AS ids, count(*) AS c
                WHERE name IS NOT NULL AND parent IS NOT NULL AND c > 1
                RETURN name, parent, c, ids
                ORDER BY c DESC
            """)
            results['function_params'] = [dict(record) for record in func_param_result]
            print(f"   Function Parameter重複: {len(results['function_params'])}件")
            
            # Object Parameter重複診断
            print("4. Object Parameter重複診断中...")
            obj_param_result = session.run("""
                MATCH (p:Parameter {kind:'object'})
                WITH p.name AS name, p.parent_object AS parent, collect(elementId(p)) AS ids, count(*) AS c
                WHERE name IS NOT NULL AND parent IS NOT NULL AND c > 1
                RETURN name, parent, c, ids
                ORDER BY c DESC
            """)
            results['object_params'] = [dict(record) for record in obj_param_result]
            print(f"   Object Parameter重複: {len(results['object_params'])}件")
            
            # ObjectDefinition重複診断
            print("5. ObjectDefinition重複診断中...")
            obj_def_result = session.run("""
                MATCH (n:ObjectDefinition)
                WITH n.name AS name, collect(elementId(n)) AS ids, count(*) AS c
                WHERE name IS NOT NULL AND c > 1
                RETURN name, c, ids
                ORDER BY c DESC
            """)
            results['object_definitions'] = [dict(record) for record in obj_def_result]
            print(f"   ObjectDefinition重複: {len(results['object_definitions'])}件")
            
            # Function重複診断
            print("6. Function重複診断中...")
            func_result = session.run("""
                MATCH (f:Function)
                WITH f.name AS name, collect(elementId(f)) AS ids, count(*) AS c
                WHERE name IS NOT NULL AND c > 1
                RETURN name, c, ids
                ORDER BY c DESC
            """)
            results['functions'] = [dict(record) for record in func_result]
            print(f"   Function重複: {len(results['functions'])}件")
            
            return results

    def deduplicate_types(self) -> int:
        """Type重複解消"""
        with self.driver.session(database=self.database) as session:
            try:
                result = session.run("""
                    MATCH (t:Type)
                    WITH t.name AS name, collect(t) AS nodes
                    WHERE name IS NOT NULL AND size(nodes) > 1
                    CALL apoc.refactor.mergeNodes(nodes, {
                        properties: 'combine',
                        mergeRels: true,
                        force: true
                    }) YIELD node
                    RETURN count(*) AS merged_count
                """)
                count = result.single()['merged_count']
                print(f"Type重複解消: {count}件")
                return count
            except Exception as e:
                print(f"APOC使用でType重複解消に失敗。手動実行: {e}")
                return self._manual_merge_types(session)

    def deduplicate_entities(self) -> int:
        """__Entity__重複解消"""
        with self.driver.session(database=self.database) as session:
            try:
                result = session.run("""
                    MATCH (e:__Entity__)
                    WITH e.id AS id, collect(e) AS nodes
                    WHERE id IS NOT NULL AND size(nodes) > 1
                    CALL apoc.refactor.mergeNodes(nodes, {
                        properties: 'combine',
                        mergeRels: true,
                        force: true
                    }) YIELD node
                    RETURN count(*) AS merged_count
                """)
                count = result.single()['merged_count']
                print(f"__Entity__重複解消: {count}件")
                return count
            except Exception as e:
                print(f"APOC使用で__Entity__重複解消に失敗。手動実行: {e}")
                return self._manual_merge_entities(session)

    def deduplicate_parameters(self) -> Tuple[int, int]:
        """Parameter重複解消（Function/Object別）"""
        with self.driver.session(database=self.database) as session:
            func_count = 0
            obj_count = 0
            
            try:
                # Function Parameter
                result = session.run("""
                    MATCH (p:Parameter {kind:'function'})
                    WITH p.name AS name, p.parent_function AS parent, collect(p) AS nodes
                    WHERE name IS NOT NULL AND parent IS NOT NULL AND size(nodes) > 1
                    CALL apoc.refactor.mergeNodes(nodes, {
                        properties: 'combine',
                        mergeRels: true,
                        force: true
                    }) YIELD node
                    RETURN count(*) AS merged_count
                """)
                func_count = result.single()['merged_count']
                print(f"Function Parameter重複解消: {func_count}件")
            except Exception as e:
                print(f"APOC使用でFunction Parameter重複解消に失敗: {e}")
            
            try:
                # Object Parameter
                result = session.run("""
                    MATCH (p:Parameter {kind:'object'})
                    WITH p.name AS name, p.parent_object AS parent, collect(p) AS nodes
                    WHERE name IS NOT NULL AND parent IS NOT NULL AND size(nodes) > 1
                    CALL apoc.refactor.mergeNodes(nodes, {
                        properties: 'combine',
                        mergeRels: true,
                        force: true
                    }) YIELD node
                    RETURN count(*) AS merged_count
                """)
                obj_count = result.single()['merged_count']
                print(f"Object Parameter重複解消: {obj_count}件")
            except Exception as e:
                print(f"APOC使用でObject Parameter重複解消に失敗: {e}")
            
            return func_count, obj_count

    def deduplicate_objects_and_functions(self) -> Tuple[int, int]:
        """ObjectDefinition/Function重複解消"""
        with self.driver.session(database=self.database) as session:
            obj_count = 0
            func_count = 0
            
            try:
                # ObjectDefinition
                result = session.run("""
                    MATCH (n:ObjectDefinition)
                    WITH n.name AS name, collect(n) AS nodes
                    WHERE name IS NOT NULL AND size(nodes) > 1
                    CALL apoc.refactor.mergeNodes(nodes, {
                        properties: 'combine',
                        mergeRels: true,
                        force: true
                    }) YIELD node
                    RETURN count(*) AS merged_count
                """)
                obj_count = result.single()['merged_count']
                print(f"ObjectDefinition重複解消: {obj_count}件")
            except Exception as e:
                print(f"APOC使用でObjectDefinition重複解消に失敗: {e}")
            
            try:
                # Function
                result = session.run("""
                    MATCH (f:Function)
                    WITH f.name AS name, collect(f) AS nodes
                    WHERE name IS NOT NULL AND size(nodes) > 1
                    CALL apoc.refactor.mergeNodes(nodes, {
                        properties: 'combine',
                        mergeRels: true,
                        force: true
                    }) YIELD node
                    RETURN count(*) AS merged_count
                """)
                func_count = result.single()['merged_count']
                print(f"Function重複解消: {func_count}件")
            except Exception as e:
                print(f"APOC使用でFunction重複解消に失敗: {e}")
            
            return obj_count, func_count

    def _manual_merge_types(self, session) -> int:
        """Type手動統合（APOCなし）"""
        # 診断結果を取得
        result = session.run("""
            MATCH (t:Type)
            WITH t.name AS name, collect(elementId(t)) AS ids, count(*) AS c
            WHERE name IS NOT NULL AND c > 1
            RETURN name, ids
        """)
        
        merged_count = 0
        for record in result:
            name = record['name']
            ids = record['ids']
            keep_id = ids[0]  # 最初のIDを保持
            remove_ids = ids[1:]
            
            # リレーション移動
            for remove_id in remove_ids:
                session.run("""
                    MATCH (source)-[r]->(target)
                    WHERE elementId(target) = $remove_id
                    MATCH (keep)
                    WHERE elementId(keep) = $keep_id
                    WITH source, r, keep, type(r) as rel_type, properties(r) as props
                    CALL apoc.create.relationship(source, rel_type, props, keep) YIELD rel
                    DELETE r
                """, remove_id=remove_id, keep_id=keep_id)
                
                session.run("""
                    MATCH (source)-[r]->(target)
                    WHERE elementId(source) = $remove_id
                    MATCH (keep)
                    WHERE elementId(keep) = $keep_id
                    WITH target, r, keep, type(r) as rel_type, properties(r) as props
                    CALL apoc.create.relationship(keep, rel_type, props, target) YIELD rel
                    DELETE r
                """, remove_id=remove_id, keep_id=keep_id)
            
            # 重複ノード削除
            for remove_id in remove_ids:
                session.run("""
                    MATCH (t)
                    WHERE elementId(t) = $remove_id
                    DELETE t
                """, remove_id=remove_id)
            
            merged_count += len(remove_ids)
        
        print(f"Type手動統合: {merged_count}件")
        return merged_count

    def _manual_merge_entities(self, session) -> int:
        """__Entity__手動統合（APOCなし）"""
        # 診断結果を取得
        result = session.run("""
            MATCH (e:__Entity__)
            WITH e.id AS id, collect(elementId(e)) AS ids, count(*) AS c
            WHERE id IS NOT NULL AND c > 1
            RETURN id, ids
        """)
        
        merged_count = 0
        for record in result:
            entity_id = record['id']
            ids = record['ids']
            keep_id = ids[0]  # 最初のIDを保持
            remove_ids = ids[1:]
            
            # リレーション移動
            for remove_id in remove_ids:
                session.run("""
                    MATCH (source)-[r:MAPS_TO]->(target)
                    WHERE elementId(target) = $remove_id
                    MATCH (keep)
                    WHERE elementId(keep) = $keep_id
                    MERGE (source)-[:MAPS_TO]->(keep)
                    DELETE r
                """, remove_id=remove_id, keep_id=keep_id)
                
                session.run("""
                    MATCH (source)-[r]->(target)
                    WHERE elementId(target) = $remove_id
                    DELETE r
                """, remove_id=remove_id)
                
                session.run("""
                    MATCH (source)-[r]->(target)
                    WHERE elementId(source) = $remove_id
                    DELETE r
                """, remove_id=remove_id)
            
            # 重複ノード削除
            for remove_id in remove_ids:
                session.run("""
                    MATCH (e)
                    WHERE elementId(e) = $remove_id
                    DELETE e
                """, remove_id=remove_id)
            
            merged_count += len(remove_ids)
        
        print(f"__Entity__手動統合: {merged_count}件")
        return merged_count

    def create_constraints_and_indexes(self):
        """制約とインデックスを作成"""
        with self.driver.session(database=self.database) as session:
            constraints = [
                "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Type) REQUIRE t.name IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (n:__Node__) REQUIRE n.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (n:__Entity__) REQUIRE n.id IS UNIQUE",
            ]
            
            indexes = [
                "CREATE INDEX IF NOT EXISTS FOR (p:Parameter) ON (p.name)",
                "CREATE INDEX IF NOT EXISTS FOR (p:Parameter) ON (p.parent_function)",
                "CREATE INDEX IF NOT EXISTS FOR (p:Parameter) ON (p.parent_object)",
                "CREATE INDEX IF NOT EXISTS FOR (p:Parameter) ON (p.kind)",
            ]
            
            print("制約とインデックスを作成中...")
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                    print(f"  制約作成: {constraint.split()[-1]}")
                except Exception as e:
                    print(f"  制約作成失敗: {e}")
            
            for index in indexes:
                try:
                    session.run(index)
                    print(f"  インデックス作成: {index.split()[-1]}")
                except Exception as e:
                    print(f"  インデックス作成失敗: {e}")

    def verify_no_duplicates(self) -> bool:
        """重複解消結果の検証"""
        with self.driver.session(database=self.database) as session:
            print("\n=== 重複解消結果検証 ===")
            
            # 各種別の重複チェック
            checks = [
                ("Type", "MATCH (t:Type) WITH t.name AS name, count(*) AS c WHERE name IS NOT NULL AND c > 1 RETURN count(*) AS duplicates"),
                ("__Entity__", "MATCH (e:__Entity__) WITH e.id AS id, count(*) AS c WHERE id IS NOT NULL AND c > 1 RETURN count(*) AS duplicates"),
                ("Function Parameter", "MATCH (p:Parameter {kind:'function'}) WITH p.name AS name, p.parent_function AS parent, count(*) AS c WHERE c > 1 RETURN count(*) AS duplicates"),
                ("Object Parameter", "MATCH (p:Parameter {kind:'object'}) WITH p.name AS name, p.parent_object AS parent, count(*) AS c WHERE c > 1 RETURN count(*) AS duplicates"),
                ("ObjectDefinition", "MATCH (n:ObjectDefinition) WITH n.name AS name, count(*) AS c WHERE name IS NOT NULL AND c > 1 RETURN count(*) AS duplicates"),
                ("Function", "MATCH (f:Function) WITH f.name AS name, count(*) AS c WHERE name IS NOT NULL AND c > 1 RETURN count(*) AS duplicates"),
            ]
            
            all_clean = True
            for label, query in checks:
                result = session.run(query)
                duplicates = result.single()['duplicates']
                status = "OK" if duplicates == 0 else "NG"
                print(f"  {label}: {duplicates}件の重複 ({status})")
                if duplicates > 0:
                    all_clean = False
            
            if all_clean:
                print("\n[OK] 全ての重複が解消されました")
            else:
                print("\n[NG] まだ重複が残っています")
            
            return all_clean

    def run_comprehensive_deduplication(self):
        """包括的重複解消処理"""
        print("=== Neo4j包括的重複解消処理開始 ===")
        
        # 1. 診断
        print("\n1. 重複診断")
        duplicates = self.diagnose_duplicates()
        
        total_duplicates = (len(duplicates['types']) + len(duplicates['entities']) + 
                          len(duplicates['function_params']) + len(duplicates['object_params']) +
                          len(duplicates['object_definitions']) + len(duplicates['functions']))
        
        if total_duplicates == 0:
            print("重複は見つかりませんでした")
            return True
        
        print(f"\n総重複数: {total_duplicates}件")
        
        # 2. 重複解消
        print("\n2. 重複解消実行")
        type_count = self.deduplicate_types()
        entity_count = self.deduplicate_entities()
        func_param_count, obj_param_count = self.deduplicate_parameters()
        obj_def_count, func_count = self.deduplicate_objects_and_functions()
        
        total_merged = (type_count + entity_count + func_param_count + 
                       obj_param_count + obj_def_count + func_count)
        print(f"\n総統合数: {total_merged}件")
        
        # 3. 制約・インデックス作成
        print("\n3. 制約・インデックス作成")
        self.create_constraints_and_indexes()
        
        # 4. 検証
        print("\n4. 結果検証")
        success = self.verify_no_duplicates()
        
        print("\n=== 処理完了 ===")
        return success


def main():
    """メイン処理"""
    # 環境変数読み込み
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "docparser")
    
    if not password:
        print("エラー: NEO4J_PASSWORDが設定されていません")
        sys.exit(1)
    
    deduplicator = None
    try:
        deduplicator = Neo4jComprehensiveDeduplicator(uri, user, password, database)
        success = deduplicator.run_comprehensive_deduplication()
        
        if success:
            print("包括的重複解消処理が正常に完了しました")
            sys.exit(0)
        else:
            print("包括的重複解消処理で問題が発生しました")
            sys.exit(1)
            
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)
    finally:
        if deduplicator:
            deduplicator.close()


if __name__ == "__main__":
    main()
