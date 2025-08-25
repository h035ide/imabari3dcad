#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
包括的検証スクリプト
すべての関数とオブジェクトを一括で確認し、包括的なレポートを生成します。

使用方法:
    python comprehensive_verification.py --save-docs
    python comprehensive_verification.py --function CreateSolid --detailed
    python comprehensive_verification.py --object ObjectDefinition --detailed
    python comprehensive_verification.py --all --save-docs
"""

import os
import sys
import argparse
import json
from datetime import datetime
from pathlib import Path
from collections import Counter
from typing import Dict, List, Any

# プロジェクトルートを設定
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from test_rag_retrieval import RagRetriever
    from verify_neo4j_data import Neo4jVerifier
except ImportError:
    sys.path.insert(0, os.path.dirname(__file__))
    from test_rag_retrieval import RagRetriever
    from verify_neo4j_data import Neo4jVerifier


class ComprehensiveVerifier:
    def __init__(self, uri: str, user: str, password: str, database: str = "docparser"):
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self.verification_timestamp = datetime.now()
        
        # 各検証器を初期化
        self.rag_retriever = RagRetriever(uri, user, password, database)
        self.neo4j_verifier = Neo4jVerifier(uri, user, password, database)
        
        # 統計情報の初期化
        self.stats = self._init_stats()

    def _init_stats(self) -> Dict[str, Any]:
        """統計情報を初期化"""
        return {
            "total_functions": 0,
            "total_objects": 0,
            "total_parameters": 0,
            "functions_with_params": 0,
            "functions_without_params": 0,
            "objects_with_properties": 0,
            "objects_without_properties": 0,
            "parameter_types": Counter(),
            "return_types": Counter()
        }

    def get_all_functions(self) -> List[Dict[str, Any]]:
        """データベース内のすべての関数を取得"""
        print("🔍 すべての関数を取得中...")
        
        try:
            functions = self.rag_retriever.get_all_function_names()
            if functions is None:
                print("⚠️  関数一覧がNoneでした。空のリストとして処理します。")
                functions = []
            
            self.stats["total_functions"] = len(functions)
            function_details = []
            
            for func_name in functions:
                try:
                    print(f"🔍 関数 '{func_name}' の詳細を取得中...")
                    spec = self.rag_retriever.get_function_spec(func_name)
                    if spec:
                        print(f"✅ 関数 '{func_name}' の詳細取得成功")
                        function_details.append(spec)
                        self._update_function_stats(spec)
                        self._display_code_sample(func_name, spec.get('parameters', []))
                    else:
                        print(f"⚠️  関数 '{func_name}' の詳細が取得できませんでした")
                        
                except Exception as e:
                    print(f"❌ 関数 '{func_name}' の詳細取得でエラー: {e}")
                    continue
            
            print(f"✅ {len(function_details)} 個の関数の詳細を取得完了")
            return function_details
            
        except Exception as e:
            print(f"❌ 関数一覧の取得でエラー: {e}")
            return []

    def _update_function_stats(self, spec: Dict[str, Any]) -> None:
        """関数の統計情報を更新"""
        params = spec.get('parameters', [])
        if params:
            self.stats["functions_with_params"] += 1
            self.stats["total_parameters"] += len(params)
            for param in params:
                param_type = param.get('type', 'Unknown')
                self.stats["parameter_types"][param_type] += 1
        else:
            self.stats["functions_without_params"] += 1
        
        return_type = spec.get('return_type', 'Unknown')
        self.stats["return_types"][return_type] += 1

    def _display_code_sample(self, func_name: str, params: List[Dict[str, Any]]) -> None:
        """コード生成サンプルを表示"""
        print(f"📝 コード生成サンプル:")
        print("```python")
        if params:
            param_names = [param.get('name', 'param') for param in sorted(params, key=lambda p: p.get('position', 0))]
            print(f"part.{func_name}(")
            print("    " + ",\n    ".join(param_names))
            print(")")
        else:
            print(f"part.{func_name}()")
        print("```")

    def get_all_objects(self) -> List[Dict[str, Any]]:
        """データベース内のすべてのオブジェクト定義を取得"""
        print("🔍 すべてのオブジェクト定義を取得中...")
        
        try:
            query = """
            MATCH (o:ObjectDefinition)
            RETURN o.name as name, o.description as description
            ORDER BY o.name
            """
            
            with self.rag_retriever.driver.session(database=self.database) as session:
                result = session.run(query)
                objects = [{"name": record["name"], "description": record["description"]} 
                          for record in result]
            
            self.stats["total_objects"] = len(objects)
            detailed_objects = []
            
            for obj in objects:
                try:
                    properties = self.get_object_properties(obj["name"])
                    obj["properties"] = properties
                    
                    if properties:
                        self.stats["objects_with_properties"] += 1
                        for prop in properties:
                            prop_type = prop.get('type', 'Unknown')
                            self.stats["parameter_types"][prop_type] += 1
                    else:
                        self.stats["objects_without_properties"] += 1
                    
                    detailed_objects.append(obj)
                    
                except Exception as e:
                    print(f"⚠️  オブジェクト '{obj['name']}' のプロパティ取得でエラー: {e}")
                    detailed_objects.append(obj)
                    continue
            
            print(f"✅ {len(detailed_objects)} 個のオブジェクト定義を取得完了")
            return detailed_objects
            
        except Exception as e:
            print(f"❌ オブジェクト定義の取得でエラー: {e}")
            return []

    def get_object_properties(self, object_name: str) -> List[Dict[str, Any]]:
        """オブジェクトのプロパティを取得"""
        try:
            check_query = """
            MATCH (o:ObjectDefinition {name: $object_name})
            OPTIONAL MATCH (o)-[:HAS_PROPERTY]->(p)
            RETURN count(p) as property_count
            """
            
            with self.rag_retriever.driver.session(database=self.database) as session:
                check_result = session.run(check_query, object_name=object_name)
                property_count = check_result.single()["property_count"]
                
                if property_count == 0:
                    print(f"⚠️  オブジェクト '{object_name}' にプロパティが定義されていません")
                    return []
                
                query = """
                MATCH (o:ObjectDefinition {name: $object_name})-[:HAS_PROPERTY]->(p)
                OPTIONAL MATCH (p)-[:HAS_TYPE]->(t)
                RETURN p.name as name, p.description as description, 
                       t.name as type
                ORDER BY p.name
                """
                
                result = session.run(query, object_name=object_name)
                properties = []
                for record in result:
                    properties.append({
                        "name": record["name"],
                        "description": record["description"],
                        "type": record["type"] or "Unknown",
                        "required": False
                    })
                
                return properties
                
        except Exception as e:
            print(f"⚠️  オブジェクト '{object_name}' のプロパティ取得でエラー: {e}")
            return []

    def get_database_summary(self) -> Dict[str, Any]:
        """データベースの概要情報を取得"""
        print("🔍 データベース概要を取得中...")
        
        try:
            summary = self.neo4j_verifier._get_database_info()
            print("✅ データベース概要を取得完了")
            return summary
        except Exception as e:
            print(f"❌ データベース概要の取得でエラー: {e}")
            return {}

    def generate_comprehensive_report(self, functions: List[Dict], objects: List[Dict], 
                                    database_summary: Dict) -> str:
        """包括的なレポートを生成"""
        print("📝 包括的レポートを生成中...")
        
        report_sections = [
            self._generate_report_header(),
            self._generate_database_summary(database_summary),
            self._generate_statistics_section(),
            self._generate_functions_section(functions),
            self._generate_objects_section(objects),
            self._generate_code_samples_section(functions)
        ]
        
        report_content = "\n".join(report_sections)
        print("✅ 包括的レポートの生成完了")
        return report_content

    def _generate_report_header(self) -> str:
        """レポートヘッダーを生成"""
        return f"""# 包括的検証レポート

