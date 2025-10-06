"""
AI Agent System Information API
================================

This FastAPI application exposes an endpoint that returns a structured
summary of best‑practices and reference information for building AI
agent systems.  The content has been gathered from up‑to‑date,
publicly available sources dated October 2025 and distilled into a
concise, machine‑readable format.  Each section includes citations
that point back to the original source lines (rendered as tether IDs)
so that you can trace the provenance of the information.

The endpoint `/ai_agent_info` returns a JSON document with the
following top‑level keys:

* ``architecture`` – explains the core layers of an AI agent (perception,
  memory, reasoning, action and feedback), citing Designveloper’s
  overview【727157579330473†L245-L325】.
* ``agent_types`` – describes common agent architectures (reactive,
  deliberative, hybrid, multi‑agent and LLM‑powered) and when to use
  them【727157579330473†L348-L447】【727157579330473†L450-L471】.
* ``design_steps`` – enumerates a step‑by‑step process for designing
  an agent system, adapted from Designveloper’s guide: define the
  use‑case, choose the agent type, design core components, select
  frameworks/tools, build and integrate modules, and train, test and
  optimize【727157579330473†L484-L573】.
* ``best_practices`` – lists recommended design principles such as
  modularity, continuous learning via feedback loops, monitoring and
  evaluation metrics, and keeping a human in the loop for critical
  decisions【727157579330473†L575-L626】.
* ``challenges`` – outlines common challenges (data quality issues,
  latency and scaling, security & privacy concerns, and ethical
  decision‑making) that must be addressed when deploying agents
  【727157579330473†L628-L674】.
* ``frameworks`` – summarizes the features of popular open‑source
  frameworks for building AI agents, including LangChain and AutoGen
  (with their respective strengths and weaknesses【416798405249974†L134-L170】),
  CrewAI (standalone multi‑agent framework【661424786708206†L63-L76】 and its
  concept of crews and flows【661424786708206†L170-L200】), and Microsoft
  Agent Framework (which unifies Semantic Kernel and AutoGen into an
  enterprise‑ready platform【362865409205602†L170-L233】).
* ``use_cases`` – highlights real‑world applications such as
  conversational AI and customer service【727157579330473†L684-L691】, robotics
  and autonomous vehicles【727157579330473†L693-L699】, healthcare &
  diagnostics【727157579330473†L702-L709】, financial trading & fraud
  detection【727157579330473†L711-L717】, and other enterprise use cases
  (customer support automation, marketing & sales co‑pilots, finance
  optimization engines, supply chain coordination, and healthcare
  assistants【539663969109775†L232-L293】).

To run the API locally use::

    pip install fastapi uvicorn
    uvicorn ai_agent_info_api:app --reload

Then open ``http://127.0.0.1:8000/ai_agent_info`` in a browser or
issue a ``GET`` request using ``curl`` or any HTTP client.

"""

from fastapi import FastAPI


app = FastAPI(title="AI Agent System Information API")


