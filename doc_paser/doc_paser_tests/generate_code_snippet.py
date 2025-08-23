import os
import sys
import argparse
from neo4j import GraphDatabase
from dotenv import load_dotenv
# Reuse the retriever class to fetch data from Neo4j
from .test_rag_retrieval import RagRetriever

class CodeGenerator:
    def __init__(self, retriever):
        self.retriever = retriever

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

def main():
    parser = argparse.ArgumentParser(description="Generate and optionally validate a Python code snippet from a function specification in the Neo4j database.")
    parser.add_argument("function_name", type=str, help="The name of the function to generate code for.")
    parser.add_argument("--validate", nargs='?', const=True, default=False, metavar="GOLDEN_PATH", help="Validate generated code against a golden pattern. If no path is given, defaults to 'golden_snippets/{function_name}_golden.py'.")
    args = parser.parse_args()

    load_dotenv()
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USER = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

    if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
        print("Error: Neo4j connection details must be set in .env file.", file=sys.stderr)
        sys.exit(1)

    retriever = RagRetriever(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    generator = CodeGenerator(retriever)

    try:
        generated_code = generator.generate_snippet(args.function_name)

        if not generated_code:
            print("Failed to generate code.", file=sys.stderr)
            sys.exit(1)

        print("\n--- Generated Code ---")
        print(generated_code)
        print("----------------------\n")

        if args.validate:
            golden_path = args.validate if isinstance(args.validate, str) else os.path.join(os.path.dirname(__file__), 'golden_snippets', f"{args.function_name}_golden.py")

            print(f"--- Validating against Golden Pattern ---")
            print(f"Golden pattern path: {golden_path}")

            try:
                with open(golden_path, 'r', encoding='utf-8') as f:
                    golden_code = f.read()

                # Normalize both strings for a more robust comparison (strip whitespace)
                is_match = generated_code.strip() == golden_code.strip()

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

            except FileNotFoundError:
                print(f"❌ FAILED: Golden pattern file not found at '{golden_path}'")

    finally:
        retriever.close()

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    main()
