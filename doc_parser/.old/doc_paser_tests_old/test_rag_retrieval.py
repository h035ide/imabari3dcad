# 生成されたテストケースの検証スクリプト
# シンプルで読みやすい構造にリファクタリング済み
# ユーザーの判断を支援する詳細な差異分析機能付き
# Neo4jのデータのみを使用して検証（golden_snippetsは不要）
#
# 使用方法:
#   python test_rag_retrieval.py                    # デフォルトでテストケースを検証
#   python test_rag_retrieval.py --validate-snippets # 明示的にテストケースを検証（詳細分析付き）
#   python test_rag_retrieval.py --save-docs        # 結果をドキュメントとして保存
#   python test_rag_retrieval.py --function NAME    # 特定の関数をテスト（未実装）
#
# 特徴:
#   • 失敗したテストの詳細な差異分析
#   • Neo4jデータベース仕様との比較
#   • 生成されたコードの内容表示
#   • ユーザー判断のための推奨事項
#   • golden_snippetsに依存せず、Neo4jデータのみを使用

import os
import json
import argparse
import ast
import glob
import sys
from datetime import datetime
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv

class TestValidator:
    """シンプルなテストケース検証クラス"""
    
    def __init__(self, uri, user, password, database="docparser"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database
        self.results = []
        self.timestamp = datetime.now()
    
    def close(self):
        self.driver.close()
    
    def validate_snippets(self):
        """生成されたテストケースを検証（Neo4jデータのみ使用）"""
        print("🔍 テストケース検証を開始...")
        
        # スクリプトの場所を基準にパスを取得
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # code_snippets のみを検証（Neo4jデータと比較）
        code_dir = os.path.join(script_dir, "code_snippets")
        if os.path.exists(code_dir):
            print(f"\n📁 code_snippets を検証中...")
            self._validate_directory(code_dir, "test")
        else:
            print(f"❌ code_snippets ディレクトリが見つかりません")
            print(f"   パス: {code_dir}")
        
        print(f"\n💡 golden_snippets は使用していません（Neo4jデータが基準）")
    
    def _validate_directory(self, directory, test_type):
        """ディレクトリ内のファイルを検証"""
        files = glob.glob(os.path.join(directory, "*.py"))
        files.sort()
        
        print(f"📊 検証対象: {len(files)}個のファイル")
        
        for file_path in files:
            filename = os.path.basename(file_path)
            print(f"\n🧪 {filename}")
            
            # 構文チェック
            if not self._check_syntax(file_path):
                self._add_result(filename, False, "構文エラー", test_type)
                continue
            
            # 関数呼び出しを解析
            function_info = self._extract_function_call(file_path)
            if not function_info:
                self._add_result(filename, False, "関数呼び出しが見つかりません", test_type)
                continue
            
            # データベースと照合
            self._validate_function(filename, function_info, test_type)
    
    def _check_syntax(self, file_path):
        """Pythonファイルの構文チェック"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
            return True
        except Exception:
            return False
    
    def _extract_function_call(self, file_path):
        """ファイルから関数呼び出しを抽出"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    if node.func.value.id == 'part':
                        return {
                            'name': node.func.attr,
                            'arg_count': len(node.args)
                        }
        except Exception:
            pass
        return None
    
    def _get_function_spec(self, function_name):
        """データベースから関数仕様を取得"""
        with self.driver.session(database=self.database) as session:
            query = """
            MATCH (f:Function {name: $function_name})
            OPTIONAL MATCH (f)-[r:HAS_PARAMETER]->(p:Parameter)
            OPTIONAL MATCH (p)-[:HAS_TYPE]->(t)
            WITH f, r, p, t
            ORDER BY r.position
            RETURN f.name as name, 
                   f.description as description,
                   collect(DISTINCT {
                       name: p.name,
                       position: r.position,
                       type: t.name,
                       description: p.description
                   }) as parameters
            """
            result = session.run(query, function_name=function_name).single()
            
            if result:
                return {
                    'name': result['name'],
                    'description': result['description'],
                    'parameters': result['parameters']
                }
            return None

    def _validate_function(self, filename, function_info, test_type):
        """関数の引数数をNeo4jデータベースと照合し、詳細な差異を表示"""
        function_name = function_info['name']
        arg_count = function_info['arg_count']
        
        # データベースから関数仕様を取得
        db_spec = self._get_function_spec(function_name)
        if not db_spec:
            self._add_result(filename, False, f"関数 '{function_name}' がデータベースに見つかりません", test_type)
            return
        
        # nullでないパラメータのみをカウント
        valid_params = [p for p in db_spec.get('parameters', []) if p.get('name')]
        expected_params = len(valid_params)
        is_match = (arg_count == expected_params)
        
        # 詳細な差異分析
        if not is_match:
            self._display_detailed_difference(
                filename, function_name, arg_count, expected_params, 
                valid_params, db_spec, test_type
            )
        
        # テストタイプに基づいて結果を判定
        if test_type == "test":
            # ファイル名からpositive/negativeを判定
            if "positive" in filename:
                passed = is_match
                details = f"引数数一致: {arg_count}/{expected_params}"
            else:  # negative
                passed = not is_match
                details = f"引数数不一致を正しく検出: {arg_count}/{expected_params}"
        
        self._add_result(filename, passed, details, test_type)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}: {details}")
    
    def _display_detailed_difference(self, filename, function_name, arg_count, expected_params, 
                                   valid_params, db_spec, test_type):
        """失敗したテストの詳細な差異を表示"""
        print(f"\n🔍 **詳細分析: {filename}**")
        print(f"   関数名: {function_name}")
        print(f"   生成されたコードの引数数: {arg_count}")
        print(f"   データベースの期待パラメータ数: {expected_params}")
        
        if db_spec.get('description'):
            print(f"   関数の説明: {db_spec['description']}")
        
        print(f"\n📋 **データベースの詳細仕様:**")
        for param in valid_params:
            pos = param.get('position', '?')
            name = param.get('name', 'Unknown')
            param_type = param.get('type', 'Unknown')
            desc = param.get('description', 'No description')
            print(f"   {pos:2d}. {name:<20} ({param_type:<15}) - {desc}")
        
        # 生成されたコードの内容も表示
        self._display_generated_code(filename)
        
        print(f"\n💡 **判断のポイント:**")
        if arg_count < expected_params:
            print(f"   → 生成されたコードに {expected_params - arg_count}個 のパラメータが不足しています")
            print(f"   → 不足しているパラメータを確認し、必要に応じて追加してください")
        elif arg_count > expected_params:
            print(f"   → 生成されたコードに {arg_count - expected_params}個 の余分なパラメータがあります")
            print(f"   → 不要なパラメータを削除するか、データベース仕様を確認してください")
        
        print(f"   → どちらが正しいかは、実際のAPIドキュメントや使用例を参照して判断してください")
        print("-" * 80)
    
    def _display_generated_code(self, filename):
        """生成されたコードの内容を表示"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # code_snippetsのみから読み込み
            file_path = os.path.join(script_dir, "code_snippets", filename)
            
            if os.path.exists(file_path):
                print(f"\n📝 **生成されたコード:**")
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 最初の10行を表示
                    lines = content.split('\n')[:10]
                    for line in lines:
                        if line.strip():
                            print(f"      {line}")
                    if len(content.split('\n')) > 10:
                        remaining_lines = len(content.split('\n')) - 10
                        print(f"      ... (残り {remaining_lines}行)")
        except Exception as e:
            print(f"      [コードの読み込みに失敗: {e}]")
    
    def _add_result(self, test_name, passed, details, test_type):
        """テスト結果を追加"""
        self.results.append({
            "test_name": test_name,
            "passed": passed,
            "details": details,
            "test_type": test_type
        })
    
    def print_summary(self):
        """検証結果のサマリーを表示"""
        if not self.results:
            print("No tests were executed.")
            return
        
        print("\n" + "=" * 80)
        print("🔍 **検証結果サマリー**")
        print("=" * 80)
        
        # 統計情報
        passed_count = sum(1 for r in self.results if r['passed'])
        total_count = len(self.results)
        failed_count = total_count - passed_count
        
        print(f"📊 **全体統計:**")
        print(f"   • 総検証数: {total_count}")
        print(f"   • 成功: {passed_count} ({passed_count/total_count*100:.1f}%)")
        print(f"   • 失敗: {failed_count} ({failed_count/total_count*100:.1f}%)")
        
        # 失敗したテストの詳細分析
        if failed_count > 0:
            print(f"\n❌ **失敗したテストの詳細分析:**")
            print("-" * 80)
            
            # テストタイプ別にグループ化
            failed_by_type = {}
            for result in self.results:
                if not result['passed']:
                    test_type = result.get('test_type', 'unknown')
                    if test_type not in failed_by_type:
                        failed_by_type[test_type] = []
                    failed_by_type[test_type].append(result)
            
            for test_type, results in failed_by_type.items():
                print(f"\n🔍 **{test_type.upper()} テストの失敗 ({len(results)}件):**")
                for result in results:
                    test_name = result.get('test_name', 'Unknown')
                    details = result.get('details', 'No details')
                    print(f"   • {test_name}: {details}")
            
            print(f"\n💡 **改善のための推奨事項:**")
            print(f"   1. 失敗したテストケースの詳細分析を確認してください")
            print(f"   2. データベース仕様と生成されたコードの差異を検討してください")
            print(f"   3. 必要に応じて生成スクリプトを修正してください")
            print(f"   4. 実際のAPIドキュメントと照合して正しい仕様を確認してください")
        
        print(f"\n" + "=" * 80)
        print(f"🎯 **最終結果: {passed_count}/{total_count} tests passed**")
        if failed_count == 0:
            print(f"✅ すべてのテストが成功しました！")
        else:
            print(f"⚠️  {failed_count}個のテストが失敗しました。詳細分析を確認してください。")
        print("=" * 80)
    
    def save_results(self, output_dir="verification_reports"):
        """結果をファイルとして保存（詳細分析情報付き）"""
        output_path = Path(__file__).parent / output_dir
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp_str = self.timestamp.strftime("%Y%m%d_%H%M%S")
        
        # Markdownファイル
        md_file = output_path / f"validation_report_{timestamp_str}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            self._write_detailed_markdown_report(f)
        
        # JSONファイル
        json_file = output_path / f"validation_results_{timestamp_str}.json"
        export_data = self._prepare_detailed_json_data()
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 詳細な結果を保存しました:")
        print(f"  📝 Markdown: {md_file}")
        print(f"  📊 JSON: {json_file}")
    
    def _write_detailed_markdown_report(self, f):
        """詳細なMarkdownレポートを書き込み"""
        f.write(f"# テストケース検証レポート（詳細版）\n\n")
        f.write(f"**日時**: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**データベース**: {self.database}\n")
        f.write(f"**生成元**: test_rag_retrieval.py (Neo4jデータのみ使用、詳細分析機能付き)\n")
        f.write(f"**検証基準**: Neo4jデータベースの関数仕様\n\n")
        
        # 全体統計
        passed_count = sum(1 for r in self.results if r['passed'])
        total_count = len(self.results)
        failed_count = total_count - passed_count
        
        f.write("## 📊 全体統計\n\n")
        f.write(f"- **総検証数**: {total_count}\n")
        f.write(f"- **成功**: {passed_count} ({passed_count/total_count*100:.1f}%)\n")
        f.write(f"- **失敗**: {failed_count} ({failed_count/total_count*100:.1f}%)\n\n")
        
        # テストタイプ別の統計
        test_types = {}
        for result in self.results:
            test_type = result.get('test_type', 'unknown')
            if test_type not in test_types:
                test_types[test_type] = {"passed": 0, "total": 0}
            test_types[test_type]["total"] += 1
            if result['passed']:
                test_types[test_type]["passed"] += 1
        
        f.write("## 🔍 テストタイプ別統計\n\n")
        for test_type, stats in test_types.items():
            success_rate = (stats["passed"]/stats["total"]*100) if stats["total"] > 0 else 0
            f.write(f"- **{test_type.upper()}**: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)\n")
        f.write("\n")
        
        # 失敗したテストの詳細分析
        if failed_count > 0:
            f.write("## ❌ 失敗したテストの詳細分析\n\n")
            f.write("以下のテストケースで詳細な差異が検出されました。\n\n")
            
            # テストタイプ別にグループ化
            failed_by_type = {}
            for result in self.results:
                if not result['passed']:
                    test_type = result.get('test_type', 'unknown')
                    if test_type not in failed_by_type:
                        failed_by_type[test_type] = []
                    failed_by_type[test_type].append(result)
            
            for test_type, results in failed_by_type.items():
                f.write(f"### {test_type.upper()} テストの失敗 ({len(results)}件)\n\n")
                
                for result in results:
                    test_name = result.get('test_name', 'Unknown')
                    details = result.get('details', 'No details')
                    f.write(f"#### {test_name}\n\n")
                    f.write(f"**結果**: {details}\n\n")
                    
                    # 詳細分析情報を追加
                    self._write_test_analysis_to_report(f, test_name, result)
                    f.write("\n---\n\n")
        
        # 成功したテストの一覧
        f.write("## ✅ 成功したテスト一覧\n\n")
        passed_tests = [r for r in self.results if r['passed']]
        for result in passed_tests:
            test_name = result.get('test_name', 'Unknown')
            details = result.get('details', 'No details')
            f.write(f"- **{test_name}**: {details}\n")
        
        # 推奨事項
        f.write("\n## 💡 改善のための推奨事項\n\n")
        if failed_count == 0:
            f.write("✅ すべてのテストが成功しました。生成されたテストケースは高品質です。\n")
        else:
            f.write("❌ 一部のテストが失敗しました。以下の点を確認してください：\n\n")
            f.write("1. **失敗したテストケースの詳細分析を確認**\n")
            f.write("   - 上記の詳細分析セクションで各テストの失敗原因を確認\n")
            f.write("   - Neo4jデータベース仕様と生成されたコードの差異を検討\n\n")
            f.write("2. **生成スクリプトの改善**\n")
            f.write("   - 不足しているパラメータの追加\n")
            f.write("   - 余分なパラメータの削除\n")
            f.write("   - パラメータ順序の修正\n\n")
            f.write("3. **Neo4jデータベース仕様の確認**\n")
            f.write("   - 実際のAPIドキュメントとの照合\n")
            f.write("   - 使用例との比較\n")
            f.write("   - 必要に応じてデータベースの更新\n\n")
            f.write("4. **テストケースの品質向上**\n")
            f.write("   - 正しい引数数のテストケースの生成\n")
            f.write("   - エッジケースの考慮\n")
            f.write("   - 実際の使用パターンとの整合性確認\n")
        
        f.write("\n---\n")
        f.write(f"*このレポートは {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} に自動生成されました。*\n")
        f.write(f"*Neo4jデータベースの仕様を基準として検証を行いました。*\n")
    
    def _write_test_analysis_to_report(self, f, test_name, result):
        """個別テストの詳細分析をレポートに書き込み"""
        # ファイル名から関数名を抽出
        if '_' in test_name:
            function_name = test_name.split('_')[0]
        else:
            function_name = test_name
        
        # データベースから関数仕様を取得
        db_spec = self._get_function_spec(function_name)
        if not db_spec:
            f.write("**注意**: データベースから関数仕様を取得できませんでした。\n\n")
            return
        
        # 生成されたコードの内容を取得
        generated_code = self._get_generated_code_content(test_name)
        
        # 詳細分析を書き込み
        f.write("**詳細分析**:\n\n")
        f.write(f"- **関数名**: {function_name}\n")
        
        if db_spec.get('description'):
            f.write(f"- **関数の説明**: {db_spec['description']}\n")
        
        # 引数数の比較
        arg_count = self._extract_arg_count_from_result(result)
        valid_params = [p for p in db_spec.get('parameters', []) if p.get('name')]
        expected_params = len(valid_params)
        
        f.write(f"- **生成されたコードの引数数**: {arg_count}\n")
        f.write(f"- **データベースの期待パラメータ数**: {expected_params}\n\n")
        
        # データベースの詳細仕様
        f.write("**データベースの詳細仕様**:\n\n")
        for param in valid_params:
            pos = param.get('position', '?')
            name = param.get('name', 'Unknown')
            param_type = param.get('type', 'Unknown')
            desc = param.get('description', 'No description')
            f.write(f"{pos:2d}. {name:<20} ({param_type:<15}) - {desc}\n")
        
        # 生成されたコード
        if generated_code:
            f.write(f"\n**生成されたコード**:\n\n")
            f.write("```python\n")
            f.write(generated_code)
            f.write("\n```\n\n")
        
        # 判断のポイント
        f.write("**判断のポイント**:\n\n")
        if arg_count < expected_params:
            f.write(f"- 生成されたコードに {expected_params - arg_count}個 のパラメータが不足しています\n")
            f.write("- 不足しているパラメータを確認し、必要に応じて追加してください\n")
        elif arg_count > expected_params:
            f.write(f"- 生成されたコードに {arg_count - expected_params}個 の余分なパラメータがあります\n")
            f.write("- 不要なパラメータを削除するか、データベース仕様を確認してください\n")
        
        f.write("- どちらが正しいかは、実際のAPIドキュメントや使用例を参照して判断してください\n")
    
    def _extract_arg_count_from_result(self, result):
        """結果から引数数を抽出"""
        details = result.get('details', '')
        if '引数数一致:' in details:
            # "引数数一致: 6/7" から "6" を抽出
            parts = details.split(':')
            if len(parts) > 1:
                arg_part = parts[1].strip()
                if '/' in arg_part:
                    return int(arg_part.split('/')[0])
        elif '引数数:' in details:
            # "引数数: 6/7" から "6" を抽出
            parts = details.split(':')
            if len(parts) > 1:
                arg_part = parts[1].strip()
                if '/' in arg_part:
                    return int(arg_part.split('/')[0])
        return 0
    
    def _get_generated_code_content(self, test_name):
        """生成されたコードの内容を取得"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # code_snippetsのみから読み込み
            file_path = os.path.join(script_dir, "code_snippets", test_name)
            
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 最初の20行を返す
                    lines = content.split('\n')[:20]
                    return '\n'.join(lines)
        except Exception:
            pass
        return None
    
    def _prepare_detailed_json_data(self):
        """詳細なJSONデータを準備"""
        # 失敗したテストの詳細情報を収集
        detailed_results = []
        for result in self.results:
            detailed_result = result.copy()
            
            if not result['passed']:
                # 失敗したテストの詳細情報を追加
                test_name = result.get('test_name', 'Unknown')
                function_name = test_name.split('_')[0] if '_' in test_name else test_name
                
                # データベース仕様を取得
                db_spec = self._get_function_spec(function_name)
                if db_spec:
                    detailed_result['database_spec'] = {
                        'name': db_spec.get('name'),
                        'description': db_spec.get('description'),
                        'parameters': db_spec.get('parameters', [])
                    }
                
                # 生成されたコードの内容を取得
                generated_code = self._get_generated_code_content(test_name)
                if generated_code:
                    detailed_result['generated_code'] = generated_code
                
                # 引数数の詳細
                arg_count = self._extract_arg_count_from_result(result)
                detailed_result['arg_count_details'] = {
                    'generated': arg_count,
                    'expected': len([p for p in db_spec.get('parameters', []) if p.get('name')]) if db_spec else 0
                }
            
            detailed_results.append(detailed_result)
        
        return {
            "metadata": {
                "timestamp": self.timestamp.isoformat(),
                "database": self.database,
                "generator": "test_rag_retrieval.py (Neo4jデータのみ使用、詳細分析機能付き)",
                "export_timestamp": datetime.now().isoformat()
            },
            "summary": {
                "total": len(self.results),
                "passed": sum(1 for r in self.results if r['passed']),
                "failed": sum(1 for r in self.results if not r['passed']),
                "test_types": self._get_test_type_summary()
            },
            "results": detailed_results
        }
    
    def _get_test_type_summary(self):
        """テストタイプ別のサマリーを取得"""
        test_types = {}
        for result in self.results:
            test_type = result.get('test_type', 'unknown')
            if test_type not in test_types:
                test_types[test_type] = {"passed": 0, "total": 0}
            test_types[test_type]["total"] += 1
            if result['passed']:
                test_types[test_type]["passed"] += 1
        
        # 成功率を計算
        for test_type in test_types:
            total = test_types[test_type]["total"]
            passed = test_types[test_type]["passed"]
            test_types[test_type]["success_rate"] = (passed/total*100) if total > 0 else 0
        
        return test_types


def main():
    parser = argparse.ArgumentParser(description="テストケース検証スクリプト")
    parser.add_argument('--save-docs', action='store_true', help='結果をドキュメントとして保存')
    parser.add_argument('--function', type=str, help='特定の関数をテスト（未実装）')
    parser.add_argument('--validate-snippets', action='store_true', help='生成されたテストケースを検証（デフォルト）')
    
    args = parser.parse_args()
    
    # 環境変数を読み込み
    load_dotenv()
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not all([uri, user, password]):
        print("❌ 環境変数が設定されていません。.envファイルを確認してください。")
        sys.exit(1)
    
    # 検証を実行
    validator = TestValidator(uri, user, password)
    try:
        # --validate-snippetsが指定されているか、デフォルトで実行
        if args.validate_snippets or not args.function:
            validator.validate_snippets()
            validator.print_summary()
            
            if args.save_docs:
                validator.save_results()
        else:
            print("特定の関数のテスト機能は未実装です。")
    
    finally:
        validator.close()


if __name__ == "__main__":
    main()