@app.get("/ai_agent_info")
async def get_ai_agent_info():
    """Return a structured summary of AI agent system design guidance.

    Each field contains human‑readable text along with citations to
    the original sources.  The response format is JSON so it can be
    consumed directly by tools or other services.
    """
    return {
        "architecture": {
            "description": (
                "A well‑designed AI agent follows a perception–reasoning–action\n"
                "loop with optional feedback.  The *perception* layer ingests\n"
                "raw input (text, sensor data or API calls) and transforms it\n"
                "into a structured format【727157579330473†L245-L267】.  The *memory*\n"
                "layer stores short‑term context (session state) and long‑term\n"
                "knowledge to enable more personal, context‑aware behaviour\n"
                "【727157579330473†L271-L281】.  *Reasoning & decision‑making* uses\n"
                "rules, search algorithms or LLMs to select appropriate actions\n"
                "【727157579330473†L295-L305】.  *Action & execution* executes those\n"
                "decisions by calling APIs, running code or actuating hardware\n"
                "【727157579330473†L308-L316】.  Finally, a *feedback loop* logs\n"
                "results and updates the model via supervised learning,\n"
                "reinforcement learning or self‑critique【727157579330473†L318-L333】."
            ),
            "citations": [
                "【727157579330473†L245-L333】"
            ],
        },
        "agent_types": {
            "reactive": "Reactive agents respond immediately to input without\n"
                        "memory or planning.  They are simple and fast but\n"
                        "cannot handle complex reasoning【727157579330473†L348-L370】.",
            "deliberative": "Deliberative agents build internal models of the\n"
                            "world and plan before acting; they are useful for\n"
                            "complex tasks but require more compute【727157579330473†L375-L397】.",
            "hybrid": "Hybrid agents combine reactive speed with deliberative\n"
                       "planning【727157579330473†L399-L416】.",
            "multi_agent": "Multi‑agent systems (MAS) coordinate multiple\n"
                           "agents either centrally or decentralised to solve\n"
                           "large‑scale or distributed problems【727157579330473†L418-L447】.",
            "llm_agents": "LLM‑powered agents leverage large language models to\n"
                           "interpret natural language, use tools and memory,\n"
                           "and adapt dynamically【727157579330473†L450-L471】.",
            "citations": [
                "【727157579330473†L348-L447】",
                "【727157579330473†L450-L471】",
            ],
        },
        "design_steps": [
            {
                "step": 1,
                "title": "Define the use case",
                "details": "Identify the business problem or goal before\n"
                           "designing an agent.  Clear requirements prevent\n"
                           "over‑engineering and ensure alignment with\n"
                           "stakeholders【727157579330473†L484-L497】."
            },
            {
                "step": 2,
                "title": "Choose the agent type",
                "details": "Select an appropriate agent architecture (reactive,\n"
                           "goal‑based, learning or hybrid) based on the\n"
                           "problem’s complexity and the need for planning or\n"
                           "learning【727157579330473†L498-L507】."
            },
            {
                "step": 3,
                "title": "Design the core components",
                "details": "Add perception, reasoning, memory and action modules\n"
                           "to your architecture.  Clarify how data flows\n"
                           "between components to achieve the goal【727157579330473†L510-L527】."
            },
            {
                "step": 4,
                "title": "Select frameworks and tools",
                "details": "Choose libraries or SDKs (e.g., LangChain, AutoGen,\n"
                           "CrewAI, Ray) that provide the abstractions and\n"
                           "integrations needed for your project【727157579330473†L532-L548】."
            },
            {
                "step": 5,
                "title": "Build and integrate modules",
                "details": "Develop perception, reasoning and action modules\n"
                           "and illustrate their connections so that\n"
                           "stakeholders understand the data flow【727157579330473†L551-L562】."
            },
            {
                "step": 6,
                "title": "Train, test and optimize",
                "details": "Use simulation environments, measure metrics\n"
                           "(accuracy, latency, completion rate) and iterate\n"
                           "through training and fine‑tuning to improve\n"
                           "performance【727157579330473†L564-L573】."
            }
        ],
        "best_practices": {
            "modular_design": "Design agents with modular components so you\n"
                              "can add or remove perception, reasoning or\n"
                              "memory modules without rewriting the entire\n"
                              "system【727157579330473†L575-L592】.",
            "continuous_learning": "Implement feedback loops to allow\n"
                                    "agents to adapt based on past actions\n"
                                    "and outcomes【727157579330473†L594-L602】.",
            "monitoring_metrics": "Define metrics (e.g., accuracy, response\n"
                                  "time, user satisfaction) and set up\n"
                                  "dashboards or logging to track agent\n"
                                  "performance【727157579330473†L604-L614】.",
            "human_in_loop": "For high‑stakes decisions, keep a human\n"
                             "reviewer in the loop to validate outputs and\n"
                             "maintain user trust【727157579330473†L618-L626】.",
            "citations": [
                "【727157579330473†L575-L626】"
            ],
        },
        "challenges": {
            "data_quality": "Poor or biased data leads to inaccurate or\n"
                           "harmful outputs.  Agents need robust data\n"
                           "pipelines and verification mechanisms to ensure\n"
                           "input quality【727157579330473†L634-L642】.",
            "latency_scaling": "Large models or complex workflows may\n"
                               "introduce latency or scaling issues; use\n"
                               "parallel processing frameworks and scalable\n"
                               "infrastructure【727157579330473†L644-L652】.",
            "security_privacy": "Agents can expose sensitive data if they\n"
                                "lack proper encryption, access control or\n"
                                "prompt‑injection protection【727157579330473†L654-L663】.",
            "ethical_decision_making": "Agents may face ethical dilemmas\n"
                                      "(e.g., autonomous vehicles in crash\n"
                                      "situations).  Build in ethical frameworks,\n"
                                      "explainable reasoning and bias detection\n"
                                      "【727157579330473†L666-L672】.",
            "citations": [
                "【727157579330473†L634-L674】"
            ],
        },
        "frameworks": {
            "langchain": {
                "description": "LangChain is a modular framework that provides\n"
                               "wrappers for LLMs, prompt templates, memory\n"
                               "modules, tool integration and chains.  It\n"
                               "emphasizes composability and has a rich set\n"
                               "of integrations for data sources and models\n"
                               "【416798405249974†L134-L170】.",
                "strengths": "Large ecosystem of integrations, strong\n"
                            "community support, and production‑oriented\n"
                            "tooling such as LangSmith and LangServe\n"
                            "【416798405249974†L134-L170】.",
                "weaknesses": "Primarily geared toward single‑agent pipelines;\n"
                              "complex tasks may require additional add‑ons\n"
                              "like LangGraph and may introduce overhead\n"
                              "【416798405249974†L213-L220】."
            },
            "autogen": {
                "description": "AutoGen is a developer‑focused framework from\n"
                               "Microsoft for orchestrating multiple LLM agents\n"
                               "using an event‑driven architecture.  It supports\n"
                               "asynchronous message passing, agent roles and\n"
                               "extension APIs【416798405249974†L134-L154】.",
                "strengths": "Built‑in multi‑agent orchestration,\n"
                            "extensibility via the Extensions API, and\n"
                            "observability features such as message tracing\n"
                            "【416798405249974†L134-L154】.",
                "weaknesses": "Smaller integration ecosystem compared to\n"
                              "LangChain and a steeper learning curve due to\n"
                              "its code‑centric approach【416798405249974†L204-L218】."
            },
            "crewai": {
                "description": "CrewAI is an open‑source Python framework that\n"
                               "orchestrates teams of autonomous agents (\"crews\")\n"
                               "and event‑driven workflows (\"flows\") for complex\n"
                               "tasks.  It offers high performance and low‑level\n"
                               "customization while remaining independent of\n"
                               "LangChain【661424786708206†L63-L76】.",
                "key_features": "Crews enable role‑based collaboration with\n"
                                "natural decision‑making and task delegation,\n"
                                "while flows provide fine‑grained control, state\n"
                                "management and conditional branching.  The\n"
                                "combination allows you to balance autonomy\n"
                                "with precise control【661424786708206†L170-L200】.",
                "strengths": "Standalone, high‑performance design; flexible\n"
                            "customization; suitable for both simple and\n"
                            "enterprise‑grade use cases; backed by a growing\n"
                            "community【661424786708206†L137-L147】.",
                "weaknesses": "Requires Python ≥3.10 and uses its own project\n"
                              "layout and CLI; ecosystem is newer than\n"
                              "LangChain/AutoGen (observed from community\n"
                              "feedback)."
            },
            "microsoft_agent_framework": {
                "description": "Microsoft Agent Framework (MAF) unifies the\n"
                               "enterprise‑ready Semantic Kernel with the\n"
                               "experimental multi‑agent orchestration from\n"
                               "AutoGen into one open‑source SDK and runtime\n"
                               "【362865409205602†L170-L233】.",
                "pillars": "MAF emphasizes open standards and\n"
                           "interoperability (MCP, A2A and OpenAPI), a\n"
                           "pipeline from research to production, community\n"
                           "extensibility and enterprise readiness with\n"
                           "observability and security features【362865409205602†L212-L226】.",
                "features": "Supports agent orchestration and workflow\n"
                           "orchestration, offers connectors to multiple\n"
                           "memory stores, runs across clouds, and uses VS\n"
                           "Code tooling for development【362865409205602†L212-L246】.",
            },
            "citations": [
                "【416798405249974†L134-L170】",
                "【416798405249974†L204-L220】",
                "【661424786708206†L63-L76】",
                "【661424786708206†L170-L200】",
                "【362865409205602†L170-L233】",
                "【362865409205602†L212-L226】"
            ],
        },
        "use_cases": {
            "conversational_ai": "Chatbots and virtual assistants that use NLP\n"
                                "and LLMs to answer questions, handle customer\n"
                                "support 24/7, and reduce call centre costs\n"
                                "【727157579330473†L684-L691】.",
            "robotics_autonomy": "Physical agents such as self‑driving cars\n"
                                "and warehouse robots combine sensors,\n"
                                "planning algorithms and actuators to perform\n"
                                "dangerous or repetitive tasks【727157579330473†L693-L699】.",
            "healthcare": "Agents assist clinicians by analysing medical\n"
                         "records, imaging and lab data to suggest diagnoses\n"
                         "and treatments【727157579330473†L702-L709】.",
            "finance": "Trading bots and fraud detectors analyse real‑time\n"
                      "financial data, automate trades and flag suspicious\n"
                      "activity【727157579330473†L711-L717】.",
            "enterprise": "Use cases include customer support automation,\n"
                          "marketing and sales co‑pilots, portfolio\n"
                          "optimisation, supply chain coordination and\n"
                          "healthcare assistants【539663969109775†L232-L293】.",
            "citations": [
                "【727157579330473†L684-L717】",
                "【539663969109775†L232-L293】"
            ],
        }
    }
