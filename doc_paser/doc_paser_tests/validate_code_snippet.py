import os
import sys
import argparse
import ast
from neo4j import GraphDatabase
from dotenv import load_dotenv
# Reuse the retriever class to fetch data from Neo4j
from .test_rag_retrieval import RagRetriever

class CodeValidator:
    def __init__(self, retriever):
        self.retriever = retriever

    def validate_snippet(self, snippet_path):
        """
        Validates a Python code snippet against the database specification.
        Returns a tuple: (is_match: bool, details: str, test_type: str)
        """
        print(f"Validating snippet: {snippet_path}")

        with open(snippet_path, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            content = first_line + f.read()

        # Determine test type from comment
        test_type = 'positive' # default
        if '# test_type:' in first_line:
            test_type = first_line.split(':')[-1].strip()

        if test_type not in ['positive', 'negative']:
             return False, f"Invalid test_type '{test_type}' in snippet.", test_type

        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return False, f"Invalid Python syntax in snippet: {e}", test_type

        call_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_node = node
                break

        if not call_node or not isinstance(call_node.func, ast.Attribute):
            return False, "No valid function call found in snippet.", test_type

        function_name = call_node.func.attr
        arg_count = len(call_node.args)

        spec = self.retriever.get_function_spec(function_name)
        if not spec:
            return False, f"Function '{function_name}' not found in the database.", test_type

        param_count = len(spec.get('parameters', []))

        is_match = (arg_count == param_count)
        details = f"Code arg count ({arg_count}) vs DB spec count ({param_count})"

        return is_match, details, test_type

def main():
    parser = argparse.ArgumentParser(description="Validate a Python code snippet against the function specification in the Neo4j database.")
    parser.add_argument("snippet_path", type=str, help="Path to the Python code snippet file to validate.")
    args = parser.parse_args()

    if not os.path.exists(args.snippet_path):
        print(f"Error: Snippet file not found at '{args.snippet_path}'", file=sys.stderr)
        sys.exit(1)

    load_dotenv()
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USER = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

    if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
        print("Error: Neo4j connection details must be set in .env file.", file=sys.stderr)
        sys.exit(1)

    retriever = RagRetriever(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    validator = CodeValidator(retriever)

    try:
        is_match, details, test_type = validator.validate_snippet(args.snippet_path)

        passed = False
        if test_type == 'positive':
            passed = is_match
            final_details = f"Positive test. {details}"
        elif test_type == 'negative':
            passed = not is_match
            final_details = f"Negative test. Correctly identified mismatch: {details}" if passed else f"Negative test. FAILED to identify mismatch: {details}"

        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"\n--- Validation Result ---")
        print(f"Test Type: {test_type}")
        print(f"{status}: {final_details}")

    finally:
        retriever.close()

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    main()
