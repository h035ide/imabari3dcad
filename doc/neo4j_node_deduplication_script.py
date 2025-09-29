#!/usr/bin/env python3
"""
Neo4jノード重複解消スクリプト

問題:
- Type:boolが複数のelementIdを持つ
- __Entity__:Type:boolが複数のidを持つ

解決策:
1. 説明文があるType:boolノードを保持、空のものを削除
2. __Entity__:Type:boolノードを統合
3. 既存リレーションを統合先ノードに付け替え
"""

import os
import sys
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv
from typing import List, Dict, Any

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

load_dotenv()


class Neo4jDeduplicator:
    def __init__(self, uri: str, user: str, password: str, database: str = "docparser"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database

    def close(self):
        self.driver.close()

    def analyze_bool_nodes(self):
        """boolノードの重複状況を分析"""
        with self.driver.session(database=self.database) as session:
            # Type:boolノードの確認
            type_result = session.run("""
                MATCH (t:Type {name: 'bool'})
                RETURN elementId(t) as element_id, t.description as description
                ORDER BY t.description DESC
            """)
            type_nodes = list(type_result)
            
            # __Entity__:Type:boolノードの確認
            entity_result = session.run("""
                MATCH (e:__Entity__:Type {name: 'bool'})
                RETURN elementId(e) as element_id, e.id as entity_id, e.description as description
            """)
            entity_nodes = list(entity_result)
            
            print(f"Type:bool ノード数: {len(type_nodes)}")
            for node in type_nodes:
                desc = node['description'] or "(空)"
                print(f"  - {node['element_id']}: {desc}")
            
            print(f"\n__Entity__:Type:bool ノード数: {len(entity_nodes)}")
            for node in entity_nodes:
                desc = node['description'] or "(空)"
                print(f"  - {node['element_id']} (id: {node['entity_id']}): {desc}")
            
            return type_nodes, entity_nodes

    def deduplicate_type_bool(self):
        """Type:boolノードの重複解消"""
        with self.driver.session(database=self.database) as session:
            # 説明文があるノードとないノードを特定
            result = session.run("""
                MATCH (t:Type {name: 'bool'})
                WITH t, CASE WHEN t.description IS NOT NULL AND t.description <> '' THEN 1 ELSE 0 END as has_desc
                ORDER BY has_desc DESC, elementId(t)
                RETURN collect(elementId(t)) as element_ids, collect(t.description) as descriptions
            """)
            
            record = result.single()
            if not record or not record['element_ids']:
                print("Type:boolノードが見つかりません")
                return None
            
            element_ids = record['element_ids']
            descriptions = record['descriptions']
            
            if len(element_ids) <= 1:
                print("Type:boolノードに重複はありません")
                return element_ids[0] if element_ids else None
            
            # 最初のノード（説明文があるもの）を保持対象とする
            keep_id = element_ids[0]
            remove_ids = element_ids[1:]
            
            print(f"保持対象: {keep_id} (説明: {descriptions[0] or '(空)'})")
            print(f"削除対象: {remove_ids}")
            
            # リレーションを保持対象ノードに移動（APOCを使用）
            for remove_id in remove_ids:
                try:
                    # 入力リレーション移動
                    session.run("""
                        MATCH (source)-[r]->(target)
                        WHERE elementId(target) = $remove_id
                        MATCH (keep)
                        WHERE elementId(keep) = $keep_id
                        WITH source, r, keep, type(r) as rel_type, properties(r) as props
                        CALL apoc.create.relationship(source, rel_type, props, keep) YIELD rel
                        DELETE r
                    """, remove_id=remove_id, keep_id=keep_id)
                    
                    # 出力リレーション移動
                    session.run("""
                        MATCH (source)-[r]->(target)
                        WHERE elementId(source) = $remove_id
                        MATCH (keep)
                        WHERE elementId(keep) = $keep_id
                        WITH target, r, keep, type(r) as rel_type, properties(r) as props
                        CALL apoc.create.relationship(keep, rel_type, props, target) YIELD rel
                        DELETE r
                    """, remove_id=remove_id, keep_id=keep_id)
                    
                except Exception as e:
                    print(f"APOC使用でリレーション移動に失敗。手動実行: {e}")
                    # APOCなしでの手動リレーション移動
                    # 入力リレーション（HAS_TYPE等）
                    session.run("""
                        MATCH (source)-[r:HAS_TYPE]->(target)
                        WHERE elementId(target) = $remove_id
                        MATCH (keep)
                        WHERE elementId(keep) = $keep_id
                        MERGE (source)-[:HAS_TYPE]->(keep)
                        DELETE r
                    """, remove_id=remove_id, keep_id=keep_id)
                    
                    # その他の入力リレーション
                    session.run("""
                        MATCH (source)-[r]->(target)
                        WHERE elementId(target) = $remove_id AND NOT type(r) = 'HAS_TYPE'
                        DELETE r
                    """, remove_id=remove_id)
                    
                    # 出力リレーション（通常Typeノードは出力リレーションを持たないが念のため）
                    session.run("""
                        MATCH (source)-[r]->(target)
                        WHERE elementId(source) = $remove_id
                        DELETE r
                    """, remove_id=remove_id)
            
            # 重複ノード削除
            for remove_id in remove_ids:
                session.run("""
                    MATCH (t)
                    WHERE elementId(t) = $remove_id
                    DELETE t
                """, remove_id=remove_id)
            
            # 保持ノードの説明文を確実に設定
            session.run("""
                MATCH (t)
                WHERE elementId(t) = $keep_id
                SET t.description = COALESCE(t.description, '真偽値。True または False を指定。例: True, False')
            """, keep_id=keep_id)
            
            print(f"Type:bool重複解消完了。保持ノード: {keep_id}")
            return keep_id

    def deduplicate_entity_bool(self):
        """__Entity__:Type:boolノードの重複解消"""
        with self.driver.session(database=self.database) as session:
            # 全ての__Entity__:Type:boolノードを取得
            result = session.run("""
                MATCH (e:__Entity__:Type {name: 'bool'})
                RETURN elementId(e) as element_id, e.id as entity_id
                ORDER BY elementId(e)
            """)
            
            nodes = list(result)
            if len(nodes) <= 1:
                print("__Entity__:Type:boolノードに重複はありません")
                return nodes[0]['element_id'] if nodes else None
            
            # 最初のノードを保持対象とする
            keep_id = nodes[0]['element_id']
            remove_ids = [node['element_id'] for node in nodes[1:]]
            
            print(f"__Entity__保持対象: {keep_id}")
            print(f"__Entity__削除対象: {remove_ids}")
            
            # APOCのmergeNodesを使用（利用可能な場合）
            try:
                session.run("""
                    MATCH (e:__Entity__:Type {name: 'bool'})
                    WITH collect(e) as nodes
                    CALL apoc.refactor.mergeNodes(nodes, {
                        properties: 'combine',
                        mergeRels: true
                    }) YIELD node
                    SET node.description = COALESCE(node.description, '真偽値。True または False を指定。例: True, False')
                    RETURN elementId(node) as merged_id
                """)
                print("APOCを使用して__Entity__:Type:boolノードを統合しました")
            except Exception as e:
                print(f"APOC統合に失敗。手動統合を実行: {e}")
                # 手動統合
                for remove_id in remove_ids:
                    # リレーション移動（MAPS_TO等）
                    session.run("""
                        MATCH (source)-[r:MAPS_TO]->(target)
                        WHERE elementId(target) = $remove_id
                        MATCH (keep)
                        WHERE elementId(keep) = $keep_id
                        MERGE (source)-[:MAPS_TO]->(keep)
                        DELETE r
                    """, remove_id=remove_id, keep_id=keep_id)
                    
                    # その他のリレーション削除
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
                
                # 保持ノードの説明文設定
                session.run("""
                    MATCH (e)
                    WHERE elementId(e) = $keep_id
                    SET e.description = COALESCE(e.description, '真偽値。True または False を指定。例: True, False')
                """, keep_id=keep_id)
            
            print(f"__Entity__:Type:bool重複解消完了。保持ノード: {keep_id}")
            return keep_id

    def verify_deduplication(self):
        """重複解消結果の検証"""
        with self.driver.session(database=self.database) as session:
            # Type:boolノード数確認
            type_count = session.run("""
                MATCH (t:Type {name: 'bool'})
                RETURN count(t) as count
            """).single()['count']
            
            # __Entity__:Type:boolノード数確認
            entity_count = session.run("""
                MATCH (e:__Entity__:Type {name: 'bool'})
                RETURN count(e) as count
            """).single()['count']
            
            print(f"\n=== 重複解消結果 ===")
            print(f"Type:boolノード数: {type_count}")
            print(f"__Entity__:Type:boolノード数: {entity_count}")
            
            if type_count <= 1 and entity_count <= 1:
                print("[OK] 重複解消が正常に完了しました")
                return True
            else:
                print("[NG] まだ重複が残っています")
                return False

    def run_full_deduplication(self):
        """完全な重複解消処理"""
        print("=== Neo4j bool型ノード重複解消処理開始 ===")
        
        # 現状分析
        print("\n1. 現状分析")
        self.analyze_bool_nodes()
        
        # Type:bool重複解消
        print("\n2. Type:boolノード重複解消")
        self.deduplicate_type_bool()
        
        # __Entity__:Type:bool重複解消
        print("\n3. __Entity__:Type:boolノード重複解消") 
        self.deduplicate_entity_bool()
        
        # 結果検証
        print("\n4. 結果検証")
        success = self.verify_deduplication()
        
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
        deduplicator = Neo4jDeduplicator(uri, user, password, database)
        success = deduplicator.run_full_deduplication()
        
        if success:
            print("重複解消処理が正常に完了しました")
            sys.exit(0)
        else:
            print("重複解消処理で問題が発生しました")
            sys.exit(1)
            
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)
    finally:
        if deduplicator:
            deduplicator.close()


if __name__ == "__main__":
    main()
