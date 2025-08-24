# This script runs specification tests for GraphRAG data retrieval from Neo4j database.
# 生成されたテストケース（code_snippets/とgolden_snippets/）を使用して検証を実行します。
#
# 使用方法:
#   python test_rag_retrieval.py                    # デフォルトでdocparserデータベースを使用
#   python test_rag_retrieval.py --database neo4j   # 指定されたデータベースを使用
#   python test_rag_retrieval.py --save-docs        # テスト結果をドキュメントとして保存
#   python test_rag_retrieval.py --output-dir reports # カスタム出力ディレクトリを指定
#   python test_rag_retrieval.py --test-snippets    # 生成されたテストケースを検証
#   python test_rag_retrieval.py --function CreateSolid # 特定の関数をテスト
#   python test_rag_retrieval.py --list-functions   # 利用可能な関数一覧を表示
#   python test_rag_retrieval.py --all-functions    # 全関数の基本的なチェックを実行
#   python test_rag_retrieval.py --validate-snippets # 生成されたテストケースの構文と引数数を検証
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
import ast
import glob
from datetime import datetime
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv

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

    def validate_generated_snippets(self):
        """生成されたテストケース（code_snippets/とgolden_snippets/）を検証"""
        print("\n🔍 生成されたテストケースの検証を開始します...")
        
        if not self.test_timestamp:
            self.test_timestamp = datetime.now()
            self._get_database_info()
        
        # スクリプトファイルの場所を基準とした絶対パスを取得
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # code_snippetsディレクトリのテストケースを検証
        code_snippets_dir = os.path.join(script_dir, "code_snippets")
        if os.path.exists(code_snippets_dir):
            print(f"\n📁 {code_snippets_dir}ディレクトリのテストケースを検証中...")
            self._validate_code_snippets(code_snippets_dir)
        else:
            print(f"⚠️ {code_snippets_dir}ディレクトリが見つかりません")
        
        # golden_snippetsディレクトリのテンプレートを検証
        golden_snippets_dir = os.path.join(script_dir, "golden_snippets")
        if os.path.exists(golden_snippets_dir):
            print(f"\n📁 {golden_snippets_dir}ディレクトリのテンプレートを検証中...")
            self._validate_golden_snippets(golden_snippets_dir)
        else:
            print(f"⚠️ {golden_snippets_dir}ディレクトリが見つかりません")

    def _validate_code_snippets(self, snippets_dir):
        """code_snippetsディレクトリのテストケースを検証"""
        test_files = glob.glob(os.path.join(snippets_dir, "*.py"))
        test_files.sort()
        
        print(f"📊 検証対象: {len(test_files)}個のテストファイル")
        
        for test_file in test_files:
            test_name = os.path.basename(test_file)
            print(f"\n🧪 検証中: {test_name}")
            
            # テストタイプを判定
            test_type = self._determine_test_type(test_file)
            
            # 構文チェック
            syntax_valid, syntax_error = self._check_syntax(test_file)
            
            # 関数呼び出しの解析
            function_call = self._extract_function_call(test_file)
            
            if function_call:
                function_name = function_call['name']
                arg_count = function_call['arg_count']
                
                # データベースの仕様と照合
                db_spec = self.get_function_spec(function_name)
                
                if db_spec:
                    expected_params = len(db_spec.get('parameters', []))
                    is_match = (arg_count == expected_params)
                    
                    # テストタイプに基づいて結果を判定
                    if test_type == 'positive':
                        passed = is_match
                        details = f"引数数一致: {arg_count}/{expected_params}"
                    else:  # negative
                        passed = not is_match
                        details = f"引数数不一致を正しく検出: {arg_count}/{expected_params}"
                    
                    self._add_test_result(
                        f"{test_name} ({function_name})", 
                        passed, 
                        details,
                        test_type=test_type
                    )
                    
                    status = "✅ PASS" if passed else "❌ FAIL"
                    print(f"   {status}: {details}")
                    
                else:
                    self._add_test_result(
                        f"{test_name} ({function_name})", 
                        False, 
                        f"関数 '{function_name}' がデータベースに見つかりません",
                        test_type=test_type
                    )
                    print(f"   ❌ FAIL: 関数 '{function_name}' がデータベースに見つかりません")
            else:
                self._add_test_result(
                    test_name, 
                    False, 
                    "関数呼び出しが見つかりません",
                    test_type=test_type
                )
                print(f"   ❌ FAIL: 関数呼び出しが見つかりません")
            
            # 構文チェックの結果も記録
            if not syntax_valid:
                self._add_test_result(
                    f"{test_name} (構文)", 
                    False, 
                    f"構文エラー: {syntax_error}",
                    test_type="syntax"
                )
                print(f"   ❌ 構文エラー: {syntax_error}")

    def _validate_golden_snippets(self, snippets_dir):
        """golden_snippetsディレクトリのテンプレートを検証"""
        template_files = glob.glob(os.path.join(snippets_dir, "*.py"))
        template_files.sort()
        
        print(f"📊 検証対象: {len(template_files)}個のテンプレートファイル")
        
        for template_file in template_files:
            template_name = os.path.basename(template_file)
            print(f"\n🧪 検証中: {template_name}")
            
            # 構文チェック
            syntax_valid, syntax_error = self._check_syntax(template_file)
            
            # 関数呼び出しの解析
            function_call = self._extract_function_call(template_file)
            
            if function_call:
                function_name = function_call['name']
                arg_count = function_call['arg_count']
                
                # データベースの仕様と照合
                db_spec = self.get_function_spec(function_name)
                
                if db_spec:
                    expected_params = len(db_spec.get('parameters', []))
                    is_match = (arg_count == expected_params)
                    
                    self._add_test_result(
                        f"{template_name} ({function_name})", 
                        is_match, 
                        f"テンプレート引数数: {arg_count}, 期待値: {expected_params}",
                        test_type="template"
                    )
                    
                    status = "✅ PASS" if is_match else "❌ FAIL"
                    print(f"   {status}: 引数数 {arg_count}/{expected_params}")
                    
                else:
                    self._add_test_result(
                        f"{template_name} ({function_name})", 
                        False, 
                        f"関数 '{function_name}' がデータベースに見つかりません",
                        test_type="template"
                    )
                    print(f"   ❌ FAIL: 関数 '{function_name}' がデータベースに見つかりません")
            else:
                self._add_test_result(
                    template_name, 
                    False, 
                    "関数呼び出しが見つかりません",
                    test_type="template"
                )
                print(f"   ❌ FAIL: 関数呼び出しが見つかりません")
            
            # 構文チェックの結果も記録
            if not syntax_valid:
                self._add_test_result(
                    f"{template_name} (構文)", 
                    False, 
                    f"構文エラー: {syntax_error}",
                    test_type="syntax"
                )
                print(f"   ❌ 構文エラー: {syntax_error}")

    def _determine_test_type(self, file_path):
        """ファイルの内容からテストタイプを判定"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if '# test_type:' in first_line:
                    test_type = first_line.split(':')[-1].strip()
                    return test_type
        except Exception:
            pass
        return 'unknown'

    def _check_syntax(self, file_path):
        """Pythonファイルの構文チェック"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
            return True, None
        except SyntaxError as e:
            return False, str(e)
        except Exception as e:
            return False, f"読み込みエラー: {str(e)}"

    def _extract_function_call(self, file_path):
        """ファイルから関数呼び出しを抽出"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    if node.func.value.id == 'part':  # part.function_name()の形式
                        return {
                            'name': node.func.attr,
                            'arg_count': len(node.args)
                        }
        except Exception:
            pass
        return None

    def get_all_function_names(self):
        """データベースからすべての関数名を取得"""
        with self.driver.session(database=self.database) as session:
            query = "MATCH (f:Function) RETURN f.name as name ORDER BY f.name"
            records = session.run(query).data()
            return [r['name'] for r in records]

    def _add_test_result(self, test_name, passed, details, test_type="unknown"):
        """テスト結果を追加"""
        result = {
            "test_name": test_name,
            "passed": passed,
            "details": details,
            "test_type": test_type,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)

    def save_results_as_markdown(self, output_dir="verification_reports"):
        """テスト結果をMarkdownファイルとして保存"""
        output_path = Path(__file__).parent / output_dir
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp_str = self.test_timestamp.strftime("%Y%m%d_%H%M%S") if self.test_timestamp else "unknown"
        filename = f"generated_snippets_validation_{self.database}_{timestamp_str}.md"
        filepath = output_path / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                self._write_markdown_header(f)
                self._write_database_info(f)
                self._write_test_summary(f)
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
        f.write(f"# 生成されたテストケース検証レポート\n\n")
        f.write(f"**データベース名**: {self.database}\n")
        f.write(f"**検証日時**: {self.test_timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.test_timestamp else 'Unknown'}\n")
        f.write(f"**生成元**: test_rag_retrieval.py (修正版)\n\n")

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
        f.write("\n## 検証結果サマリー\n\n")
        passed_count = sum(1 for r in self.test_results if r.get('passed'))
        total_tests = len(self.test_results)
        
        f.write(f"- **総検証数**: {total_tests}\n")
        f.write(f"- **通過数**: {passed_count}\n")
        f.write(f"- **失敗数**: {total_tests - passed_count}\n")
        f.write(f"- **成功率**: {(passed_count/total_tests*100):.1f}%\n\n")
        
        overall_status = "✅ 全検証通過" if passed_count == total_tests else "❌ 一部検証失敗"
        f.write(f"**全体結果**: {overall_status}\n")

    def _write_detailed_results(self, f):
        """詳細検証結果を書き込み"""
        f.write("\n## 詳細検証結果\n\n")
        
        # テストタイプ別にグループ化
        test_types = {}
        for result in self.test_results:
            test_type = result.get('test_type', 'unknown')
            if test_type not in test_types:
                test_types[test_type] = []
            test_types[test_type].append(result)
        
        for test_type, results in test_types.items():
            f.write(f"### {test_type.upper()} テスト\n\n")
            
            type_passed = sum(1 for r in results if r.get('passed'))
            type_total = len(results)
            
            f.write(f"**結果**: {type_passed}/{type_total} 通過\n\n")
            
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
            f.write("✅ すべての検証が通過しました。生成されたテストケースは高品質です。\n")
        else:
            f.write("❌ 一部の検証が失敗しました。以下の点を確認してください：\n\n")
            for result in self.test_results:
                if not result.get('passed'):
                    f.write(f"- **{result.get('test_name', 'Unknown')}**: {result.get('details', 'No details')}\n")

    def _write_footer(self, f):
        """フッターを書き込み"""
        f.write("\n---\n")
        f.write(f"*このレポートは {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} に自動生成されました。*")

    def save_results_as_json(self, output_dir="verification_reports"):
        """テスト結果をJSONファイルとして保存"""
        output_path = Path(__file__).parent / output_dir
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp_str = self.test_timestamp.strftime("%Y%m%d_%H%M%S") if self.test_timestamp else "unknown"
        filename = f"generated_snippets_validation_{self.database}_{timestamp_str}.json"
        filepath = output_path / filename
        
        try:
            export_data = {
                "metadata": {
                    "database_name": self.database,
                    "test_timestamp": self.test_timestamp.isoformat() if self.test_timestamp else None,
                    "generator": "test_rag_retrieval.py (修正版)",
                    "export_timestamp": datetime.now().isoformat()
                },
                "database_info": self.database_info,
                "test_results": self.test_results,
                "summary": self._generate_test_summary()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 検証結果JSONを保存しました: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ JSON保存中にエラーが発生しました: {e}")
            return None

    def _generate_test_summary(self):
        """テスト結果のサマリーを生成"""
        passed_count = sum(1 for r in self.test_results if r.get('passed'))
        total_tests = len(self.test_results)
        
        # テストタイプ別の統計
        test_types = {}
        for result in self.test_results:
            test_type = result.get('test_type', 'unknown')
            if test_type not in test_types:
                test_types[test_type] = {"passed": 0, "total": 0}
            test_types[test_type]["total"] += 1
            if result.get('passed'):
                test_types[test_type]["passed"] += 1
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_count,
            "failed_tests": total_tests - passed_count,
            "success_rate": (passed_count/total_tests*100) if total_tests > 0 else 0,
            "overall_status": "passed" if passed_count == total_tests else "failed",
            "test_type_summary": test_types
        }

    def run_basic_function_test(self, function_name):
        """基本的な関数仕様テスト"""
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
        description="Run specification tests for GraphRAG data retrieval using generated test cases.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python test_rag_retrieval.py                    # デフォルトでdocparserデータベースを使用
  python test_rag_retrieval.py --database neo4j   # 指定されたデータベースを使用
  python test_rag_retrieval.py --save-docs        # テスト結果をドキュメントとして保存
  python test_rag_retrieval.py --output-dir reports # カスタム出力ディレクトリを指定
  python test_rag_retrieval.py --validate-snippets # 生成されたテストケースを検証
  python test_rag_retrieval.py --function CreateSolid # 特定の関数をテスト
  python test_rag_retrieval.py --list-functions   # 利用可能な関数一覧を表示
  python test_rag_retrieval.py --all-functions    # 全関数の基本的なチェックを実行
        """
    )
    
    parser.add_argument('--database', type=str, default='docparser',
                      help='使用するNeo4jデータベース名 (デフォルト: docparser)')
    parser.add_argument('--save-docs', action='store_true',
                      help='テスト結果をMarkdownとJSONファイルとして保存')
    parser.add_argument('--output-dir', type=str, default='verification_reports',
                      help='ドキュメント保存先ディレクトリ (デフォルト: verification_reports)')
    parser.add_argument('--function', type=str, metavar='FUNCTION_NAME',
                      help='特定の関数をテスト')
    parser.add_argument('--list-functions', action='store_true',
                      help='データベース内の利用可能な関数一覧を表示')
    parser.add_argument('--all-functions', action='store_true',
                      help='全関数の基本的なチェックを実行')
    parser.add_argument('--validate-snippets', action='store_true',
                      help='生成されたテストケース（code_snippets/とgolden_snippets/）を検証')
    
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
        # 生成されたテストケースの検証
        elif args.validate_snippets:
            retriever.validate_generated_snippets()
        else:
            # デフォルトで生成されたテストケースを検証
            print("デフォルトで生成されたテストケースの検証を実行します...")
            retriever.validate_generated_snippets()

        # 最終サマリーを表示
        if retriever.test_results:
            print("\n--- Final Test Summary ---")
            passed_count = sum(1 for r in retriever.test_results if r.get('passed'))
            total_tests = len(retriever.test_results)

            for result in retriever.test_results:
                if not result.get('passed'):
                    print(f"  ❌ FAILED - {result.get('test_name', 'Unknown')}: {result['details']}")

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
