# Imabari 3D CAD with Graph RAG

Imabari 3D CAD is a Python-based application that combines 3D CAD capabilities with AI-powered graph retrieval-augmented generation (RAG). The system uses Tree-sitter for code parsing, Neo4j for graph storage, and LlamaIndex with OpenAI for intelligent code analysis and documentation querying.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Bootstrap and Dependencies
- **CRITICAL**: Install Python 3.10+ first: `python3 --version` (current system has Python 3.12.3)
- **NEVER CANCEL**: Dependency installation takes 45-70 minutes. Set timeout to 90+ minutes minimum.
- Install dependencies: `pip install -e .` -- **NEVER CANCEL** this command. Full installation requires 90+ minutes.
- If installation fails due to network timeouts, retry with: `pip install --timeout 1000 -e .`
- Alternative dependency installation: `pip install -r requirements.txt` -- takes 45-60 minutes. **NEVER CANCEL**.

### Required External Services
- **Neo4j Database**: Download and install Neo4j Community Edition from https://neo4j.com/download/
  - Start Neo4j: `neo4j start` or use Neo4j Desktop
  - Default connection: `bolt://localhost:7687` with username `neo4j`
  - **CRITICAL**: Set password during first setup
- **OpenAI API**: Obtain API key from https://platform.openai.com/api-keys

### Environment Configuration
- Create `.env` file in project root with:
```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password
NEO4J_DATABASE=neo4j

# OpenAI Configuration  
OPENAI_API_KEY=your_openai_api_key

# Graph RAG Configuration
SKIP_GRAPH_BUILD=false
CLEAR_GRAPH_DATA=false
EXTRACTION_LLM_MODEL=gpt-4o
AGENT_LLM_MODEL=gpt-4o

# LangSmith (optional)
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_PROJECT=imabari3dcad-api-docs
```

### Build and Test
- **No build step required** - this is a pure Python project using setuptools
- Test Neo4j connection: `python test.py --test-connection` -- takes 30-60 seconds
- **NEVER CANCEL**: Run integration tests: `python test_treesitter_neo4j_integration.py` -- takes 15-30 minutes
- Test basic functionality: `python -c "print('Basic Python test successful')"` -- takes 2-3 seconds

### Run Applications
- **Basic RAG**: `python main.py` -- takes 5-10 minutes for initial index building. **NEVER CANCEL**.
- **Graph RAG with Chat**: `python graph_rag_app.py` -- takes 10-45 minutes for knowledge graph construction. **NEVER CANCEL**.
- **Tree-sitter Analysis**: `python test.py` -- takes 2-5 minutes for code parsing and graph building

## Validation

### Manual Testing Scenarios
- **ALWAYS** run through these validation scenarios after making changes:

#### Scenario 1: Basic API Documentation Query
1. Set SKIP_GRAPH_BUILD=true in .env for faster startup
2. Run: `python graph_rag_app.py`
3. Enter query: "CreateVariable 関数は何を返しますか？"
4. Verify response contains function return type information
5. Exit with "終了"

#### Scenario 2: Code Analysis Workflow  
1. Run: `python test.py`
2. Verify Tree-sitter parsing completes without errors
3. Check Neo4j graph construction statistics are displayed
4. Confirm function and parameter nodes are created

#### Scenario 3: 3D CAD Integration
1. Navigate to evoship directory: `cd evoship`
2. Examine test file: `python create_test.py` (requires Windows COM interface)
3. **Note**: Full CAD functionality requires Windows environment with EVO.SHIP software

### Expected Timing and Warnings
- **CRITICAL TIMINGS** - Always use these timeout values:
  - Dependency installation: 90+ minutes timeout. **NEVER CANCEL**.
  - Knowledge graph building: 60+ minutes timeout. **NEVER CANCEL**.
  - Tree-sitter parsing: 15+ minutes timeout for large codebases.
  - API queries: 2-5 minutes timeout per query.
- If any operation appears stuck, wait minimum 60 minutes before investigating
- **Building the knowledge graph from scratch can take 30-45 minutes** - this is normal

### Testing Requirements
- **Connection Test**: Always run `python test.py --test-connection` before other operations
- **Database Management**: Use `python test.py --manage-db` to view statistics or clear data
- Neo4j must be running and accessible before starting any Graph RAG operations
- Validate .env configuration with connection test before running main applications

## Common Tasks

### Repository Structure
```
/home/runner/work/imabari3dcad/imabari3dcad/
├── main.py                              # Basic RAG application (LlamaIndex + OpenAI)
├── graph_rag_app.py                     # Advanced Graph RAG with Neo4j + LangChain
├── test.py                              # Neo4j connection testing and Tree-sitter analysis
├── treesitter_neo4j_advanced.py        # Core Tree-sitter Neo4j integration
├── neo4j_query_engine.py               # Neo4j graph query engine
├── test_treesitter_neo4j_integration.py # Integration testing
├── pyproject.toml                       # Project configuration and dependencies
├── requirements.txt                     # Pinned dependency versions
├── .env                                 # Environment variables (create manually)
├── data/api_doc/                        # API documentation files for RAG
├── evoship/                             # 3D CAD model files and scripts
│   ├── create_test.py                   # CAD operation test script
│   ├── EvoModel15.evomdl               # Sample 3D model
│   └── EVOSHIP_HELP_FILES/             # CAD help documentation
└── .github/copilot-instructions.md     # This file
```

