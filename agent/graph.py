import os
import logging
import re
from typing import Dict

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph

from agent.tools import fetch_user_creatives, analyze_clarity, classify_user_intent
from agent.prompt import SYSTEM_PROMPT, IRRELEVANT_QUERY_RESPONSE, EMPTY_QUERY_RESPONSE

logger = logging.getLogger("creative-qa-agent.agent")

MAX_QUERY_LENGTH = 500
PROMPT_INJECTION_PATTERNS = [
    "ignore previous instructions",
    "forget your rules",
    "reveal other users",
    "execute code",
    "system prompt",
    "api key",
    "openai key",
]

def sanitize_query(query: str) -> str:
    """
    Sanitizes user input by stripping whitespace and truncating to max length.
    """
    query = query.strip()
    query = re.sub(r"\s+", " ", query)
    return query[:MAX_QUERY_LENGTH]

def is_prompt_injection(query: str) -> bool:
    """
    Checks if query contains known prompt injection patterns.
    """
    q = query.lower()
    return any(pattern in q for pattern in PROMPT_INJECTION_PATTERNS)

def get_llm() -> ChatOpenAI:
    """
    Initializes ChatOpenAI LLM using either OpenRouter or OpenAI API key.
    OpenRouter is preferred if both are present.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    api_base = "https://openrouter.ai/api/v1" if api_key else None

    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")
        api_base = None

    if not api_key:
        raise RuntimeError(
            "Either OPENROUTER_API_KEY or OPENAI_API_KEY must be set in environment"
        )

    return ChatOpenAI(
        model="openai/gpt-4o-mini",
        openai_api_key=api_key,
        openai_api_base=api_base,
        temperature=0.2,
    )

def run_agent(user_id: str, user_query: str) -> str:
    """
    Main entry point for the Creative QA Agent.
    Accepts a user ID and a string query.
    Returns a single string answer.
    """

    query = sanitize_query(user_query)

    def agent_node(state: Dict):
        # 1️⃣ Prompt injection protection
        if is_prompt_injection(query):
            logger.warning(f"Prompt injection blocked for user={user_id}")
            return {"answer": "Your request appears unsafe. Please ask a question only about your own creatives."}

        # 2️⃣ Intent classification
        intent_result = classify_user_intent.run(query)
        intent = intent_result.get("intent")
        logger.info(f"Intent detected: {intent}")

        if intent == "EMPTY_OR_INVALID":
            return {"answer": EMPTY_QUERY_RESPONSE}

        if intent == "IRRELEVANT":
            return {"answer": IRRELEVANT_QUERY_RESPONSE}

        # 3️⃣ Fetch user-scoped creatives
        creatives = fetch_user_creatives.run(user_id)
        if not creatives:
            return {"answer": "You do not have any creatives yet. Please create one to receive feedback."}

        creative_text = creatives[0].get("creative_text", "").strip()
        if not creative_text:
            return {"answer": "Your creative appears to be empty."}

        # 4️⃣ Tool-based feedback
        if intent == "CREATIVE_FEEDBACK":
            return {"answer": analyze_clarity.run(creative_text)}

        # 5️⃣ LLM-based Q&A (safe context)
        llm = get_llm()
        try:
            response = llm.invoke([
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=f"Creative:\n{creative_text}"),
                HumanMessage(content=f"User Question:\n{query}"),
            ])
            return {"answer": response.content or "I could not generate a response."}
        except Exception as exc:
            logger.error(f"LLM invocation failed for user={user_id}", exc_info=exc)
            return {"answer": "There was an internal error while generating the response."}

    # -------------------------
    # LangGraph orchestration
    # -------------------------
    graph = StateGraph(dict)
    graph.add_node("agent", agent_node)
    graph.set_entry_point("agent")
    app = graph.compile()

    return app.invoke({})["answer"]
