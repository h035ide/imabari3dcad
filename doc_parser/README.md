# API Document Parser and Neo4j Importer

This document describes the workflow for parsing the natural language API documentation and importing it into a Neo4j graph database. This process is a preparatory step for a larger system aimed at automated Python code generation.

This directory contains two main scripts:

1.  **`doc_paser.py`**: Reads unstructured API documentation from `data/src/*.txt`, uses a Large Language Model (LLM) to parse the content, and generates a structured JSON file (`parsed_api_result.json`).
2.  **`neo4j_importer.py`**: Takes the generated JSON file and imports its data into a Neo4j database, creating a graph structure optimized for querying by a code generation system.

## Setup

### 1. Install Dependencies

From the project root directory, ensure all required Python packages are installed:

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

This system requires credentials for both the OpenAI API and your Neo4j database. These should be stored in a `.env` file in the **project root**.

Create a file named `.env` and add the following content, replacing the placeholder values:

```
# For doc_paser.py
OPENAI_API_KEY="your_openai_api_key_here"

# For neo4j_importer.py
NEO4J_URI="bolt://localhost:7687"
NEO4J_USER="neo4j"
NEO4J_PASSWORD="your_neo4j_password"
```

## Usage

The scripts must be run from the **project root directory** in the correct order.

### Step 1: Parse the API Documentation

Run the `doc_paser.py` script to generate the structured JSON file.

```bash
python3 doc_paser/doc_paser.py
```

This will create `doc_paser/parsed_api_result.json`. The script is currently configured to run in a "mock mode" and will produce a sample JSON file without needing a real OpenAI API key. To run it in live mode, you will need to edit the `main` function in `doc_paser.py` to restore the LLM call chain.

### Step 2: Import the Data into Neo4j

After the JSON file has been generated, run the `neo4j_importer.py` script to populate the Neo4j database.

```bash
python3 doc_paser/neo4j_importer.py
```

This script connects to the Neo4j instance specified in your `.env` file and builds the graph.

## Graph Model for Code Generation

The importer creates a specific graph structure designed to support automated code generation.

### Node Labels

-   `(:Function)`: An API function.
-   `(:ObjectDefinition)`: A complex parameter object (e.g., `押し出しパラメータオブジェクト`).
-   `(:Parameter)`: A parameter for a function or a property of an object.
-   `(:Type)`: A basic data type (e.g., `文字列`, `長さ`).

### Relationship Types

-   `[:HAS_PARAMETER {position: integer}]`: Links a function to its parameters, preserving order.
-   `[:HAS_PROPERTY]`: Links an object definition to its properties.
-   `[:HAS_TYPE]`: Links a parameter/property to its type.
-   `[:RETURNS]`: Links a function to its return type.
-   `[:FEEDS_INTO {via_object: string}]`: A powerful, direct link between two functions. This relationship is created when the return value of one function (e.g., `CreateLinearSweepParam`) is an object that is used as a parameter in another function (e.g., `CreateLinearSweep`). This explicitly models the "Builder Pattern" and makes discovering code generation workflows much simpler.

This graph structure allows a code generation AI to traverse the dependencies and understand the correct sequence of operations needed to build valid code.