**生成日時**: {self.verification_timestamp.strftime('%Y-%m-%d %H:%M:%S')}
**対象データベース**: {self.database}"""

    def _generate_database_summary(self, database_summary: Dict) -> str:
        """データベース概要セクションを生成"""
        if not database_summary:
            return "\n## データベース概要\n\nデータベース情報が取得できませんでした。"
        
        summary_lines = ["\n## データベース概要\n"]
        for key, value in database_summary.items():
            summary_lines.append(f"- **{key}**: {value}")
        return "\n".join(summary_lines)

    def _generate_statistics_section(self) -> str:
        """統計情報セクションを生成"""
        stats_lines = [
            "\n## 統計情報\n",
            f"- **総関数数**: {self.stats['total_functions']}",
            f"- **総オブジェクト数**: {self.stats['total_objects']}",
            f"- **総パラメータ数**: {self.stats['total_parameters']}",
            f"- **パラメータを持つ関数**: {self.stats['functions_with_params']}",
            f"- **パラメータのない関数**: {self.stats['functions_without_params']}",
            f"- **プロパティを持つオブジェクト**: {self.stats['objects_with_properties']}",
            f"- **プロパティのないオブジェクト**: {self.stats['objects_without_properties']}",
            ""
        ]
        
        # パラメータ型の分布
        stats_lines.append("### パラメータ型の分布")
        for param_type, count in self.stats["parameter_types"].most_common():
            stats_lines.append(f"- **{param_type}**: {count}個")
        stats_lines.append("")
        
        # 戻り値型の分布
        stats_lines.append("### 戻り値型の分布")
        for return_type, count in self.stats["return_types"].most_common():
            stats_lines.append(f"- **{return_type}**: {count}個")
        stats_lines.append("")
        
        return "\n".join(stats_lines)

    def _generate_functions_section(self, functions: List[Dict]) -> str:
        """関数セクションを生成"""
        if not functions:
            return "\n## 関数一覧\n\n関数が見つかりませんでした。"
        
        lines = ["\n## 関数一覧\n"]
        for func in functions:
            lines.extend(self._generate_function_details(func))
        return "\n".join(lines)

    def _generate_function_details(self, func: Dict) -> List[str]:
        """個別関数の詳細を生成"""
        lines = [
            f"### {func.get('name', 'Unknown')}",
            "",
            f"**説明**: {func.get('description', 'N/A')}",
            f"**戻り値の型**: {func.get('return_type', 'N/A')}",
            f"**戻り値の説明**: {func.get('return_description', 'N/A')}",
            ""
        ]
        
        params = func.get('parameters', [])
        if params:
            lines.append("**パラメータ**:")
            lines.append("")
            for param in sorted(params, key=lambda p: p.get('position', 0)):
                lines.append(f"- **{param['name']}** (位置: {param.get('position', 'N/A')}, 型: {param.get('type', 'N/A')})")
                lines.append(f"  - 説明: {param.get('description', 'N/A')}")
                lines.append(f"  - オブジェクト定義: {'はい' if param.get('is_object', False) else 'いいえ'}")
                lines.append("")
        else:
            lines.append("**パラメータ**: なし")
            lines.append("")
        
        # コード生成サンプル
        lines.extend(self._generate_function_code_sample(func))
        return lines

    def _generate_function_code_sample(self, func: Dict) -> List[str]:
        """関数のコードサンプルを生成"""
        lines = [
            "**コード生成サンプル**:",
            "",
            "```python"
        ]
        
        params = func.get('parameters', [])
        if params:
            param_names = [param.get('name', 'param') for param in sorted(params, key=lambda p: p.get('position', 0))]
            lines.append(f"part.{func.get('name', 'Function')}(")
            lines.append("    " + ",\n    ".join(param_names))
            lines.append(")")
        else:
            lines.append(f"part.{func.get('name', 'Function')}()")
        
        lines.extend(["```", ""])
        return lines

    def _generate_objects_section(self, objects: List[Dict]) -> str:
        """オブジェクト定義セクションを生成"""
        if not objects:
            return "\n## オブジェクト定義一覧\n\nオブジェクト定義が見つかりませんでした。"
        
        lines = ["\n## オブジェクト定義一覧\n"]
        for obj in objects:
            lines.extend(self._generate_object_details(obj))
        return "\n".join(lines)

    def _generate_object_details(self, obj: Dict) -> List[str]:
        """個別オブジェクトの詳細を生成"""
        lines = [
            f"### {obj.get('name', 'Unknown')}",
            "",
            f"**説明**: {obj.get('description', 'N/A')}",
            ""
        ]
        
        properties = obj.get('properties', [])
        if properties:
            lines.append("**プロパティ**:")
            lines.append("")
            for prop in properties:
                required_mark = "**必須**" if prop.get('required', False) else "任意"
                lines.append(f"- **{prop['name']}** (型: {prop['type']}, {required_mark})")
                lines.append(f"  - 説明: {prop.get('description', 'N/A')}")
                lines.append("")
        else:
            lines.append("**プロパティ**: なし")
            lines.append("")
        
        return lines

    def _generate_code_samples_section(self, functions: List[Dict]) -> str:
        """コード生成サンプルセクションを生成"""
        lines = [
            "\n## コード生成サンプル一覧\n",
            "以下は、各関数の使用例です。",
            ""
        ]
        
        for func in functions:
            lines.extend(self._generate_function_code_sample(func))
        
        return "\n".join(lines)

    def save_comprehensive_report(self, report_content: str, output_dir: str = "verification_reports") -> None:
        """包括的レポートを保存"""
        output_path = Path(__file__).parent / output_dir
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = self.verification_timestamp.strftime("%Y%m%d_%H%M%S")
        
        # Markdownファイルの保存
        md_filename = f"comprehensive_verification_{timestamp}.md"
        md_path = output_path / md_filename
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"📄 Markdownレポートを保存しました: {md_path}")
        
        # JSONファイルの保存
        json_filename = f"comprehensive_verification_{timestamp}.json"
        json_path = output_path / json_filename
        
        json_data = {
            "timestamp": self.verification_timestamp.isoformat(),
            "database": self.database,
            "statistics": self.stats,
            "verification_summary": {
                "total_functions": self.stats["total_functions"],
                "total_objects": self.stats["total_objects"],
                "total_parameters": self.stats["total_parameters"]
            }
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"📊 JSONレポートを保存しました: {json_path}")

    def verify_specific_function(self, function_name: str, detailed: bool = False) -> Dict[str, Any]:
        """特定の関数を詳細検証"""
        print(f"🔍 関数 '{function_name}' を詳細検証中...")
        
        try:
            spec = self.rag_retriever.get_function_spec(function_name)
            if not spec:
                return {"error": f"関数 '{function_name}' が見つかりません"}
            
            # コード生成サンプルを表示
            params = spec.get('parameters', [])
            self._display_code_sample(function_name, params)
            
            result = {
                "function_name": function_name,
                "specification": spec,
                "verification_status": "SUCCESS"
            }
            
            if detailed:
                result["parameter_verification"] = self._verify_function_parameters(params)
            
            print(f"✅ 関数 '{function_name}' の検証完了")
            return result
            
        except Exception as e:
            print(f"❌ 関数 '{function_name}' の検証でエラー: {e}")
            return {"error": str(e), "function_name": function_name}

    def _verify_function_parameters(self, params: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """関数パラメータの詳細検証"""
        param_verification = []
        
        for param in params:
            param_info = {
                "name": param.get('name'),
                "type": param.get('type'),
                "description": param.get('description'),
                "position": param.get('position'),
                "is_object": param.get('is_object', False)
            }
            
            # オブジェクト定義の存在確認
            if param.get('is_object', False):
                obj_props = self.get_object_properties(param.get('type', ''))
                param_info["object_properties_count"] = len(obj_props)
                param_info["object_properties"] = obj_props
            
            param_verification.append(param_info)
        
        return param_verification

    def verify_specific_object(self, object_name: str, detailed: bool = False) -> Dict[str, Any]:
        """特定のオブジェクトを詳細検証"""
        print(f"🔍 オブジェクト '{object_name}' を詳細検証中...")
        
        try:
            properties = self.get_object_properties(object_name)
            
            result = {
                "object_name": object_name,
                "properties_count": len(properties),
                "properties": properties,
                "verification_status": "SUCCESS"
            }
            
            if detailed:
                result["property_verification"] = self._verify_object_properties(properties)
            
            print(f"✅ オブジェクト '{object_name}' の検証完了")
            return result
            
        except Exception as e:
            print(f"❌ オブジェクト '{object_name}' の検証でエラー: {e}")
            return {"error": str(e), "object_name": object_name}

    def _verify_object_properties(self, properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """オブジェクトプロパティの詳細検証"""
        property_verification = []
        
        for prop in properties:
            prop_info = {
                "name": prop.get('name'),
                "type": prop.get('type'),
                "description": prop.get('description'),
                "required": prop.get('required', False)
            }
            
            # 型の詳細情報
            if prop.get('type'):
                obj_props = self.get_object_properties(prop.get('type'))
                prop_info["referenced_object_properties_count"] = len(obj_props)
            
            property_verification.append(prop_info)
        
        return property_verification

    def run_comprehensive_verification(self) -> Dict[str, Any]:
        """包括的検証を実行"""
        print("🚀 包括的検証を開始します...")
        print(f"📊 対象データベース: {self.database}")
        print("=" * 60)
        
        # データベース概要を取得
        database_summary = self.get_database_summary()
        
        # すべての関数を取得
        functions = self.get_all_functions()
        
        # すべてのオブジェクトを取得
        objects = self.get_all_objects()
        
        # 統計情報を表示
        self._display_verification_summary()
        
        # 包括的レポートを生成
        report_content = self.generate_comprehensive_report(functions, objects, database_summary)
        
        result = {
            "verification_timestamp": self.verification_timestamp.isoformat(),
            "database": self.database,
            "statistics": self.stats,
            "functions_count": len(functions),
            "objects_count": len(objects),
            "report_content": report_content,
            "verification_status": "COMPLETED"
        }
        
        print("\n✅ 包括的検証が完了しました")
        return result

    def _display_verification_summary(self) -> None:
        """検証結果サマリーを表示"""
        print("\n📊 検証結果サマリー")
        print("-" * 40)
        print(f"関数数: {self.stats['total_functions']}")
        print(f"オブジェクト数: {self.stats['total_objects']}")
        print(f"パラメータ数: {self.stats['total_parameters']}")
        print(f"パラメータを持つ関数: {self.stats['functions_with_params']}")
        print(f"プロパティを持つオブジェクト: {self.stats['objects_with_properties']}")

    def close(self):
        """リソースを解放"""
        if hasattr(self, 'rag_retriever'):
            self.rag_retriever.close()
        if hasattr(self, 'neo4j_verifier'):
            self.neo4j_verifier.close()


def main():
    parser = argparse.ArgumentParser(description="包括的検証スクリプト - すべての関数とオブジェクトを一括で確認")
    parser.add_argument("--function", type=str, help="特定の関数を詳細検証")
    parser.add_argument("--object", type=str, help="特定のオブジェクトを詳細検証")
    parser.add_argument("--detailed", action="store_true", help="詳細検証を実行")
    parser.add_argument("--all", action="store_true", help="すべての関数とオブジェクトを一括検証")
    parser.add_argument("--save-docs", action="store_true", help="検証結果をverification_reportsディレクトリに保存")
    parser.add_argument("--output-dir", type=str, default="verification_reports", help="出力ディレクトリ")
    parser.add_argument("--database", type=str, default="docparser", help="使用するNeo4jデータベース名（デフォルト: docparser）")
    args = parser.parse_args()

    # 環境変数を読み込み
    from dotenv import load_dotenv
    load_dotenv()
    
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USER = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
    NEO4J_DATABASE = args.database

    if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
        print("❌ エラー: .envファイルでNeo4j接続情報を設定してください")
        print("必要な環境変数: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD")
        sys.exit(1)

    verifier = ComprehensiveVerifier(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE)

    try:
        if args.function:
            # 特定の関数を検証
            result = verifier.verify_specific_function(args.function, args.detailed)
            print("\n" + "="*60)
            print(f"関数 '{args.function}' の検証結果")
            print("="*60)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
        elif args.object:
            # 特定のオブジェクトを検証
            result = verifier.verify_specific_object(args.object, args.detailed)
            print("\n" + "="*60)
            print(f"オブジェクト '{args.object}' の検証結果")
            print("="*60)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
        elif args.all:
            # 包括的検証を実行
            result = verifier.run_comprehensive_verification()
            
            if args.save_docs:
                verifier.save_comprehensive_report(result["report_content"], args.output_dir)
                
        else:
            # デフォルトで包括的検証を実行
            result = verifier.run_comprehensive_verification()
            
            if args.save_docs:
                verifier.save_comprehensive_report(result["report_content"], args.output_dir)

    except KeyboardInterrupt:
        print("\n⚠️  検証が中断されました")
    except Exception as e:
        print(f"❌ 検証中にエラーが発生しました: {e}")
        sys.exit(1)
    finally:
        verifier.close()


if __name__ == "__main__":
    main()
