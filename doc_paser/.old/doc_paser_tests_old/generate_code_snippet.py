import os
import sys
import argparse
import json
from datetime import datetime
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv

# プロジェクトルートを設定して相対インポートの問題を解決
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# RagRetrieverクラスをインポート
try:
    from test_rag_retrieval import RagRetriever
except ImportError:
    # 相対インポートが失敗した場合のフォールバック
    sys.path.insert(0, os.path.dirname(__file__))
    from test_rag_retrieval import RagRetriever

class CodeGenerator:
    def __init__(self, retriever):
        self.retriever = retriever
        self.generation_timestamp = datetime.now()

    def generate_snippet(self, function_name):
        """
        Generates a Python code snippet from a function specification in the database.
        """
        print(f"Generating snippet for function: {function_name}")

        spec = self.retriever.get_function_spec(function_name)
        if not spec:
            print(f"Error: Could not retrieve spec for function '{function_name}'", file=sys.stderr)
            return None

        params = spec.get('parameters', [])
        if not params:
            return f"part.{function_name}()"

        # Sort params by position to ensure correct argument order
        sorted_params = sorted(params, key=lambda p: p.get('position', 0))

        # Build the argument string with one parameter per line
        arg_string = ",\n    ".join([p['name'] for p in sorted_params])

        # Construct the final code snippet
        code_snippet = f"part.{function_name}(\n    {arg_string}\n)"

        return code_snippet

    def save_results(self, function_name, generated_code, validation_result=None, output_dir="verification_reports"):
        """
        Save generation results to markdown and JSON files
        """
        # 出力ディレクトリのパスを設定（現在のディレクトリからの相対パス）
        output_path = Path(__file__).parent / output_dir
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = self.generation_timestamp.strftime("%Y%m%d_%H%M%S")
        
        # Markdownファイルの保存
        md_filename = f"{function_name}_code_generation_{timestamp}.md"
        md_path = output_path / md_filename
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f"# コード生成結果レポート\n\n")
            f.write(f"**生成日時**: {self.generation_timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**対象関数**: {function_name}\n")
            f.write(f"**データベース**: docparser\n\n")
            
            f.write("## 生成されたコード\n\n")
            f.write("```python\n")
            f.write(generated_code)
            f.write("\n```\n\n")
            
            if validation_result:
                f.write("## 検証結果\n\n")
                f.write(f"**検証結果**: {validation_result['status']}\n")
                if validation_result.get('golden_path'):
                    f.write(f"**ゴールデンパターン**: {validation_result['golden_path']}\n")
                if validation_result.get('differences'):
                    f.write(f"**差分**: {validation_result['differences']}\n")
            
            f.write("\n## 関数仕様\n\n")
            spec = self.retriever.get_function_spec(function_name)
            if spec:
                f.write(f"**説明**: {spec.get('description', 'N/A')}\n")
                f.write(f"**戻り値の型**: {spec.get('return_type', 'N/A')}\n")
                f.write(f"**戻り値の説明**: {spec.get('return_description', 'N/A')}\n\n")
                
                params = spec.get('parameters', [])
                if params:
                    f.write("**パラメータ**:\n\n")
                    for param in sorted(params, key=lambda p: p.get('position', 0)):
                        f.write(f"- **{param['name']}** (位置: {param.get('position', 'N/A')}, 型: {param.get('type', 'N/A')})\n")
                        f.write(f"  - 説明: {param.get('description', 'N/A')}\n")
                        f.write(f"  - オブジェクト定義: {'はい' if param.get('is_object', False) else 'いいえ'}\n\n")

        print(f"Markdownレポートを保存しました: {md_path}")

        # JSONファイルの保存
        json_filename = f"{function_name}_code_generation_{timestamp}.json"
        json_path = output_path / json_filename
        
        result_data = {
            "timestamp": self.generation_timestamp.isoformat(),
            "function_name": function_name,
            "database": "docparser",
            "generated_code": generated_code,
            "validation_result": validation_result,
            "function_spec": self.retriever.get_function_spec(function_name)
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        print(f"JSONレポートを保存しました: {json_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate and optionally validate a Python code snippet from a function specification in the Neo4j database.")
    parser.add_argument("function_name", type=str, help="The name of the function to generate code for.")
    parser.add_argument("--validate", nargs='?', const=True, default=False, metavar="GOLDEN_PATH", help="Validate generated code against a golden pattern. If no path is given, defaults to 'golden_snippets/{function_name}_golden.py'.")
    parser.add_argument("--save-docs", action="store_true", help="Save generation results to verification_reports directory")
    parser.add_argument("--output-dir", type=str, default="verification_reports", help="Output directory for reports (relative to doc_paser/doc_paser_tests/)")
    args = parser.parse_args()

    load_dotenv()
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USER = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
    NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "docparser")

    if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
        print("Error: Neo4j connection details must be set in .env file.", file=sys.stderr)
        print("Required environment variables: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD", file=sys.stderr)
        sys.exit(1)

    print(f"Connecting to Neo4j database: {NEO4J_DATABASE}")
    retriever = RagRetriever(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, database=NEO4J_DATABASE)
    generator = CodeGenerator(retriever)

    try:
        generated_code = generator.generate_snippet(args.function_name)

        if not generated_code:
            print("Failed to generate code.", file=sys.stderr)
            sys.exit(1)

        print("\n--- Generated Code ---")
        print(generated_code)
        print("----------------------\n")

        validation_result = None
        
        if args.validate:
            golden_path = args.validate if isinstance(args.validate, str) else os.path.join(os.path.dirname(__file__), 'golden_snippets', f"{args.function_name}_golden.py")

            print(f"--- Validating against Golden Pattern ---")
            print(f"Golden pattern path: {golden_path}")

            try:
                with open(golden_path, 'r', encoding='utf-8') as f:
                    golden_code = f.read()

                # Normalize both strings for a more robust comparison (strip whitespace)
                is_match = generated_code.strip() == golden_code.strip()

                validation_result = {
                    "status": "PASSED" if is_match else "FAILED",
                    "golden_path": golden_path,
                    "golden_code": golden_code,
                    "is_match": is_match
                }

                if is_match:
                    print("✅ PASSED: Generated code matches the golden pattern.")
                else:
                    print("❌ FAILED: Generated code does not match the golden pattern.")
                    print("\n--- Differences ---")
                    print("Expected:")
                    print(golden_code)
                    print("\nGot:")
                    print(generated_code)
                    print("-------------------")
                    
                    # 差分の詳細を記録
                    validation_result["differences"] = {
                        "expected": golden_code.strip(),
                        "actual": generated_code.strip()
                    }

            except FileNotFoundError:
                print(f"❌ FAILED: Golden pattern file not found at '{golden_path}'")
                validation_result = {
                    "status": "ERROR",
                    "error": "Golden pattern file not found",
                    "golden_path": golden_path
                }

        # 結果の保存
        if args.save_docs:
            generator.save_results(args.function_name, generated_code, validation_result, args.output_dir)

    except Exception as e:
        print(f"Error during code generation: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        retriever.close()

if __name__ == "__main__":
    main()