### Dependency Categories
- **Core Framework**: LlamaIndex ecosystem (llama-index, agents, embeddings, readers)
- **Graph Database**: Neo4j driver, LlamaIndex Neo4j graph stores
- **AI/ML**: OpenAI API, LangChain, embeddings, language models  
- **Code Analysis**: Tree-sitter, tree-sitter-python
- **Data Processing**: pandas, numpy, networkx, pyvis
- **CAD Integration**: ezdxf (DXF file support), win32com (Windows COM for EVO.SHIP)

### Validation Commands
```bash
# Test environment and connections (run these in order)
python --version                          # Should be 3.10+ (verified: 3.12.3 available)
python -c "print('Basic Python test successful')"  # Basic functionality (2-3 seconds)

# Repository structure validation
ls -la .github/copilot-instructions.md    # Verify instructions file exists
ls -la main.py graph_rag_app.py test.py   # Verify main application files

# Dependency validation (run before installation)
python -c "
import sys
required = ['tree_sitter_python', 'neo4j', 'openai', 'llama_index', 'pandas', 'numpy', 'networkx']
missing = []
for mod in required:
    try: __import__(mod)
    except ImportError: missing.append(mod)
print(f'Missing dependencies: {len(missing)}/{len(required)}')
if missing: print('Run: pip install -e . (90+ minutes)')
"

# Post-installation validation (run after pip install -e .)
python test.py --test-connection          # Test Neo4j (30-60 seconds) - requires Neo4j running
python -c "import tree_sitter_python; print('Tree-sitter OK')"  # Test parsing library

# Full functionality tests (requires all dependencies + services)
python test.py                            # Full Tree-sitter + Neo4j test (15-30 minutes)
python main.py                            # Basic RAG (5-10 minutes setup)
python graph_rag_app.py                   # Full Graph RAG (10-45 minutes setup)
```

### Environment Variables Impact
- `SKIP_GRAPH_BUILD=true`: Use existing Neo4j data, faster startup (2-5 minutes)
- `SKIP_GRAPH_BUILD=false`: Rebuild knowledge graph from documents (30-45 minutes)
- `CLEAR_GRAPH_DATA=true`: Clear Neo4j before building (adds 1-2 minutes)
- `EXTRACTION_LLM_MODEL`: Model for knowledge extraction (gpt-4o recommended)
- `AGENT_LLM_MODEL`: Model for chat agent (gpt-4o recommended)

### Troubleshooting

#### Installation Issues
- **Network timeouts during pip install**: Use `pip install --timeout 1000 --retries 3 -e .`
- **"No module named 'tree_sitter_python'"**: Dependencies not installed, run `pip install -e .`
- **"No module named 'neo4j'"**: Missing core dependencies, ensure full installation completed
- **Partial installation failures**: Delete `.egg-info` directory and retry: `rm -rf *.egg-info && pip install -e .`

#### Runtime Issues  
- **Neo4j connection failed**: 
  - Verify Neo4j is running: `neo4j status`
  - Check .env file contains correct NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
  - Default connection: bolt://localhost:7687, username: neo4j
- **OpenAI API errors**: 
  - Check API key validity at https://platform.openai.com/api-keys
  - Verify OPENAI_API_KEY in .env file
  - Check quota limits and billing status
- **Graph construction hangs**: Normal for large projects, wait 60+ minutes
- **"Database not found" errors**: Neo4j database name case sensitivity, use lowercase names

#### Performance Issues
- **Slow startup**: Set `SKIP_GRAPH_BUILD=true` in .env to use existing data
- **Memory issues**: Knowledge graph construction is memory-intensive, ensure 8GB+ available
- **Long response times**: LLM API calls can take 2-5 minutes per query, normal behavior

### Development Workflow
- **Always** test connection before making changes: `python test.py --test-connection`
- **Always** validate changes with at least one complete scenario from the Validation section
- Use `SKIP_GRAPH_BUILD=true` for faster iteration during development
- Check Neo4j graph statistics after changes: `python test.py --manage-db`
- **Never** interrupt long-running graph construction or dependency installation
- Monitor timing and add 50% buffer for timeout recommendations

### Important Notes
- This project requires significant computational resources and time
- Knowledge graph construction is resource-intensive by design
- Full dependency installation can exceed 1 hour - this is expected
- Neo4j database operations can take 30+ minutes for large datasets
- Always ensure adequate timeout values for all operations
- The project combines multiple complex systems (AI, Graph DB, CAD) - patience required

### Expected Error Conditions
**Before Dependencies Installed:**
- `ModuleNotFoundError: No module named 'tree_sitter_python'` - Run `pip install -e .`
- `ModuleNotFoundError: No module named 'neo4j'` - Run `pip install -e .`
- `ModuleNotFoundError: No module named 'llama_index'` - Run `pip install -e .`

**Without Neo4j Running:**
- `ServiceUnavailable: Failed to establish connection` - Start Neo4j service
- `Neo4jError: Failed to establish connection` - Check Neo4j installation and status

**Without OpenAI API Key:**
- `AuthenticationError: Invalid API key` - Set OPENAI_API_KEY in .env
- `RateLimitError: Rate limit exceeded` - Check API quota and billing

**Normal Long-Running Behaviors (DO NOT INTERRUPT):**
- Dependency installation: 45-90 minutes
- Knowledge graph construction: 30-45 minutes
- Tree-sitter parsing large codebases: 15-30 minutes
- LLM analysis queries: 2-5 minutes each