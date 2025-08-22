import os
import sys
import argparse
import importlib.util
from neo4j import GraphDatabase
from dotenv import load_dotenv
from .test_dsl import FunctionSpec, Param

class RagRetriever:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.test_results = []

    def close(self):
        self.driver.close()

    def get_function_spec(self, function_name):
        """
        Fetches the full specification for a function, including details of its parameters
        and any nested parameter objects.
        """
        with self.driver.session() as session:
            # Main query to get function, its parameters, and their types
            query = """
            MATCH (f:Function {name: $function_name})
            OPTIONAL MATCH (f)-[r:HAS_PARAMETER]->(p:Parameter)
            OPTIONAL MATCH (p)-[:HAS_TYPE]->(t)
            OPTIONAL MATCH (f)-[:RETURNS]->(ret)
            RETURN
                f.name as name,
                f.description as description,
                COLLECT(DISTINCT {
                    name: p.name,
                    description: p.description,
                    position: r.position,
                    type: t.name,
                    is_object: 'ObjectDefinition' IN labels(t)
                }) as parameters,
                ret.name as return_type,
                ret.description as return_description
            ORDER BY r.position
            """
            result = session.run(query, function_name=function_name).single()

            if not result or not result['name']:
                print(f"Error: Function '{function_name}' not found.", file=sys.stderr)
                return None

            spec = dict(result)
            # Filter out null parameters that can result from the COLLECT of an OPTIONAL MATCH
            spec['parameters'] = [p for p in spec['parameters'] if p['name'] is not None]

            # For parameters that are objects, fetch their properties recursively
            for param in spec['parameters']:
                if param['is_object']:
                    param['properties'] = self._fetch_object_properties(session, param['type'])

            return spec

    def _fetch_object_properties(self, session, object_name):
        """
        Recursively fetches properties for a given ObjectDefinition.
        """
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
            if not record['name']: continue
            prop = dict(record)
            if prop['is_object']:
                prop['properties'] = self._fetch_object_properties(session, prop['type'])
            properties.append(prop)

        return properties

    def display_spec(self, spec):
        """
        Displays the fetched specification in a user-friendly format.
        """
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
            # Sort parameters by position before displaying
            sorted_params = sorted(spec['parameters'], key=lambda p: p.get('position', 0))
            for param in sorted_params:
                self._display_properties([param], indent_level=1)

        print("-" * 25)
        print("Returns:")
        print(f"  Type: {spec.get('return_type')}")
        print(f"  Description: {spec.get('return_description')}")
        print("-------------------------\n")

    def _display_properties(self, properties, indent_level=1):
        """
        Helper function to recursively display parameters or properties.
        """
        indent = "  " * indent_level
        for prop in properties:
            print(f"{indent}- Name: {prop.get('name')}")
            print(f"{indent}  Type: {prop.get('type')}")
            print(f"{indent}  Description: {prop.get('description')}")
            if 'properties' in prop and prop['properties']:
                print(f"{indent}  Properties:")
                self._display_properties(prop['properties'], indent_level + 2)

    def run_test_cases_from_file(self, pattern_path):
        """
        Loads a test pattern file, iterates through its test cases, and runs them.
        """
        print(f"\nRunning tests from: {os.path.basename(pattern_path)}")
        try:
            module_name = os.path.splitext(os.path.basename(pattern_path))[0]
            spec = importlib.util.spec_from_file_location(module_name, pattern_path)
            test_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(test_module)
            test_cases = test_module.test_cases
        except (ImportError, AttributeError, FileNotFoundError) as e:
            details = f"Failed to load test cases from {pattern_path}: {e}"
            # This is a failure of the test file itself, not a specific function test
            self.test_results.append({"function": os.path.basename(pattern_path), "passed": False, "details": details})
            return

        for case in test_cases:
            self.execute_single_test_case(case)

    def execute_single_test_case(self, case):
        """
        Executes a single test case dictionary.
        """
        test_name = case.get("test_name", "Unnamed Test")
        test_type = case.get("test_type", "positive")
        spec_obj = case.get("spec")

        if not spec_obj:
            self.test_results.append({"function": test_name, "passed": False, "details": "Test case is missing 'spec' definition."})
            return

        function_name = spec_obj.name
        expected_spec = spec_obj.to_dict()

        actual_spec = self.get_function_spec(function_name)
        if actual_spec is None:
            details = f"Function '{function_name}' not found in DB for test '{test_name}'."
            self.test_results.append({"function": function_name, "passed": False, "details": details, "test_name": test_name})
            return

        # Sort parameter lists consistently before comparison
        if actual_spec.get('parameters'):
            actual_spec['parameters'] = sorted(actual_spec['parameters'], key=lambda p: p.get('position', 0))

        is_match, details = self._compare_specs(expected_spec, actual_spec)

        passed = False
        if test_type == 'positive':
            passed = is_match
            final_details = " | ".join(details) if not passed else "OK"
        elif test_type == 'negative':
            passed = not is_match
            final_details = "Correctly identified mismatch." if passed else "Failed to identify expected mismatch."

        self.test_results.append({"function": function_name, "passed": passed, "details": final_details, "test_name": test_name})

    def _compare_specs(self, expected, actual, path=""):
        """
        Recursively compares two dictionary/list structures and returns differences.
        """
        errors = []

        # Compare dictionaries
        if isinstance(expected, dict) and isinstance(actual, dict):
            # Sort keys to handle potential ordering differences in the database results
            expected_keys = sorted(expected.keys())
            actual_keys = sorted(actual.keys())

            if expected_keys != actual_keys:
                missing = set(expected_keys) - set(actual_keys)
                extra = set(actual_keys) - set(expected_keys)
                if missing: errors.append(f"Missing keys at {path}: {missing}")
                if extra: errors.append(f"Extra keys at {path}: {extra}")

            common_keys = set(expected_keys) & set(actual_keys)
            for key in common_keys:
                new_path = f"{path}.{key}" if path else key
                # Skip comparing parameter lists here, handled below
                if key in ['parameters', 'properties']:
                    continue
                errors.extend(self._compare_specs(expected[key], actual[key], new_path)[1])

            # Special handling for parameter/property lists
            for key in ['parameters', 'properties']:
                if key in common_keys:
                    new_path = f"{path}.{key}" if path else key
                    errors.extend(self._compare_lists(expected[key], actual[key], new_path))

        # Compare lists (specifically for parameters/properties)
        elif isinstance(expected, list) and isinstance(actual, list):
             errors.extend(self._compare_lists(expected, actual, path))

        # Compare primitive values
        elif expected != actual:
            errors.append(f"Value mismatch at {path}: Expected '{expected}', Got '{actual}'")

        return not errors, errors

    def _compare_lists(self, expected_list, actual_list, path):
        errors = []
        if len(expected_list) != len(actual_list):
            errors.append(f"List length mismatch at {path}: Expected {len(expected_list)}, Got {len(actual_list)}")
            return errors

        # Convert lists of dicts to a dict keyed by name for easier lookup
        expected_dict = {item['name']: item for item in expected_list}
        actual_dict = {item['name']: item for item in actual_list}

        if sorted(expected_dict.keys()) != sorted(actual_dict.keys()):
            missing = set(expected_dict.keys()) - set(actual_dict.keys())
            extra = set(actual_dict.keys()) - set(expected_dict.keys())
            if missing: errors.append(f"Missing items in list {path}: {missing}")
            if extra: errors.append(f"Extra items in list {path}: {extra}")
            return errors

        for name, expected_item in expected_dict.items():
            actual_item = actual_dict[name]
            errors.extend(self._compare_specs(expected_item, actual_item, f"{path}[{name}]")[1])

        return errors

    def get_all_function_names(self):
        """
        Fetches the names of all Function nodes from the database.
        """
        with self.driver.session() as session:
            query = "MATCH (f:Function) RETURN f.name as name ORDER BY f.name"
            records = session.run(query).data()
            return [r['name'] for r in records]


