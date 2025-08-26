"""
Enhanced Data Migration Module

既存のNeo4jデータベースを拡張データモデルに対応させるための
マイグレーション機能を提供します。
"""

from typing import Dict, List, Any, Optional, Tuple
import json
import logging
from datetime import datetime
from neo4j import GraphDatabase, Transaction
from .enhanced_data_models import (
    EnhancedNodeType, EnhancedRelationType,
    EnhancedSyntaxNode, EnhancedSyntaxRelation,
    NodeType, RelationType
)

logger = logging.getLogger(__name__)


class DataModelMigrator:
    """データモデル移行管理クラス"""
    
    def __init__(self, uri: str, user: str, password: str):
        """Neo4jデータベース接続の初期化"""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.migration_log = []
    
    def close(self):
        """データベース接続を閉じる"""
        if self.driver:
            self.driver.close()
    
    def check_migration_status(self) -> Dict[str, Any]:
        """マイグレーション状況をチェック"""
        with self.driver.session() as session:
            # 既存ノードタイプの確認
            existing_node_types = session.run(
                "MATCH (n) RETURN DISTINCT labels(n) as labels"
            )
            node_types = set()
            for record in existing_node_types:
                node_types.update(record["labels"])
            
            # 既存リレーションタイプの確認
            existing_relation_types = session.run(
                "MATCH ()-[r]->() RETURN DISTINCT type(r) as relation_type"
            )
            relation_types = {record["relation_type"] for record in existing_relation_types}
            
            # 拡張フィールドの存在確認
            enhanced_properties = session.run(
                """
                MATCH (n) 
                WITH keys(n) as props
                UNWIND props as prop
                RETURN DISTINCT prop
                """
            )
            properties = {record["prop"] for record in enhanced_properties}
            
            # マイグレーション必要性の判定
            needs_migration = self._needs_migration(node_types, relation_types, properties)
            
            return {
                "existing_node_types": list(node_types),
                "existing_relation_types": list(relation_types),
                "existing_properties": list(properties),
                "needs_migration": needs_migration,
                "migration_plan": self._create_migration_plan(needs_migration)
            }
    
    def _needs_migration(self, node_types: set, relation_types: set, properties: set) -> Dict[str, bool]:
        """マイグレーション必要性を判定"""
        enhanced_node_types = {node_type.value for node_type in EnhancedNodeType}
        enhanced_relation_types = {rel_type.value for rel_type in EnhancedRelationType}
        enhanced_properties = {
            'function_analysis', 'class_analysis', 'error_analysis', 'performance_info',
            'semantic_tags', 'quality_score', 'usage_frequency', 'embeddings',
            'confidence_score', 'semantic_similarity', 'functional_similarity'
        }
        
        return {
            "node_types": not enhanced_node_types.issubset(node_types),
            "relation_types": not enhanced_relation_types.issubset(relation_types),
            "properties": not enhanced_properties.issubset(properties),
            "constraints": True,  # 制約は常にチェックが必要
            "indexes": True       # インデックスも常にチェック
        }
    
    def _create_migration_plan(self, needs_migration: Dict[str, bool]) -> List[Dict[str, Any]]:
        """マイグレーション計画を作成"""
        plan = []
        
        if needs_migration.get("constraints", False):
            plan.append({
                "step": "create_constraints",
                "description": "拡張データモデル用の制約を作成",
                "priority": 1
            })
        
        if needs_migration.get("indexes", False):
            plan.append({
                "step": "create_indexes",
                "description": "パフォーマンス向上用のインデックスを作成",
                "priority": 2
            })
        
        if needs_migration.get("properties", False):
            plan.append({
                "step": "add_enhanced_properties",
                "description": "既存ノードに拡張プロパティを追加",
                "priority": 3
            })
        
        if needs_migration.get("node_types", False):
            plan.append({
                "step": "migrate_node_types",
                "description": "新しいノードタイプの作成とマッピング",
                "priority": 4
            })
        
        if needs_migration.get("relation_types", False):
            plan.append({
                "step": "migrate_relation_types",
                "description": "新しいリレーションタイプの作成とマッピング",
                "priority": 5
            })
        
        return sorted(plan, key=lambda x: x["priority"])
    
    def execute_migration(self, dry_run: bool = True) -> Dict[str, Any]:
        """マイグレーションを実行"""
        migration_status = self.check_migration_status()
        migration_plan = migration_status["migration_plan"]
        
        results = {
            "dry_run": dry_run,
            "timestamp": datetime.now().isoformat(),
            "plan": migration_plan,
            "results": [],
            "errors": []
        }
        
        if not migration_plan:
            logger.info("マイグレーションは不要です")
            return results
        
        try:
            with self.driver.session() as session:
                for step in migration_plan:
                    step_name = step["step"]
                    logger.info(f"実行中: {step['description']}")
                    
                    if dry_run:
                        results["results"].append({
                            "step": step_name,
                            "status": "dry_run",
                            "message": f"[DRY RUN] {step['description']}"
                        })
                    else:
                        try:
                            result = self._execute_migration_step(session, step_name)
                            results["results"].append({
                                "step": step_name,
                                "status": "success",
                                "result": result
                            })
                        except Exception as e:
                            error_msg = f"ステップ {step_name} でエラー: {str(e)}"
                            logger.error(error_msg)
                            results["errors"].append({
                                "step": step_name,
                                "error": error_msg
                            })
        
        except Exception as e:
            logger.error(f"マイグレーション実行エラー: {str(e)}")
            results["errors"].append({
                "step": "general",
                "error": str(e)
            })
        
        return results
    
    def _execute_migration_step(self, session, step_name: str) -> Dict[str, Any]:
        """個別のマイグレーションステップを実行"""
        if step_name == "create_constraints":
            return self._create_constraints(session)
        elif step_name == "create_indexes":
            return self._create_indexes(session)
        elif step_name == "add_enhanced_properties":
            return self._add_enhanced_properties(session)
        elif step_name == "migrate_node_types":
            return self._migrate_node_types(session)
        elif step_name == "migrate_relation_types":
            return self._migrate_relation_types(session)
        else:
            raise ValueError(f"未知のマイグレーションステップ: {step_name}")
    
    def _create_constraints(self, session) -> Dict[str, Any]:
        """制約を作成"""
        constraints = [
            "CREATE CONSTRAINT enhanced_node_id IF NOT EXISTS FOR (n:EnhancedNode) REQUIRE n.node_id IS UNIQUE",
            "CREATE CONSTRAINT function_name IF NOT EXISTS FOR (n:Function) REQUIRE n.name IS NOT NULL",
            "CREATE CONSTRAINT class_name IF NOT EXISTS FOR (n:Class) REQUIRE n.name IS NOT NULL"
        ]
        
        created_count = 0
        for constraint in constraints:
            try:
                session.run(constraint)
                created_count += 1
                logger.info(f"制約作成成功: {constraint}")
            except Exception as e:
                logger.warning(f"制約作成スキップ (既存の可能性): {constraint}, エラー: {str(e)}")
        
        return {"created_constraints": created_count}
    
    def _create_indexes(self, session) -> Dict[str, Any]:
        """インデックスを作成"""
        indexes = [
            "CREATE INDEX enhanced_node_type IF NOT EXISTS FOR (n:EnhancedNode) ON (n.node_type)",
            "CREATE INDEX enhanced_node_name IF NOT EXISTS FOR (n:EnhancedNode) ON (n.name)",
            "CREATE INDEX enhanced_quality_score IF NOT EXISTS FOR (n:EnhancedNode) ON (n.quality_score)",
            "CREATE INDEX enhanced_usage_frequency IF NOT EXISTS FOR (n:EnhancedNode) ON (n.usage_frequency)",
            "CREATE INDEX relation_confidence IF NOT EXISTS FOR ()-[r:ENHANCED_RELATION]-() ON (r.confidence_score)",
            "CREATE INDEX semantic_similarity IF NOT EXISTS FOR ()-[r:ENHANCED_RELATION]-() ON (r.semantic_similarity)"
        ]
        
        created_count = 0
        for index in indexes:
            try:
                session.run(index)
                created_count += 1
                logger.info(f"インデックス作成成功: {index}")
            except Exception as e:
                logger.warning(f"インデックス作成スキップ (既存の可能性): {index}, エラー: {str(e)}")
        
        return {"created_indexes": created_count}
    
    def _add_enhanced_properties(self, session) -> Dict[str, Any]:
        """既存ノードに拡張プロパティを追加"""
        # 既存ノードに拡張プロパティのデフォルト値を設定
        updates = [
            """
            MATCH (n) 
            WHERE n.quality_score IS NULL 
            SET n.quality_score = 0.0, 
                n.usage_frequency = 0, 
                n.source_confidence = 1.0,
                n.semantic_tags = '[]',
                n.last_updated = datetime()
            RETURN count(n) as updated_nodes
            """,
            """
            MATCH ()-[r]->() 
            WHERE r.confidence_score IS NULL 
            SET r.confidence_score = 1.0,
                r.semantic_similarity = 0.0,
                r.functional_similarity = 0.0,
                r.usage_frequency = 0,
                r.discovery_method = 'legacy',
                r.quality_score = 0.0
            RETURN count(r) as updated_relations
            """
        ]
        
        results = {}
        for update in updates:
            result = session.run(update)
            record = result.single()
            if record:
                if 'updated_nodes' in record:
                    results['updated_nodes'] = record['updated_nodes']
                elif 'updated_relations' in record:
                    results['updated_relations'] = record['updated_relations']
        
        return results
    
    def _migrate_node_types(self, session) -> Dict[str, Any]:
        """ノードタイプのマイグレーション"""
        # 既存のノードに :EnhancedNode ラベルを追加
        result = session.run("""
            MATCH (n) 
            WHERE NOT n:EnhancedNode 
            SET n:EnhancedNode
            RETURN count(n) as migrated_nodes
        """)
        
        record = result.single()
        migrated_count = record['migrated_nodes'] if record else 0
        
        return {"migrated_nodes": migrated_count}
    
    def _migrate_relation_types(self, session) -> Dict[str, Any]:
        """リレーションタイプのマイグレーション"""
        # 既存のリレーションタイプをマッピング
        migration_mapping = {
            "CONTAINS": "CONTAINS",
            "CALLS": "CALLS",
            "USES": "USES",
            "IMPORTS": "IMPORTS"
        }
        
        migrated_count = 0
        for old_type, new_type in migration_mapping.items():
            # 必要に応じてリレーションタイプの変換処理を実装
            # 現在は同じ名前なので変換不要
            pass
        
        return {"migrated_relations": migrated_count}
    
    def backup_database(self, backup_path: str = None) -> Dict[str, Any]:
        """データベースのバックアップ"""
        if backup_path is None:
            backup_path = f"neo4j_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.cypher"
        
        with self.driver.session() as session:
            # ノードのエクスポート
            nodes_result = session.run("""
                MATCH (n) 
                RETURN n, labels(n) as labels, id(n) as internal_id
            """)
            
            # リレーションのエクスポート
            relations_result = session.run("""
                MATCH (a)-[r]->(b) 
                RETURN a.node_id as source_id, b.node_id as target_id, 
                       type(r) as relation_type, properties(r) as props
            """)
            
            backup_data = {
                "timestamp": datetime.now().isoformat(),
                "nodes": [],
                "relations": []
            }
            
            # ノードデータの収集
            for record in nodes_result:
                node = record["n"]
                backup_data["nodes"].append({
                    "properties": dict(node),
                    "labels": record["labels"],
                    "internal_id": record["internal_id"]
                })
            
            # リレーションデータの収集
            for record in relations_result:
                backup_data["relations"].append({
                    "source_id": record["source_id"],
                    "target_id": record["target_id"],
                    "relation_type": record["relation_type"],
                    "properties": record["props"]
                })
            
            # バックアップファイルの保存
            try:
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, ensure_ascii=False, indent=2)
                
                return {
                    "success": True,
                    "backup_path": backup_path,
                    "nodes_count": len(backup_data["nodes"]),
                    "relations_count": len(backup_data["relations"])
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
    
    def validate_migration(self) -> Dict[str, Any]:
        """マイグレーション後の検証"""
        with self.driver.session() as session:
            # データ整合性チェック
            validation_results = {}
            
            # 1. 必須プロパティの存在確認
            missing_props_result = session.run("""
                MATCH (n:EnhancedNode) 
                WHERE n.node_id IS NULL OR n.node_type IS NULL OR n.name IS NULL
                RETURN count(n) as missing_required_props
            """)
            validation_results["missing_required_properties"] = missing_props_result.single()["missing_required_props"]
            
            # 2. 拡張プロパティの存在確認
            enhanced_props_result = session.run("""
                MATCH (n:EnhancedNode) 
                WHERE n.quality_score IS NOT NULL AND n.usage_frequency IS NOT NULL
                RETURN count(n) as nodes_with_enhanced_props
            """)
            validation_results["nodes_with_enhanced_properties"] = enhanced_props_result.single()["nodes_with_enhanced_props"]
            
            # 3. リレーションの整合性確認
            orphan_relations_result = session.run("""
                MATCH ()-[r]->() 
                WHERE r.confidence_score IS NULL
                RETURN count(r) as relations_missing_enhanced_props
            """)
            validation_results["relations_missing_enhanced_properties"] = orphan_relations_result.single()["relations_missing_enhanced_props"]
            
            # 4. データ型の確認
            type_errors_result = session.run("""
                MATCH (n:EnhancedNode) 
                WHERE NOT (n.quality_score >= 0.0 AND n.quality_score <= 1.0)
                   OR NOT (n.usage_frequency >= 0)
                RETURN count(n) as type_errors
            """)
            validation_results["data_type_errors"] = type_errors_result.single()["type_errors"]
            
            # 検証結果の評価
            is_valid = all([
                validation_results["missing_required_properties"] == 0,
                validation_results["relations_missing_enhanced_properties"] == 0,
                validation_results["data_type_errors"] == 0
            ])
            
            return {
                "is_valid": is_valid,
                "validation_results": validation_results,
                "timestamp": datetime.now().isoformat()
            }


def create_migration_script(output_path: str = "migration_script.py") -> str:
    """マイグレーション実行スクリプトを生成"""
    script_content = '''#!/usr/bin/env python3
"""
Neo4j Enhanced Data Model Migration Script

使用方法:
    python migration_script.py --uri bolt://localhost:7687 --user neo4j --password password
    
オプション:
    --dry-run: 実際の変更を行わずに計画のみ表示
    --backup: マイグレーション前にバックアップを作成
"""

import argparse
import json
from enhanced_data_migration import DataModelMigrator

def main():
    parser = argparse.ArgumentParser(description='Neo4j Enhanced Data Model Migration')
    parser.add_argument('--uri', default='bolt://localhost:7687', help='Neo4j URI')
    parser.add_argument('--user', default='neo4j', help='Neo4j username')
    parser.add_argument('--password', required=True, help='Neo4j password')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    parser.add_argument('--backup', action='store_true', help='Create backup before migration')
    
    args = parser.parse_args()
    
    migrator = DataModelMigrator(args.uri, args.user, args.password)
    
    try:
        # バックアップ作成
        if args.backup:
            print("バックアップを作成中...")
            backup_result = migrator.backup_database()
            if backup_result["success"]:
                print(f"バックアップ完了: {backup_result['backup_path']}")
            else:
                print(f"バックアップエラー: {backup_result['error']}")
                return
        
        # マイグレーション状況確認
        print("マイグレーション状況を確認中...")
        status = migrator.check_migration_status()
        print(f"マイグレーション必要性: {status['needs_migration']}")
        
        # マイグレーション実行
        print("マイグレーションを実行中...")
        result = migrator.execute_migration(dry_run=args.dry_run)
        
        print("\\n=== マイグレーション結果 ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 検証
        if not args.dry_run and not result["errors"]:
            print("\\n検証中...")
            validation = migrator.validate_migration()
            print(f"検証結果: {'成功' if validation['is_valid'] else '失敗'}")
            if not validation["is_valid"]:
                print("検証詳細:", validation["validation_results"])
    
    finally:
        migrator.close()

if __name__ == "__main__":
    main()
'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    return output_path