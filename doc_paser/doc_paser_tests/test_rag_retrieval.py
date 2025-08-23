# This script runs specification tests for GraphRAG data retrieval from Neo4j database.
#
# 使用方法:
#   python test_rag_retrieval.py                    # デフォルトでdocparserデータベースを使用
#   python test_rag_retrieval.py --database neo4j   # 指定されたデータベースを使用
#   python test_rag_retrieval.py --save-docs        # テスト結果をドキュメントとして保存
#   python test_rag_retrieval.py --output-dir reports # カスタム出力ディレクトリを指定
#   python test_rag_retrieval.py test_patterns/     # 特定のテストパターンディレクトリを指定
#   python test_rag_retrieval.py --help            # ヘルプを表示
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
import importlib.util
from datetime import datetime
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv

# 相対インポートの問題を解決
try:
    from .test_dsl import FunctionSpec, Param
except ImportError:
    sys.path.append(os.path.dirname(__file__))
    try:
        from test_dsl import FunctionSpec, Param
    except ImportError:
        print("Warning: test_dsl module not found. Some functionality may be limited.")
        FunctionSpec = None
        Param = None


class RagRetriever:
    def __init__(self, uri, user, password, database="docparser"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database
        self.test_results = []
        self.test_timestamp = None
        self.database_info = {}

    def close(self):
        self.driver.close()

    def _get_database_info(self):
        """データベースの基本情報を取得"""
        try:
            with self.driver.session(database=self.database) as session:
                queries = {
                    "function_count": "MATCH (f:Function) RETURN count(f) as count",
                    "parameter_count": "MATCH (p:Parameter) RETURN count(p) as count",
                    "object_count": "MATCH (od:ObjectDefinition) RETURN count(od) as count"
                }
                
                results = {}
                for key, query in queries.items():
                    result = session.run(query).single()
                    results[key] = result['count'] if result else 0
                
                self.database_info = {
                    "database_name": self.database,
                    "function_count": results["function_count"],
                    "parameter_count": results["parameter_count"],
                    "object_definition_count": results["object_count"],
                    "test_timestamp": self.test_timestamp.isoformat() if self.test_timestamp else None
                }
        except Exception as e:
            print(f"Warning: Could not retrieve database statistics: {e}")
            self.database_info = {"database_name": self.database, "error": str(e)}

    def get_function_spec(self, function_name):
        """関数の完全な仕様を取得"""
        with self.driver.session(database=self.database) as session:
            query = """
            MATCH (f:Function {name: $function_name})
            OPTIONAL MATCH (f)-[r:HAS_PARAMETER]->(p:Parameter)
            OPTIONAL MATCH (p)-[:HAS_TYPE]->(t)
            OPTIONAL MATCH (f)-[:RETURNS]->(ret)
            WITH f, ret, r, p, t
            ORDER BY r.position
            WITH f, ret, COLLECT(DISTINCT {
                name: p.name,
                description: p.description,
                position: r.position,
                type: t.name,
                is_object: 'ObjectDefinition' IN labels(t)
            }) as parameters
            RETURN
                f.name as name,
                f.description as description,
                parameters,
                ret.name as return_type,
                ret.description as return_description
            """
            result = session.run(query, function_name=function_name).single()

            if not result or not result['name']:
                print(f"Error: Function '{function_name}' not found.")
                return None

            spec = dict(result)
            # nullパラメータをフィルタリング
            spec['parameters'] = [p for p in spec['parameters'] if p['name'] is not None]
            # 位置でソート
            spec['parameters'] = sorted(spec['parameters'], key=lambda x: x.get('position', 0))

            # オブジェクトパラメータのプロパティを再帰的に取得
            for param in spec['parameters']:
                if param['is_object']:
                    param['properties'] = self._fetch_object_properties(session, param['type'])

            return spec

    def _fetch_object_properties(self, session, object_name):
        """オブジェクト定義のプロパティを再帰的に取得"""
        query = """
        MATCH (od:ObjectDefinition {name: $object_name})
        OPTIONAL MATCH (od)-[:HAS_PROPERTY]->(p:Parameter)
        OPTIONAL MATCH (p)-[:HAS_TYPE]->(t)
        RETURN
            p.name as name,
            p.description as description,
            t.name as type,
            'ObjectDefinition' IN labels(t) as is_object
        """
        records = session.run(query, object_name=object_name).data()

        properties = []
        for record in records:
            if not record['name']:
                continue
            prop = dict(record)
            if prop['is_object']:
                prop['properties'] = self._fetch_object_properties(session, prop['type'])
            properties.append(prop)

        return properties

    def display_spec(self, spec):
        """取得した仕様をユーザーフレンドリーな形式で表示"""
        if not spec:
            return

        print("\n--- API Specification ---")
        print(f"Function: {spec.get('name')}")
        print(f"  Description: {spec.get('description')}")
        print("-" * 25)

        print("Parameters:")
        if not spec.get('parameters'):
            print("  (None)")
        else:
            for param in spec['parameters']:
                self._display_parameter(param, indent_level=1)

        print("-" * 25)
        print("Returns:")
        print(f"  Type: {spec.get('return_type')}")
        print(f"  Description: {spec.get('return_description')}")
        print("-------------------------\n")

    def _display_parameter(self, param, indent_level=1):
        """パラメータを表示（再帰的）"""
        indent = "  " * indent_level
        print(f"{indent}- Name: {param.get('name')}")
        print(f"{indent}  Type: {param.get('type')}")
        print(f"{indent}  Description: {param.get('description')}")
        
        if 'properties' in param and param['properties']:
            print(f"{indent}  Properties:")
            for prop in param['properties']:
                self._display_parameter(prop, indent_level + 2)

    def run_test_cases_from_file(self, pattern_path):
        """テストパターンファイルからテストケースを読み込んで実行"""
        if FunctionSpec is None or Param is None:
            print(f"Warning: Skipping {pattern_path} - test_dsl module not available")
            self._add_test_result(os.path.basename(pattern_path), False, "test_dsl module not available")
            return
        
        # 初回実行時の初期化
        if not self.test_timestamp:
            self.test_timestamp = datetime.now()
            self._get_database_info()
        
        print(f"\nRunning tests from: {os.path.basename(pattern_path)}")
        
        try:
            module_name = os.path.splitext(os.path.basename(pattern_path))[0]
            spec = importlib.util.spec_from_file_location(module_name, pattern_path)
            test_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(test_module)
            test_cases = test_module.test_cases
        except (ImportError, AttributeError, FileNotFoundError) as e:
            details = f"Failed to load test cases from {pattern_path}: {e}"
            self._add_test_result(os.path.basename(pattern_path), False, details)
            return

        for case in test_cases:
            self._execute_single_test_case(case)

    def _execute_single_test_case(self, case):
        """単一のテストケースを実行"""
        test_name = case.get("test_name", "Unnamed Test")
        test_type = case.get("test_type", "positive")
        spec_obj = case.get("spec")

        if not spec_obj:
            self._add_test_result(test_name, False, "Test case is missing 'spec' definition.")
            return

        function_name = spec_obj.name
        expected_spec = spec_obj.to_dict()
        actual_spec = self.get_function_spec(function_name)
        
        if actual_spec is None:
            details = f"Function '{function_name}' not found in DB for test '{test_name}'."
            self._add_test_result(function_name, False, details, test_name)
            return

        # パラメータリストを一貫してソート
        if actual_spec.get('parameters'):
            actual_spec['parameters'] = sorted(actual_spec['parameters'], key=lambda p: p.get('position', 0))

        is_match, details = self._compare_specs(expected_spec, actual_spec)

        # テストタイプに基づいて結果を判定
        if test_type == 'positive':
            passed = is_match
            final_details = " | ".join(details) if not passed else "OK"
        else:  # negative
            passed = not is_match
            final_details = "Correctly identified mismatch." if passed else "Failed to identify expected mismatch."

        self._add_test_result(function_name, passed, final_details, test_name)

    def _compare_specs(self, expected, actual, path=""):
        """2つの辞書/リスト構造を再帰的に比較して差分を返す"""
        errors = []

        if isinstance(expected, dict) and isinstance(actual, dict):
            # キーをソートして順序の違いを処理
            expected_keys = sorted(expected.keys())
            actual_keys = sorted(actual.keys())

            if expected_keys != actual_keys:
                missing = set(expected_keys) - set(actual_keys)
                extra = set(actual_keys) - set(expected_keys)
                if missing:
                    errors.append(f"Missing keys at {path}: {missing}")
                if extra:
                    errors.append(f"Extra keys at {path}: {extra}")

            # 共通キーを比較
            common_keys = set(expected_keys) & set(actual_keys)
            for key in common_keys:
                new_path = f"{path}.{key}" if path else key
                if key in ['parameters', 'properties']:
                    continue  # パラメータリストは別途処理
                errors.extend(self._compare_specs(expected[key], actual[key], new_path)[1])

            # パラメータ/プロパティリストの特別処理
            for key in ['parameters', 'properties']:
                if key in common_keys:
                    new_path = f"{path}.{key}" if path else key
                    errors.extend(self._compare_lists(expected[key], actual[key], new_path))

        elif isinstance(expected, list) and isinstance(actual, list):
            errors.extend(self._compare_lists(expected, actual, path))

        elif expected != actual:
            errors.append(f"Value mismatch at {path}: Expected '{expected}', Got '{actual}'")

        return not errors, errors

    def _compare_lists(self, expected_list, actual_list, path):
        """リストを比較（パラメータ/プロパティ用）"""
        errors = []
        
        if len(expected_list) != len(actual_list):
            errors.append(f"List length mismatch at {path}: Expected {len(expected_list)}, Got {len(actual_list)}")
            return errors

        # 名前でキー化して比較
        expected_dict = {item['name']: item for item in expected_list}
        actual_dict = {item['name']: item for item in actual_list}

        if sorted(expected_dict.keys()) != sorted(actual_dict.keys()):
            missing = set(expected_dict.keys()) - set(actual_dict.keys())
            extra = set(actual_dict.keys()) - set(expected_dict.keys())
            if missing:
                errors.append(f"Missing items in list {path}: {missing}")
            if extra:
                errors.append(f"Extra items in list {path}: {extra}")
            return errors

        # 各アイテムの詳細比較
        for name, expected_item in expected_dict.items():
            actual_item = actual_dict[name]
            errors.extend(self._compare_specs(expected_item, actual_item, f"{path}[{name}]")[1])

        return errors

    def get_all_function_names(self):
        """データベースからすべての関数名を取得"""
        with self.driver.session(database=self.database) as session:
            query = "MATCH (f:Function) RETURN f.name as name ORDER BY f.name"
            records = session.run(query).data()
            return [r['name'] for r in records]

    def _add_test_result(self, function_name, passed, details, test_name=None):
        """テスト結果を追加"""
        result = {
            "function": function_name,
            "passed": passed,
            "details": details
        }
        if test_name:
            result["test_name"] = test_name
        self.test_results.append(result)

    def save_results_as_markdown(self, output_dir="verification_reports"):
        """テスト結果をMarkdownファイルとして保存"""
        output_path = Path(__file__).parent / output_dir
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp_str = self.test_timestamp.strftime("%Y%m%d_%H%M%S") if self.test_timestamp else "unknown"
        filename = f"rag_retrieval_test_{self.database}_{timestamp_str}.md"
        filepath = output_path / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                self._write_markdown_header(f)
                self._write_database_info(f)
                self._write_test_summary(f)
                self._write_detailed_results(f)
                self._write_recommendations(f)
                self._write_footer(f)
            
            print(f"✅ RAGテストレポートを保存しました: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ レポート保存中にエラーが発生しました: {e}")
            return None

    def _write_markdown_header(self, f):
        """Markdownヘッダーを書き込み"""
        f.write(f"# RAG Retrieval テストレポート\n\n")
        f.write(f"**データベース名**: {self.database}\n")
        f.write(f"**テスト日時**: {self.test_timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.test_timestamp else 'Unknown'}\n")
        f.write(f"**生成元**: test_rag_retrieval.py\n\n")

    def _write_database_info(self, f):
        """データベース情報を書き込み"""
        f.write("## データベース基本情報\n\n")
        if self.database_info:
            f.write(f"- **データベース名**: {self.database_info.get('database_name', 'Unknown')}\n")
            f.write(f"- **関数数**: {self.database_info.get('function_count', 0)}個\n")
            f.write(f"- **パラメータ数**: {self.database_info.get('parameter_count', 0)}個\n")
            f.write(f"- **オブジェクト定義数**: {self.database_info.get('object_definition_count', 0)}個\n")

    def _write_test_summary(self, f):
        """テスト結果サマリーを書き込み"""
        f.write("\n## テスト結果サマリー\n\n")
        passed_count = sum(1 for r in self.test_results if r.get('passed'))
        total_tests = len(self.test_results)
        
        f.write(f"- **総テスト数**: {total_tests}\n")
        f.write(f"- **通過テスト数**: {passed_count}\n")
        f.write(f"- **失敗テスト数**: {total_tests - passed_count}\n")
        f.write(f"- **成功率**: {(passed_count/total_tests*100):.1f}%\n\n")
        
        overall_status = "✅ 全テスト通過" if passed_count == total_tests else "❌ 一部テスト失敗"
        f.write(f"**全体結果**: {overall_status}\n")

    def _write_detailed_results(self, f):
        """詳細テスト結果を書き込み"""
        f.write("\n## 詳細テスト結果\n\n")
        
        # テストファイル別にグループ化
        test_files = {}
        for result in self.test_results:
            test_file = result.get('function', 'Unknown')
            if test_file not in test_files:
                test_files[test_file] = []
            test_files[test_file].append(result)
        
        for test_file, results in test_files.items():
            f.write(f"### {test_file}\n\n")
            
            file_passed = sum(1 for r in results if r.get('passed'))
            file_total = len(results)
            
            f.write(f"**ファイル結果**: {file_passed}/{file_total} 通過\n\n")
            
            for result in results:
                status_icon = "✅" if result.get('passed') else "❌"
                test_name = result.get('test_name', 'Unnamed Test')
                details = result.get('details', 'No details')
                
                f.write(f"{status_icon} **{test_name}**\n")
                f.write(f"   - 詳細: {details}\n\n")

    def _write_recommendations(self, f):
        """推奨事項を書き込み"""
        f.write("## 推奨事項\n\n")
        passed_count = sum(1 for r in self.test_results if r.get('passed'))
        total_tests = len(self.test_results)
        
        if passed_count == total_tests:
            f.write("✅ すべてのテストが通過しました。RAG検索機能は正常に動作しています。\n")
        else:
            f.write("❌ 一部のテストが失敗しました。以下の点を確認してください：\n\n")
            for result in self.test_results:
                if not result.get('passed'):
                    f.write(f"- **{result.get('function', 'Unknown')}**: {result.get('details', 'No details')}\n")

    def _write_footer(self, f):
        """フッターを書き込み"""
        f.write("\n---\n")
        f.write(f"*このレポートは {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} に自動生成されました。*")

    def save_results_as_json(self, output_dir="verification_reports"):
        """テスト結果をJSONファイルとして保存"""
        output_path = Path(__file__).parent / output_dir
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp_str = self.test_timestamp.strftime("%Y%m%d_%H%M%S") if self.test_timestamp else "unknown"
        filename = f"rag_retrieval_test_{self.database}_{timestamp_str}.json"
        filepath = output_path / filename
        
        try:
            export_data = {
                "metadata": {
                    "database_name": self.database,
                    "test_timestamp": self.test_timestamp.isoformat() if self.test_timestamp else None,
                    "generator": "test_rag_retrieval.py",
                    "export_timestamp": datetime.now().isoformat()
                },
                "database_info": self.database_info,
                "test_results": self.test_results,
                "summary": self._generate_test_summary()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ RAGテスト結果JSONを保存しました: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ JSON保存中にエラーが発生しました: {e}")
            return None

    def _generate_test_summary(self):
        """テスト結果のサマリーを生成"""
        passed_count = sum(1 for r in self.test_results if r.get('passed'))
        total_tests = len(self.test_results)
        
        # テストファイル別の統計
        test_files = {}
        for result in self.test_results:
            test_file = result.get('function', 'Unknown')
            if test_file not in test_files:
                test_files[test_file] = {"passed": 0, "total": 0}
            test_files[test_file]["total"] += 1
            if result.get('passed'):
                test_files[test_file]["passed"] += 1
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_count,
            "failed_tests": total_tests - passed_count,
            "success_rate": (passed_count/total_tests*100) if total_tests > 0 else 0,
            "overall_status": "passed" if passed_count == total_tests else "failed",
            "test_file_summary": test_files
        }

    def run_basic_function_test(self, function_name):
        """基本的な関数仕様テスト（test_dslがなくても動作）"""
        print(f"\n🔍 Basic function test for: {function_name}")
        
        if not self.test_timestamp:
            self.test_timestamp = datetime.now()
            self._get_database_info()
        
        spec = self.get_function_spec(function_name)
        if spec:
            self.display_spec(spec)
            self._add_test_result(function_name, True, "Function specification retrieved successfully")
            print(f"✅ Function '{function_name}' test passed")
        else:
            self._add_test_result(function_name, False, f"Function '{function_name}' not found in database")
            print(f"❌ Function '{function_name}' test failed")

    def list_available_functions(self):
        """利用可能な関数の一覧を表示"""
        print("\n📋 Available functions in database:")
        try:
            functions = self.get_all_function_names()
            if functions:
                for i, func_name in enumerate(functions, 1):
                    print(f"  {i:2d}. {func_name}")
                print(f"\nTotal: {len(functions)} functions")
            else:
                print("  No functions found in database")
        except Exception as e:
            print(f"  Error retrieving function list: {e}")

    def run_all_functions_basic_check(self):
        """全関数の基本的なチェックを実行"""
        print(f"\n🔍 Running comprehensive function check for all functions...")
        
        if not self.test_timestamp:
            self.test_timestamp = datetime.now()
            self._get_database_info()
        
        functions = self.get_all_function_names()
        if not functions:
            print("❌ No functions found in database")
            return
        
        print(f"📋 Found {len(functions)} functions to check")
        print("=" * 60)
        
        for i, func_name in enumerate(functions, 1):
            print(f"\n[{i:3d}/{len(functions)}] Checking: {func_name}")
            print("-" * 40)
            
            try:
                spec = self.get_function_spec(func_name)
                if spec:
                    print(f"✅ Function found")
                    print(f"   Description: {spec.get('description', 'No description')}")
                    print(f"   Parameters: {len(spec.get('parameters', []))}")
                    print(f"   Return Type: {spec.get('return_type', 'Unknown')}")
                    
                    self._add_test_result(func_name, True, 
                                        f"Function specification retrieved successfully - {len(spec.get('parameters', []))} parameters")
                else:
                    print(f"❌ Function not found")
                    self._add_test_result(func_name, False, f"Function '{func_name}' not found in database")
                    
            except Exception as e:
                print(f"❌ Error checking function: {e}")
                self._add_test_result(func_name, False, f"Error during check: {str(e)}")
        
        print("\n" + "=" * 60)
        print("🎯 Comprehensive function check completed!")
        
        # 統計情報を表示
        passed_count = sum(1 for r in self.test_results if r.get('passed'))
        total_count = len(self.test_results)
        print(f"📊 Results: {passed_count}/{total_count} functions passed")
        
        return self.test_results


def main():
    parser = argparse.ArgumentParser(
        description="Run specification tests for GraphRAG data retrieval.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python test_rag_retrieval.py                    # デフォルトでdocparserデータベースを使用
  python test_rag_retrieval.py --database neo4j   # 指定されたデータベースを使用
  python test_rag_retrieval.py --save-docs        # テスト結果をドキュメントとして保存
  python test_rag_retrieval.py --output-dir reports # カスタム出力ディレクトリを指定
  python test_rag_retrieval.py test_patterns/     # 特定のテストパターンディレクトリを指定
  python test_rag_retrieval.py --function CreateSolid # 特定の関数をテスト
  python test_rag_retrieval.py --list-functions   # 利用可能な関数一覧を表示
  python test_rag_retrieval.py --all-functions    # 全関数の基本的なチェックを実行
        """
    )
    
    parser.add_argument("test_path", nargs='?', default=None, 
                      help="Path to a specific test file or directory.")
    parser.add_argument('--database', type=str, default='docparser',
                      help='使用するNeo4jデータベース名 (デフォルト: docparser)')
    parser.add_argument('--save-docs', action='store_true',
                      help='テスト結果をMarkdownとJSONファイルとして保存')
    parser.add_argument('--output-dir', type=str, default='verification_reports',
                      help='ドキュメント保存先ディレクトリ (デフォルト: verification_reports)')
    parser.add_argument('--function', type=str, metavar='FUNCTION_NAME',
                      help='特定の関数をテスト（test_dslがなくても動作）')
    parser.add_argument('--list-functions', action='store_true',
                      help='データベース内の利用可能な関数一覧を表示')
    parser.add_argument('--all-functions', action='store_true',
                      help='全関数の基本的なチェックを実行')
    
    args = parser.parse_args()

    load_dotenv()
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USER = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
    NEO4J_DATABASE = args.database

    if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
        print("Error: NEO4J_URI, NEO4J_USER (or NEO4J_USERNAME), and NEO4J_PASSWORD must be set in the .env file.", file=sys.stderr)
        sys.exit(1)

    print(f"🔍 RAG Retrieval Test for database: {NEO4J_DATABASE}")
    if NEO4J_DATABASE == "docparser":
        print("  → APIドキュメント解析データを格納するdocparserデータベースでテストを実行します")

    retriever = RagRetriever(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE)
    try:
        # 関数一覧表示
        if args.list_functions:
            retriever.list_available_functions()
            return
        
        # 特定の関数テスト
        if args.function:
            retriever.run_basic_function_test(args.function)
        # 全関数の基本的なチェック
        elif args.all_functions:
            retriever.run_all_functions_basic_check()
        # テストパターンファイルからのテスト実行
        elif args.test_path:
            test_paths = []
            if os.path.isdir(args.test_path):
                test_paths = [os.path.join(args.test_path, f) for f in os.listdir(args.test_path) 
                             if f.startswith('test_') and f.endswith('.py')]
            elif os.path.isfile(args.test_path):
                test_paths.append(args.test_path)
            
            if test_paths:
                for path in test_paths:
                    retriever.run_test_cases_from_file(path)
            else:
                print("No test files found.")
                return
        else:
            # デフォルトでtest_patternsディレクトリのテストを実行
            patterns_dir = os.path.join(os.path.dirname(__file__), 'test_patterns')
            if os.path.isdir(patterns_dir):
                test_paths = [os.path.join(patterns_dir, f) for f in os.listdir(patterns_dir) 
                             if f.startswith('test_') and f.endswith('.py')]
                if test_paths:
                    for path in test_paths:
                        retriever.run_test_cases_from_file(path)
                else:
                    print("No test files found in test_patterns directory.")
                    return
            else:
                print("test_patterns directory not found.")
                return

        # 最終サマリーを表示
        if retriever.test_results:
            print("\n--- Final Test Summary ---")
            passed_count = sum(1 for r in retriever.test_results if r.get('passed'))
            total_tests = len(retriever.test_results)

            for result in retriever.test_results:
                if not result.get('passed'):
                    print(f"  ❌ FAILED - Test '{result.get('test_name', 'Unknown')}' in {result['function']}: {result['details']}")

            print(f"\nSummary: {passed_count}/{total_tests} tests passed.")

            # ドキュメント保存
            if args.save_docs:
                print(f"\n📄 テスト結果をドキュメントとして保存中...")
                print(f"出力ディレクトリ: {args.output_dir}")
                
                md_file = retriever.save_results_as_markdown(args.output_dir)
                json_file = retriever.save_results_as_json(args.output_dir)
                
                if md_file and json_file:
                    print(f"\n✅ ドキュメント保存完了:")
                    print(f"  📝 Markdown: {md_file}")
                    print(f"  📊 JSON: {json_file}")
                else:
                    print(f"\n⚠️ 一部のドキュメント保存に失敗しました")
        else:
            print("No tests were executed.")

    finally:
        retriever.close()


if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    main()
