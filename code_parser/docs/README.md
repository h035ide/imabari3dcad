# Code Parser

This module is responsible for parsing Python source code files, analyzing their structure, and storing the results as a knowledge graph in a Neo4j database.

## Usage

The main script for this module is `parse_code.py`. It can be run from the project's root directory.

### Prerequisites

Before running the script, you must have a `.env` file in the project root directory with the following variables defined:

```
NEO4J_URI="neo4j://your_neo4j_host:7687"
NEO4J_USER="your_username"
NEO4J_PASSWORD="your_password"
# Optional: for LLM analysis
OPENAI_API_KEY="your_openai_api_key"
```

You can use the `.env.example` file in the root directory as a template.

### Running the script

To parse a specific file:
```bash
python code_parser/parse_code.py path/to/your/python_file.py
```

If you don't provide a file path, it will default to parsing `evoship/create_test.py`:
```bash
python code_parser/parse_code.py
```

You can also specify the Neo4j database name or disable LLM features:
```bash
python code_parser/parse_code.py --db-name my_graph_db --no-llm
```
