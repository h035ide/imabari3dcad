# This script verifies the integrity of data imported into Neo4j from the parsed API documentation.
#
# 使用方法:
#   python verify_neo4j_data.py                    # デフォルトでdocparserデータベースを使用
#   python verify_neo4j_data.py --database neo4j   # 指定されたデータベースを使用
#   python verify_neo4j_data.py --save-docs        # 検証結果をドキュメントとして保存
#   python verify_neo4j_data.py --output-dir reports # カスタム出力ディレクトリを指定
#   python verify_neo4j_data.py --help            # ヘルプを表示
#
# 環境変数設定 (.envファイル):
#   NEO4J_URI=bolt://localhost:7687
#   NEO4J_USER=neo4j
#   NEO4J_PASSWORD=password
#   NEO4J_DATABASE=docparser (オプション、デフォルトはdocparser)

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv


class Neo4jVerifier:
    def __init__(self, uri, user, password, database="docparser"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database
        self.results = {}
        self.check_timestamp = None
        self.database_info = {}
        
        # JSONデータの読み込み
        self.json_data = self._load_json_data()
        if not self.json_data:
            raise ValueError("JSONデータを読み込めませんでした")

    def close(self):
        self.driver.close()

    def _load_json_data(self):
        """APIデータのJSONファイルを読み込む"""
        json_files = [
            os.path.join(os.path.dirname(__file__), '..', 'parsed_api_result_def.json'),
            os.path.join(os.path.dirname(__file__), '..', 'parsed_api_result.json')
        ]
        
        for json_path in json_files:
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    print(f"✅ Loaded API data from: {json_path}")
                    return json.load(f)
            except FileNotFoundError:
                continue
            except json.JSONDecodeError:
                print(f"❌ Error: Could not decode JSON from {json_path}")
                continue
        
        print("❌ Error: No valid JSON files found")
        return None

    def run_all_checks(self):
        """すべての検証チェックを実行"""
        self.check_timestamp = datetime.now()
        
        print("--- Starting Neo4j Data Verification ---")
        print(f"Check started at: {self.check_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Target database: {self.database}")
        
        self._get_database_info()
        
        checks = [
            ("Node Counts", self._check_node_counts),
            ("Function Integrity", self._check_function_integrity),
            ("Object Definition Integrity", self._check_object_definition_integrity),
            ("FEEDS_INTO Relationships", self._check_feeds_into_relationships),
            ("Orphan Nodes", self._check_orphan_nodes)
        ]
        
        for check_name, check_func in checks:
            print(f"\n[{len(self.results) + 1}] {check_name}...")
            check_func()
        
        print("-----------------------------------------")
        return self.results

    def _check_orphan_nodes(self):
        """孤立ノードの確認"""
        self.results['orphan_nodes'] = []
        
        with self.driver.session(database=self.database) as session:
            # 孤立したParameterノードを確認
            orphan_params = self._find_orphan_parameters(session)
            # リンクされていないObjectDefinitionノードを確認
            orphan_objs = self._find_orphan_object_definitions(session)
            
            if not orphan_params and not orphan_objs:
                print("  ✅ PASSED - No orphan nodes found.")
                self._add_result('orphan_nodes', True, "No orphan nodes found.")
            else:
                print(f"  ❌ FAILED - Found {len(orphan_params) + len(orphan_objs)} orphan/unlinked nodes.")

    def _find_orphan_parameters(self, session):
        """孤立したParameterノードを見つける"""
        query = """
        MATCH (p:Parameter)
        WHERE NOT (p)<-[:HAS_PARAMETER]-() AND NOT (p)<-[:HAS_PROPERTY]-()
        RETURN p.name, p.parent_function, p.parent_object
        """
        orphan_params = session.run(query).data()
        
        for p in orphan_params:
            details = f"Orphan Parameter found: {p['p.name']} (parent_function: {p.get('p.parent_function')}, parent_object: {p.get('p.parent_object')})"
            self._add_result('orphan_nodes', False, details)
        
        return orphan_params

    def _find_orphan_object_definitions(self, session):
        """リンクされていないObjectDefinitionノードを見つける"""
        query = """
        MATCH (od:ObjectDefinition)
        WHERE NOT ()-[:RETURNS]->(od) AND NOT ()-[:HAS_TYPE]->(od)
        RETURN od.name
        """
        orphan_objs = session.run(query).data()
        
        for obj in orphan_objs:
            details = f"Unlinked ObjectDefinition found: {obj['od.name']}"
            self._add_result('orphan_nodes', False, details)
        
        return orphan_objs

    def _check_feeds_into_relationships(self):
        """FEEDS_INTO関係の確認"""
        self.results['feeds_into'] = []
        
        # 期待される関係性をJSONから取得
        expected_rels = self._get_expected_feeds_into_relationships()
        
        # 実際の関係性をDBから取得
        actual_rels = self._get_actual_feeds_into_relationships()
        
        # 比較
        missing_rels = expected_rels - actual_rels
        extra_rels = actual_rels - expected_rels
        
        for rel in missing_rels:
            details = f"Missing FEEDS_INTO: ({rel[0]}) -> ({rel[1]}) via [{rel[2]}]"
            self._add_result('feeds_into', False, details)

        for rel in extra_rels:
            details = f"Unexpected FEEDS_INTO: ({rel[0]}) -> ({rel[1]}) via [{rel[2]}]"
            self._add_result('feeds_into', False, details)

        passed_count = len(expected_rels) - len(missing_rels)
        total_count = len(expected_rels)

        if not missing_rels and not extra_rels:
            print(f"  ✅ PASSED - All {total_count} FEEDS_INTO relationships are correct.")
            self._add_result('feeds_into', True, f"All {total_count} FEEDS_INTO relationships verified.")
        else:
            print(f"  ❌ FAILED - Verified {passed_count}/{total_count} correctly. Found {len(missing_rels)} missing and {len(extra_rels)} extra relationships.")

    def _get_expected_feeds_in_to_relationships(self):
        """JSONから期待されるFEEDS_INTO関係性を取得"""
        functions = {f['name']: f for f in self.json_data['api_entries'] if f['entry_type'] == 'function'}
        object_defs = {o['name'] for o in self.json_data['api_entries'] if o['entry_type'] == 'object_definition'}

        expected_rels = set()
        for func_name, func_data in functions.items():
            return_type = func_data.get('returns', {}).get('type')
            if return_type in object_defs:
                for consumer_name, consumer_data in functions.items():
                    for param in consumer_data.get('params', []):
                        if param.get('type') == return_type:
                            expected_rels.add((func_name, consumer_name, return_type))
        
        return expected_rels

    def _get_actual_feeds_in_to_relationships(self):
        """DBから実際のFEEDS_INTO関係性を取得"""
        with self.driver.session(database=self.database) as session:
            query = "MATCH (a:Function)-[r:FEEDS_INTO]->(b:Function) RETURN a.name, b.name, r.via_object"
            records = session.run(query).data()
            return {(r['a.name'], r['b.name'], r['r.via_object']) for r in records}

    def _check_object_definition_integrity(self):
        """オブジェクト定義の整合性確認"""
        self.results['object_definition_integrity'] = []
        obj_defs_in_json = [entry for entry in self.json_data.get('api_entries', []) 
                           if entry.get('entry_type') == 'object_definition']

        with self.driver.session(database=self.database) as session:
            for obj_json in obj_defs_in_json:
                self._verify_single_object_definition(session, obj_json)

        self._print_check_summary('object_definition_integrity', obj_defs_in_json)

    def _verify_single_object_definition(self, session, obj_json):
        """単一のオブジェクト定義を検証"""
        obj_name = obj_json['name']
        
        query = """
        MATCH (od:ObjectDefinition {name: $obj_name})
        OPTIONAL MATCH (od)-[:HAS_PROPERTY]->(p:Parameter)
        WITH od, p
        OPTIONAL MATCH (p)-[:HAS_TYPE]->(t)
        RETURN od.description as description,
               p.name as prop_name,
               p.description as prop_desc,
               t.name as prop_type
        """
        records = session.run(query, obj_name=obj_name).data()

        if not records:
            self._add_result('object_definition_integrity', False, 
                           f"ObjectDefinition '{obj_name}' not found in DB.")
            return

        # プロパティの検証
        json_props = obj_json.get('properties', [])
        db_props_list = [r for r in records if r['prop_name']]
        
        if len(json_props) != len(db_props_list):
            self._add_result('object_definition_integrity', False, 
                           f"ObjectDefinition '{obj_name}' has wrong property count. JSON: {len(json_props)}, DB: {len(db_props_list)}")
            return

        # 各プロパティの詳細検証
        all_props_match = self._verify_object_properties(obj_json, db_props_list, obj_name)
        
        if all_props_match and len(json_props) == len(db_props_list):
            self._add_result('object_definition_integrity', True, 
                           f"ObjectDefinition '{obj_name}' and its properties are consistent.")

    def _verify_object_properties(self, obj_json, db_props_list, obj_name):
        """オブジェクトのプロパティを検証"""
        json_props = obj_json.get('properties', [])
        all_props_match = True
        
        for prop_json in json_props:
            prop_found = any(
                prop_json['name'] == prop_db.get('prop_name') and 
                prop_json['type'] == prop_db.get('prop_type') 
                for prop_db in db_props_list
            )
            
            if not prop_found:
                all_props_match = False
                self._add_result('object_definition_integrity', False, 
                               f"Property '{prop_json['name']}' of ObjectDefinition '{obj_name}' not found or has mismatched type.")
        
        return all_props_match

    def _check_function_integrity(self):
        """関数とパラメータの整合性確認"""
        self.results['function_integrity'] = []
        functions_in_json = [entry for entry in self.json_data.get('api_entries', []) 
                           if entry.get('entry_type') == 'function']

        with self.driver.session(database=self.database) as session:
            for func_json in functions_in_json:
                self._verify_single_function(session, func_json)

        self._print_check_summary('function_integrity', functions_in_json)

    def _verify_single_function(self, session, func_json):
        """単一の関数を検証"""
        func_name = func_json['name']
        
        query = """
        MATCH (f:Function {name: $func_name})
        OPTIONAL MATCH (f)-[r:HAS_PARAMETER]->(p:Parameter)
        WITH f, r, p
        OPTIONAL MATCH (p)-[:HAS_TYPE]->(t)
        RETURN f.description as description,
               r.position as position,
               p.name as param_name,
               p.description as param_desc,
               t.name as param_type
        """
        records = session.run(query, func_name=func_name).data()

        if not records:
            self._add_result('function_integrity', False, f"Function '{func_name}' not found in DB.")
            return

        # 関数の説明を検証
        if records[0]['description'] != func_json.get('description'):
            self._add_result('function_integrity', False, f"Function '{func_name}' description mismatch.")

        # パラメータの検証
        json_params = func_json.get('params', [])
        db_params_list = [r for r in records if r['param_name']]
        
        if len(json_params) != len(db_params_list):
            self._add_result('function_integrity', False, 
                           f"Function '{func_name}' has wrong parameter count. JSON: {len(json_params)}, DB: {len(db_params_list)}")
            return

        # 各パラメータの詳細検証
        all_params_match = self._verify_function_parameters(func_json, db_params_list, func_name)
        
        if all_params_match and len(json_params) == len(db_params_list):
            self._add_result('function_integrity', True, f"Function '{func_name}' and its parameters are consistent.")

    def _verify_function_parameters(self, func_json, db_params_list, func_name):
        """関数のパラメータを検証"""
        json_params = func_json.get('params', [])
        all_params_match = True
        
        for param_json in json_params:
            param_found = False
            for param_db in db_params_list:
                if param_json['name'] == param_db['param_name']:
                    param_found = True
                    # 位置とタイプをチェック
                    if (param_json.get('position') != param_db.get('position') or 
                        param_json.get('type') != param_db.get('param_type')):
                        all_params_match = False
                        self._add_result('function_integrity', False, 
                                       f"Parameter '{param_json['name']}' of function '{func_name}' has mismatched properties (position/type).")
                    break
            
            if not param_found:
                all_params_match = False
                self._add_result('function_integrity', False, 
                               f"Parameter '{param_json['name']}' of function '{func_name}' not found in DB.")
        
        return all_params_match

    def _check_node_counts(self):
        """ノード数の確認"""
        self.results['node_counts'] = []
        
        checks = {
            "Function": {"label": "Function", "json_key": "api_entries", "filter": lambda x: x['entry_type'] == 'function'},
            "ObjectDefinition": {"label": "ObjectDefinition", "json_key": "api_entries", "filter": lambda x: x['entry_type'] == 'object_definition'},
            "Type": {"label": "Type", "json_key": "type_definitions", "filter": lambda x: True},
        }

        with self.driver.session(database=self.database) as session:
            for name, check in checks.items():
                self._verify_node_count(session, name, check)

    def _verify_node_count(self, session, name, check):
        """単一のノードタイプの数を検証"""
        # JSONからカウント
        json_count = len([item for item in self.json_data[check['json_key']] if check['filter'](item)])

        # Neo4jからカウント
        query = f"MATCH (n:{check['label']}) RETURN count(n) as count"
        result = session.run(query).single()
        db_count = result['count'] if result else 0

        # 比較と結果の保存
        is_match = json_count == db_count
        status = "✅ PASSED" if is_match else "❌ FAILED"
        message = f"{name} count: JSON ({json_count}) vs DB ({db_count})"
        print(f"  {status} - {message}")
        
        self.results['node_counts'].append({
            "check": f"{name} count",
            "passed": is_match,
            "details": message
        })

    def _get_database_info(self):
        """データベースの基本情報を取得"""
        try:
            with self.driver.session(database=self.database) as session:
                # ノード統計
                stats_query = """
                MATCH (n)
                RETURN labels(n) as labels, count(n) as count
                ORDER BY count DESC
                """
                stats_result = session.run(stats_query).data()
                
                # 関係性統計
                rel_query = """
                MATCH ()-[r]->()
                RETURN type(r) as relationship_type, count(r) as count
                ORDER BY count DESC
                """
                rel_result = session.run(rel_query).data()
                
                self.database_info = {
                    "database_name": self.database,
                    "node_statistics": stats_result,
                    "relationship_statistics": rel_result,
                    "check_timestamp": self.check_timestamp.isoformat() if self.check_timestamp else None
                }
        except Exception as e:
            print(f"Warning: Could not retrieve database statistics: {e}")
            self.database_info = {"database_name": self.database, "error": str(e)}

    def _add_result(self, category, passed, details):
        """検証結果を追加"""
        if category not in self.results:
            self.results[category] = []

        if not passed:
            print(f"  ❌ FAILED: {details}")

        self.results[category].append({
            "check": details.split("'")[1] if "'" in details else "General Check",
            "passed": passed,
            "details": details
        })

    def _print_check_summary(self, category, items):
        """チェック結果のサマリーを表示"""
        passed_count = sum(1 for r in self.results[category] if r['passed'])
        total_count = len(items)
        status = "✅ PASSED" if passed_count == total_count else "❌ FAILED"
        print(f"  {status} - Verified {passed_count}/{total_count} successfully.")

    def save_results_as_markdown(self, output_dir="verification_reports"):
        """チェック結果をMarkdownファイルとして保存"""
        output_path = Path(__file__).parent / output_dir
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp_str = self.check_timestamp.strftime("%Y%m%d_%H%M%S") if self.check_timestamp else "unknown"
        filename = f"neo4j_verification_{self.database}_{timestamp_str}.md"
        filepath = output_path / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                self._write_markdown_header(f)
                self._write_database_info(f)
                self._write_verification_summary(f)
                self._write_detailed_results(f)
                self._write_recommendations(f)
                self._write_footer(f)
            
            print(f"✅ 検証レポートを保存しました: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ レポート保存中にエラーが発生しました: {e}")
            return None

    def _write_markdown_header(self, f):
        """Markdownヘッダーを書き込み"""
        f.write(f"# Neo4j データベース検証レポート\n\n")
        f.write(f"**データベース名**: {self.database}\n")
        f.write(f"**検証日時**: {self.check_timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.check_timestamp else 'Unknown'}\n")
        f.write(f"**生成元**: verify_neo4j_data.py\n\n")

    def _write_database_info(self, f):
        """データベース情報を書き込み"""
        f.write("## データベース基本情報\n\n")
        if self.database_info:
            f.write(f"- **データベース名**: {self.database_info.get('database_name', 'Unknown')}\n")
            
            if 'node_statistics' in self.database_info:
                f.write("\n### ノード統計\n")
                for stat in self.database_info['node_statistics']:
                    labels = ', '.join(stat['labels']) if stat['labels'] else 'No Label'
                    f.write(f"- {labels}: {stat['count']}個\n")
            
            if 'relationship_statistics' in self.database_info:
                f.write("\n### 関係性統計\n")
                for rel in self.database_info['relationship_statistics']:
                    f.write(f"- {rel['relationship_type']}: {rel['count']}個\n")

    def _write_verification_summary(self, f):
        """検証結果サマリーを書き込み"""
        f.write("\n## 検証結果サマリー\n\n")
        total_checks = 0
        passed_checks = 0
        
        for category, checks in self.results.items():
            if checks:
                category_passed = sum(1 for check in checks if check['passed'])
                category_total = len(checks)
                total_checks += category_total
                passed_checks += category_passed
                
                status_icon = "✅" if category_passed == category_total else "❌"
                f.write(f"- **{category}**: {status_icon} {category_passed}/{category_total} 通過\n")
        
        overall_status = "✅ 全検証通過" if passed_checks == total_checks else "❌ 一部検証失敗"
        f.write(f"\n**全体結果**: {overall_status} ({passed_checks}/{total_checks})\n")

    def _write_detailed_results(self, f):
        """詳細検証結果を書き込み"""
        f.write("\n## 詳細検証結果\n\n")
        
        for category, checks in self.results.items():
            if checks:
                f.write(f"### {category.replace('_', ' ').title()}\n\n")
                
                for check in checks:
                    status_icon = "✅" if check['passed'] else "❌"
                    f.write(f"{status_icon} **{check['check']}**\n")
                    f.write(f"   - 詳細: {check['details']}\n\n")

    def _write_recommendations(self, f):
        """推奨事項を書き込み"""
        f.write("## 推奨事項\n\n")
        
        total_checks = sum(len(checks) for checks in self.results.values())
        passed_checks = sum(sum(1 for check in checks if check['passed']) for checks in self.results.values())
        
        if passed_checks == total_checks:
            f.write("✅ すべての検証が通過しました。データベースの整合性は良好です。\n")
        else:
            f.write("❌ 一部の検証が失敗しました。以下の点を確認してください：\n\n")
            for category, checks in self.results.items():
                failed_checks = [check for check in checks if not check['passed']]
                if failed_checks:
                    f.write(f"### {category.replace('_', ' ').title()}\n")
                    for check in failed_checks:
                        f.write(f"- {check['details']}\n")
                    f.write("\n")

    def _write_footer(self, f):
        """フッターを書き込み"""
        f.write("\n---\n")
        f.write(f"*このレポートは {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} に自動生成されました。*")

    def save_results_as_json(self, output_dir="verification_reports"):
        """チェック結果をJSONファイルとして保存"""
        output_path = Path(__file__).parent / output_dir
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp_str = self.check_timestamp.strftime("%Y%m%d_%H%M%S") if self.check_timestamp else "unknown"
        filename = f"neo4j_verification_{self.database}_{timestamp_str}.json"
        filepath = output_path / filename
        
        try:
            export_data = {
                "metadata": {
                    "database_name": self.database,
                    "check_timestamp": self.check_timestamp.isoformat() if self.check_timestamp else None,
                    "generator": "verify_neo4j_data.py",
                    "export_timestamp": datetime.now().isoformat()
                },
                "database_info": self.database_info,
                "verification_results": self.results,
                "summary": self._generate_summary()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 検証結果JSONを保存しました: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ JSON保存中にエラーが発生しました: {e}")
            return None

    def _generate_summary(self):
        """検証結果のサマリーを生成"""
        total_checks = 0
        passed_checks = 0
        category_summary = {}
        
        for category, checks in self.results.items():
            if checks:
                category_passed = sum(1 for check in checks if check['passed'])
                category_total = len(checks)
                total_checks += category_total
                passed_checks += category_total
                
                category_summary[category] = {
                    "passed": category_passed,
                    "total": category_total,
                    "status": "passed" if category_passed == category_total else "failed"
                }
        
        return {
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": total_checks - passed_checks,
            "overall_status": "passed" if passed_checks == total_checks else "failed",
            "category_summary": category_summary
        }


def main():
    parser = argparse.ArgumentParser(
        description='Neo4jにインポートされたAPIデータの整合性を検証するスクリプト',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python verify_neo4j_data.py                    # デフォルトでdocparserデータベースを使用
  python verify_neo4j_data.py --database neo4j   # 指定されたデータベースを使用
  python verify_neo4j_data.py --save-docs        # 検証結果をドキュメントとして保存
  python verify_neo4j_data.py --output-dir reports # カスタム出力ディレクトリを指定
        """
    )
    
    parser.add_argument('--database', type=str, default='docparser',
                      help='使用するNeo4jデータベース名 (デフォルト: docparser)')
    parser.add_argument('--save-docs', action='store_true',
                      help='検証結果をMarkdownとJSONファイルとして保存')
    parser.add_argument('--output-dir', type=str, default='verification_reports',
                      help='ドキュメント保存先ディレクトリ (デフォルト: verification_reports)')
    
    args = parser.parse_args()
    
    load_dotenv()

    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USER = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
    NEO4J_DATABASE = args.database

    if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
        print("Error: NEO4J_URI, NEO4J_USER (or NEO4J_USERNAME), and NEO4J_PASSWORD must be set in the .env file.")
        return

    print(f"🔍 Neo4j Data Verification for database: {NEO4J_DATABASE}")
    if NEO4J_DATABASE == "docparser":
        print("  → APIドキュメント解析データを格納するdocparserデータベースを検証します")

    try:
        verifier = Neo4jVerifier(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE)
        results = verifier.run_all_checks()

        print("\n--- Verification Summary ---")
        all_passed = all(all(check['passed'] for check in checks) for checks in results.values())

        if all_passed:
            print("✅ All verification checks passed!")
        else:
            print("\nSome verification checks failed.")
            for category, checks in results.items():
                for check in checks:
                    if not check['passed']:
                        print(f"❌ FAILED: {check['check']} - {check['details']}")

        # ドキュメント保存
        if args.save_docs:
            print(f"\n📄 検証結果をドキュメントとして保存中...")
            print(f"出力ディレクトリ: {args.output_dir}")
            
            md_file = verifier.save_results_as_markdown(args.output_dir)
            json_file = verifier.save_results_as_json(args.output_dir)
            
            if md_file and json_file:
                print(f"\n✅ ドキュメント保存完了:")
                print(f"  📝 Markdown: {md_file}")
                print(f"  📊 JSON: {json_file}")
            else:
                print(f"\n⚠️ 一部のドキュメント保存に失敗しました")

    except ValueError as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        if 'verifier' in locals():
            verifier.close()


if __name__ == "__main__":
    # プロジェクトルートをPythonパスに追加
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    main()
