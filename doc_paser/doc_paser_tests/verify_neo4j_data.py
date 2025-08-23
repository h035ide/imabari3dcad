import os
import sys
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv

class Neo4jVerifier:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.results = {}
        self.json_data = self._load_json_data()

    def close(self):
        self.driver.close()

    def _load_json_data(self):
        json_path = os.path.join(os.path.dirname(__file__), 'parsed_api_result.json')
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: JSON file not found at {json_path}")
            return None
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {json_path}")
            return None

    def run_all_checks(self):
        if not self.json_data:
            print("Aborting checks because JSON data could not be loaded.")
            return

        print("--- Starting Neo4j Data Verification ---")
        self.check_node_counts()
        self.check_function_integrity()
        self.check_object_definition_integrity()
        self.check_feeds_into_relationships()
        self.check_for_orphan_nodes()
        print("-----------------------------------------")

        return self.results

    def check_for_orphan_nodes(self):
        print("\n[5] Checking for orphan nodes...")
        self.results['orphan_nodes'] = []

        with self.driver.session() as session:
            # Check for orphan Parameter nodes
            query_orphan_params = """
            MATCH (p:Parameter)
            WHERE NOT (p)<-[:HAS_PARAMETER]-() AND NOT (p)<-[:HAS_PROPERTY]-()
            RETURN p.name, p.parent_function, p.parent_object
            """
            orphan_params = session.run(query_orphan_params).data()
            if orphan_params:
                for p in orphan_params:
                    details = f"Orphan Parameter found: {p['p.name']} (parent_function: {p.get('p.parent_function')}, parent_object: {p.get('p.parent_object')})"
                    self._add_result('orphan_nodes', False, details)

            # Check for unlinked ObjectDefinition nodes
            query_orphan_objs = """
            MATCH (od:ObjectDefinition)
            WHERE NOT ()-[:RETURNS]->(od) AND NOT ()-[:HAS_TYPE]->(od)
            RETURN od.name
            """
            orphan_objs = session.run(query_orphan_objs).data()
            if orphan_objs:
                for obj in orphan_objs:
                    details = f"Unlinked ObjectDefinition found: {obj['od.name']}"
                    self._add_result('orphan_nodes', False, details)

        if not self.results['orphan_nodes']:
            print("  ✅ PASSED - No orphan nodes found.")
            self._add_result('orphan_nodes', True, "No orphan nodes found.")
        else:
            print(f"  ❌ FAILED - Found {len(self.results['orphan_nodes'])} orphan/unlinked nodes.")

    def check_feeds_into_relationships(self):
        print("\n[4] Verifying 'FEEDS_INTO' relationships...")
        self.results['feeds_into'] = []

        # 1. Find expected relationships from JSON
        functions = {f['name']: f for f in self.json_data['api_entries'] if f['entry_type'] == 'function'}
        object_defs = {o['name'] for o in self.json_data['api_entries'] if o['entry_type'] == 'object_definition'}

        expected_rels = set()
        for func_name, func_data in functions.items():
            return_type = func_data.get('returns', {}).get('type')
            if return_type in object_defs:
                # This function returns an object. Now find who consumes it.
                for consumer_name, consumer_data in functions.items():
                    for param in consumer_data.get('params', []):
                        if param.get('type') == return_type:
                            expected_rels.add((func_name, consumer_name, return_type))

        # 2. Get actual relationships from DB
        with self.driver.session() as session:
            query = "MATCH (a:Function)-[r:FEEDS_INTO]->(b:Function) RETURN a.name, b.name, r.via_object"
            records = session.run(query).data()
            actual_rels = {(r['a.name'], r['b.name'], r['r.via_object']) for r in records}

        # 3. Compare
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
            status = "✅ PASSED"
            print(f"  {status} - All {total_count} FEEDS_INTO relationships are correct.")
            self._add_result('feeds_into', True, f"All {total_count} FEEDS_INTO relationships verified.")
        else:
            status = "❌ FAILED"
            print(f"  {status} - Verified {passed_count}/{total_count} correctly. Found {len(missing_rels)} missing and {len(extra_rels)} extra relationships.")

    def check_object_definition_integrity(self):
        print("\n[3] Verifying object definition integrity...")
        self.results['object_definition_integrity'] = []
        obj_defs_in_json = [entry for entry in self.json_data.get('api_entries', []) if entry.get('entry_type') == 'object_definition']

        with self.driver.session() as session:
            for obj_json in obj_defs_in_json:
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
                    self._add_result('object_definition_integrity', False, f"ObjectDefinition '{obj_name}' not found in DB.")
                    continue

                # Verify properties
                json_props = obj_json.get('properties', [])
                db_props_list = [r for r in records if r['prop_name']]
                if len(json_props) != len(db_props_list):
                    self._add_result('object_definition_integrity', False, f"ObjectDefinition '{obj_name}' has wrong property count. JSON: {len(json_props)}, DB: {len(db_props_list)}")
                    continue

                all_props_match = True
                for prop_json in json_props:
                    prop_found_in_db = any(prop_json['name'] == prop_db.get('prop_name') and prop_json['type'] == prop_db.get('prop_type') for prop_db in db_props_list)
                    if not prop_found_in_db:
                        all_props_match = False
                        self._add_result('object_definition_integrity', False, f"Property '{prop_json['name']}' of ObjectDefinition '{obj_name}' not found or has mismatched type.")

                if all_props_match and len(json_props) == len(db_props_list):
                    self._add_result('object_definition_integrity', True, f"ObjectDefinition '{obj_name}' and its properties are consistent.")

        passed_count = sum(1 for r in self.results['object_definition_integrity'] if r['passed'])
        total_count = len(obj_defs_in_json)
        status = "✅ PASSED" if passed_count == total_count else "❌ FAILED"
        print(f"  {status} - Verified {passed_count}/{total_count} object definitions successfully.")

    def check_function_integrity(self):
        print("\n[2] Verifying function and parameter integrity...")
        self.results['function_integrity'] = []
        functions_in_json = [entry for entry in self.json_data.get('api_entries', []) if entry.get('entry_type') == 'function']

        with self.driver.session() as session:
            for func_json in functions_in_json:
                func_name = func_json['name']

                # Fetch function and its parameters from DB
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
                    continue

                # Verify function description
                db_func_desc = records[0]['description']
                if db_func_desc != func_json.get('description'):
                    self._add_result('function_integrity', False, f"Function '{func_name}' description mismatch.")

                # Verify parameter count
                json_params = func_json.get('params', [])
                db_params_list = [r for r in records if r['param_name']]
                if len(json_params) != len(db_params_list):
                    self._add_result('function_integrity', False, f"Function '{func_name}' has wrong parameter count. JSON: {len(json_params)}, DB: {len(db_params_list)}")
                    continue

                # Verify each parameter
                all_params_match = True
                for param_json in json_params:
                    param_found_in_db = False
                    for param_db in db_params_list:
                        if param_json['name'] == param_db['param_name']:
                            param_found_in_db = True
                            # Check position and type
                            if param_json.get('position') != param_db.get('position') or \
                               param_json.get('type') != param_db.get('param_type'):
                                all_params_match = False
                                self._add_result('function_integrity', False, f"Parameter '{param_json['name']}' of function '{func_name}' has mismatched properties (position/type).")
                            break
                    if not param_found_in_db:
                        all_params_match = False
                        self._add_result('function_integrity', False, f"Parameter '{param_json['name']}' of function '{func_name}' not found in DB.")

                if all_params_match and len(json_params) == len(db_params_list):
                     self._add_result('function_integrity', True, f"Function '{func_name}' and its parameters are consistent.")

        # Report summary for this check
        passed_count = sum(1 for r in self.results['function_integrity'] if r['passed'])
        total_count = len(functions_in_json)
        status = "✅ PASSED" if passed_count == total_count else "❌ FAILED"
        print(f"  {status} - Verified {passed_count}/{total_count} functions successfully.")


    def _add_result(self, category, passed, details):
        if category not in self.results:
            self.results[category] = []

        # To avoid verbose success messages, only print failures here
        if not passed:
            print(f"  ❌ FAILED: {details}")

        self.results[category].append({
            "check": details.split("'")[1] if "'" in details else "General Check",
            "passed": passed,
            "details": details
        })

    def check_node_counts(self):
        print("\n[1] Verifying node counts...")
        self.results['node_counts'] = []

        # Define what to check
        checks = {
            "Function": {"label": "Function", "json_key": "api_entries", "filter": lambda x: x['entry_type'] == 'function'},
            "ObjectDefinition": {"label": "ObjectDefinition", "json_key": "api_entries", "filter": lambda x: x['entry_type'] == 'object_definition'},
            "Type": {"label": "Type", "json_key": "type_definitions", "filter": lambda x: True},
        }

        with self.driver.session() as session:
            for name, check in checks.items():
                # Count from JSON
                json_count = len([item for item in self.json_data[check['json_key']] if check['filter'](item)])

                # Count from Neo4j
                query = f"MATCH (n:{check['label']}) RETURN count(n) as count"
                result = session.run(query).single()
                db_count = result['count'] if result else 0

                # Compare and store results
                is_match = json_count == db_count
                status = "✅ PASSED" if is_match else "❌ FAILED"
                message = f"{name} count: JSON ({json_count}) vs DB ({db_count})"
                print(f"  {status} - {message}")
                self.results['node_counts'].append({
                    "check": f"{name} count",
                    "passed": is_match,
                    "details": message
                })

def main():
    load_dotenv()

    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USER = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

    if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
        print("Error: NEO4J_URI, NEO4J_USER (or NEO4J_USERNAME), and NEO4J_PASSWORD must be set in the .env file.")
        return

    verifier = Neo4jVerifier(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    try:
        results = verifier.run_all_checks()

        print("\n--- Verification Summary ---")
        all_passed = True
        for category, checks in results.items():
            for check in checks:
                if not check['passed']:
                    all_passed = False
                    print(f"❌ FAILED: {check['check']} - {check['details']}")

        if all_passed:
            print("✅ All verification checks passed!")
        else:
            print("\nSome verification checks failed.")

    finally:
        verifier.close()

if __name__ == "__main__":
    # Ensure the project root is in the Python path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    main()
