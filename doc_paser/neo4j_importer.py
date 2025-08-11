# This script will be used to import the parsed API data into a Neo4j database.
import os
import sys
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv

class Neo4jImporter:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def import_data(self, data):
        with self.driver.session() as session:
            self._import_type_definitions(session, data.get("type_definitions", []))
            self._import_api_entries(session, data.get("api_entries", []))
            self._create_dependency_links(session)
        print("Data import completed.")

    def _create_dependency_links(self, session):
        print("Creating function dependency links...")
        query = """
        MATCH (func_a:Function)-[:RETURNS]->(obj:ObjectDefinition)
        MATCH (func_b:Function)-[:HAS_PARAMETER]->(param:Parameter)-[:HAS_TYPE]->(obj)
        MERGE (func_a)-[r:FEEDS_INTO]->(func_b)
        SET r.via_object = obj.name
        """
        try:
            result = session.run(query)
            # Use consume() method for Neo4j Python Driver 4.0+
            summary = result.consume()
            print(f"  - Created {summary.counters.relationships_created} 'FEEDS_INTO' relationships.")
        except Exception as e:
            print(f"  - Warning: Could not create dependency links: {e}")

    def _import_type_definitions(self, session, type_definitions):
        print("Importing type definitions...")
        query = """
        UNWIND $types as type_data
        MERGE (t:Type {name: type_data.name})
        SET t.description = type_data.description
        """
        session.run(query, types=type_definitions)

    def _import_api_entries(self, session, api_entries):
        print("Importing API entries...")
        for entry in api_entries:
            if entry.get("entry_type") == "function":
                self._create_function_graph(session, entry)
            elif entry.get("entry_type") == "object_definition":
                self._create_object_definition_graph(session, entry)

    def _create_function_graph(self, session, func_data):
        # Create the function node first
        func_query = """
        MERGE (f:Function {name: $func.name})
        SET f.description = $func.description, f.category = $func.category,
            f.implementation_status = $func.implementation_status, f.notes = $func.notes
        """
        session.run(func_query, func=func_data)
        
        # Handle parameters individually to avoid duplication
        if func_data.get('params'):
            for param_data in func_data['params']:
                param_query = """
                MATCH (f:Function {name: $func_name})
                MERGE (p:Parameter {name: $param_name, parent_function: $func_name})
                SET p.description = $param_description, p.is_required = $param_required
                MERGE (f)-[r:HAS_PARAMETER]->(p)
                SET r.position = $param_position
                
                // Link parameter to its type
                WITH p
                OPTIONAL MATCH (od:ObjectDefinition {name: $param_type})
                MERGE (t:Type {name: $param_type})
                WITH p, COALESCE(od, t) as type_node
                MERGE (p)-[:HAS_TYPE]->(type_node)
                """
                
                session.run(param_query, 
                          func_name=func_data['name'],
                          param_name=param_data['name'],
                          param_description=param_data.get('description', ''),
                          param_required=param_data.get('is_required', False),
                          param_position=param_data.get('position', 0),
                          param_type=param_data['type'])
        
        # Handle return value
        if func_data.get('returns'):
            return_query = """
            MATCH (f:Function {name: $func_name})
            MERGE (rt:Type {name: $return_type})
            MERGE (f)-[:RETURNS]->(rt)
            """
            session.run(return_query, func_name=func_data['name'], return_type=func_data['returns'].get('type'))
        
        print(f"  - Imported function: {func_data['name']}")

    def _create_object_definition_graph(self, session, obj_data):
        # Create the object definition node
        obj_query = """
        MERGE (od:ObjectDefinition {name: $obj.name})
        SET od.description = $obj.description, od.category = $obj.category, od.notes = $obj.notes
        """
        session.run(obj_query, obj=obj_data)
        
        # Handle properties in a separate query to avoid variable scope issues
        if obj_data.get('properties'):
            for prop_data in obj_data['properties']:
                prop_query = """
                MATCH (od:ObjectDefinition {name: $obj_name})
                MERGE (p:Parameter {name: $prop_name, parent_object: $obj_name})
                SET p.description = $prop_description
                MERGE (od)-[:HAS_PROPERTY]->(p)
                
                // Link property to its type
                WITH p
                OPTIONAL MATCH (prop_od:ObjectDefinition {name: $prop_type})
                MERGE (t:Type {name: $prop_type})
                WITH p, COALESCE(prop_od, t) as type_node
                MERGE (p)-[:HAS_TYPE]->(type_node)
                """
                session.run(prop_query, 
                          obj_name=obj_data['name'],
                          prop_name=prop_data['name'],
                          prop_description=prop_data.get('description', ''),
                          prop_type=prop_data['type'])
        
        print(f"  - Imported object definition: {obj_data['name']}")

def main():
    print("Neo4j Importer script started.")
    load_dotenv()

    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USER = os.getenv("NEO4J_USERNAME")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

    if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
        print("Error: NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD must be set in the .env file.")
        return

    importer = Neo4jImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        with open('doc_paser/parsed_api_result.json', 'r', encoding='utf-8') as f:
            api_data = json.load(f)
        importer.import_data(api_data)
    except FileNotFoundError:
        print("Error: `doc_paser/parsed_api_result.json` not found.")
        print("Please run `doc_paser.py` first to generate the JSON file.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        importer.close()
    print("Neo4j Importer script finished.")


if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    print(f"プロジェクトルートパス: {project_root}")
    main()
