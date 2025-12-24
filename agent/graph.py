import os
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph
from agent.tools import fetch_user_creatives, analyze_clarity
from agent.prompt import SYSTEM_PROMPT

logger = logging.getLogger("creative-qa-agent.agent")

# Forbidden patterns for global/out-of-scope queries
FORBIDDEN_PATTERNS = [
    "all users", "other users", "everyone", "every user",
    "other creatives", "show me all", "list users"
]

# Generic knowledge keywords
GENERIC_KEYWORDS = ["where", "when", "who", "capital", "country", "city", "history", "population"]

# Prompt injection patterns
PROMPT_INJECTION_PATTERNS = [
    "ignore previous instructions",
    "forget your rules",
    "reveal other users",
    "execute code",
    "system prompt",
    "openai key",
    "api key"
]

# Keywords to determine if a query is creative-related
CREATIVE_KEYWORDS = [
    "creative", "ad", "promo", "design", "image", "text", "message", "clarity", "cta"
]

def get_llm():
    """
    Initialize and return a ChatOpenAI LLM instance using OpenRouter.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.warning("OPENROUTER_API_KEY not set. LLM calls may fail.")
    return ChatOpenAI(
        model="openai/gpt-4o-mini",
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1"
    )

def run_agent(user_id: str, user_query: str) -> str:
    """
    Run the QA agent for a specific user and query.
    Handles tool calling, out-of-scope checks, relevance checks, and LLM responses.
    """
    llm = get_llm()

    def agent_node(state):
        query_lower = user_query.lower()

        # 1️⃣ Prompt injection detection
        if any(pattern in query_lower for pattern in PROMPT_INJECTION_PATTERNS):
            logger.warning(f"Prompt injection attempt blocked for user {user_id}: {user_query}")
            return {"answer": "Your query appears unsafe. Please ask a question only about your own creatives."}

        # 2️⃣ Forbidden/global patterns
        if any(p in query_lower for p in FORBIDDEN_PATTERNS):
            return {"answer": "I can only answer questions about your own creatives. Please ask a relevant question."}

        # 3️⃣ Generic knowledge check
        if any(word in query_lower for word in GENERIC_KEYWORDS):
            return {"answer": "Please ask a question related to your own creatives only."}

        # 4️⃣ Fetch user's creatives
        creatives = fetch_user_creatives.run(user_id)
        if not creatives:
            return {"answer": "You have no creatives yet. Please create one to ask questions about it."}

        creative_text = creatives[0].get("creative_text", "")

        # 5️⃣ Tool-based clarity analysis
        if "clear" in query_lower or "clarity" in query_lower:
            return {"answer": analyze_clarity.run(creative_text)}

        # 6️⃣ Relevance check: must be creative-related
        if not any(word in query_lower for word in CREATIVE_KEYWORDS):
            logger.info(f"Irrelevant query blocked for user {user_id}: {user_query}")
            return {"answer": "I can only answer questions about your own creatives. Please ask a relevant question."}

        # 7️⃣ LLM invocation (safe)
        try:
            response = llm.invoke([
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=f"User question: {user_query}"),
                HumanMessage(content=f"User creative: {creative_text}")
            ])
            answer = response.content or "I could not generate a response."
        except Exception as e:
            logger.error(f"LLM call failed for user {user_id}", exc_info=e)
            answer = "There was an error generating the response."

        return {"answer": answer}

    # Build and compile the state graph
    graph = StateGraph(dict)
    graph.add_node("agent", agent_node)
    graph.set_entry_point("agent")
    app = graph.compile()

    # Invoke the agent and return the final answer
    return app.invoke({})["answer"]