def main():
    parser = argparse.ArgumentParser(description="Run specification tests for GraphRAG data retrieval.")
    parser.add_argument("test_path", nargs='?', default=None, help="Path to a specific test file or directory. If not provided, runs all tests in the 'test_patterns' directory.")
    args = parser.parse_args()

    load_dotenv()
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USER = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

    if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
        print("Error: NEO4J_URI, NEO4J_USER (or NEO4J_USERNAME), and NEO4J_PASSWORD must be set in the .env file.", file=sys.stderr)
        sys.exit(1)

    retriever = RagRetriever(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    try:
        test_paths = []
        if args.test_path:
            if os.path.isdir(args.test_path):
                test_paths = [os.path.join(args.test_path, f) for f in os.listdir(args.test_path) if f.startswith('test_') and f.endswith('.py')]
            elif os.path.isfile(args.test_path):
                test_paths.append(args.test_path)
        else:
            # Default to running all tests in the patterns directory
            patterns_dir = os.path.join(os.path.dirname(__file__), 'test_patterns')
            if os.path.isdir(patterns_dir):
                 test_paths = [os.path.join(patterns_dir, f) for f in os.listdir(patterns_dir) if f.startswith('test_') and f.endswith('.py')]

        if not test_paths:
            print("No test files found.")
            return

        for path in test_paths:
            retriever.run_test_cases_from_file(path)

        # Print final summary
        print("\n--- Final Test Summary ---")
        passed_count = sum(1 for r in retriever.test_results if r.get('passed'))
        total_tests = len(retriever.test_results)

        for result in retriever.test_results:
            status = "✅ PASSED" if result.get('passed') else "❌ FAILED"
            if not result.get('passed'):
                print(f"  - {status} - Test '{result['test_name']}' in {result['function']}: {result['details']}")

        print(f"\nSummary: {passed_count}/{total_tests} tests passed.")

    finally:
        retriever.close()

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    main()
