# This script will be used to import the parsed API data into a Neo4j database.
import os
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
        result = session.run(query)
        summary = result.summary()
        print(f"  - Created {summary.counters.relationships_created} 'FEEDS_INTO' relationships.")

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
        query = """
        // Create the function node
        MERGE (f:Function {name: $func.name})
        SET f.description = $func.description, f.category = $func.category,
            f.implementation_status = $func.implementation_status, f.notes = $func.notes

        // Handle parameters
        WITH f
        UNWIND $func.params as param_data
        MERGE (p:Parameter {name: param_data.name, parent_function: $func.name})
        SET p.description = param_data.description, p.is_required = param_data.is_required
        MERGE (f)-[r:HAS_PARAMETER]->(p)
        SET r.position = param_data.position

        // Link parameter to its type (either a Type or an ObjectDefinition)
        WITH p, param_data
        // Try to match with an ObjectDefinition first
        OPTIONAL MATCH (od:ObjectDefinition {name: param_data.type})
        // If not found, merge as a simple Type
        MERGE (t:Type {name: param_data.type})
        // If the object definition was found, create a link to it, otherwise to the type
        WITH p, COALESCE(od, t) as type_node
        MERGE (p)-[:HAS_TYPE]->(type_node)

        // Handle return value
        WITH f
        // If there is a return type, merge it and link
        FOREACH (ret IN CASE WHEN $func.returns IS NOT NULL THEN [1] ELSE [] END |
            MERGE (rt:Type {name: $func.returns.type})
            MERGE (f)-[:RETURNS]->(rt)
        )
        """
        session.run(query, func=func_data)
        print(f"  - Imported function: {func_data['name']}")

    def _create_object_definition_graph(self, session, obj_data):
        query = """
        // Create the object definition node
        MERGE (od:ObjectDefinition {name: $obj.name})
        SET od.description = $obj.description, od.category = $obj.category, od.notes = $obj.notes

        // Handle properties
        WITH od
        UNWIND $obj.properties as prop_data
        MERGE (p:Parameter {name: prop_data.name, parent_object: $obj.name})
        SET p.description = prop_data.description
        MERGE (od)-[:HAS_PROPERTY]->(p)

        // Link property to its type
        WITH p, prop_data
        OPTIONAL MATCH (prop_od:ObjectDefinition {name: prop_data.type})
        MERGE (t:Type {name: prop_data.type})
        WITH p, COALESCE(prop_od, t) as type_node
        MERGE (p)-[:HAS_TYPE]->(type_node)
        """
        session.run(query, obj=obj_data)
        print(f"  - Imported object definition: {obj_data['name']}")

def main():
    print("Neo4j Importer script started.")
    load_dotenv()

    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USER = os.getenv("NEO4J_USER")
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
    main()
