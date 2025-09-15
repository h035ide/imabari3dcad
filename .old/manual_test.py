import os
import sys
import logging

# --- [Path Setup] ---
# Ensure the project root is in the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- [End Path Setup] ---

from code_generator.agent import create_code_generation_agent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def run_test_query(query: str):
    """
    Initializes the agent and runs a single test query.
    """
    logger = logging.getLogger(__name__)

    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable not set. Cannot run test.")
        return

    logger.info("--- Creating Agent ---")
    agent_executor = create_code_generation_agent()

    if not agent_executor:
        logger.error("Failed to create agent.")
        return

    logger.info(f"--- Invoking Agent with query: '{query}' ---")
    response = agent_executor.invoke({"input": query, "chat_history": []})

    print("\n--- Agent Response ---")
    print(response.get("output", "No output found."))
    print("--- End of Response ---")

if __name__ == "__main__":
    test_query = "一辺が50mmの正方形のキューブを作成してください"
    run_test_query(test_query)
