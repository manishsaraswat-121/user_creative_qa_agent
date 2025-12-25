import os
import re
import logging
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph

from agent.tools import (
    fetch_user_creatives,
    analyze_clarity,
    classify_user_intent,
)
from agent.prompt import (
    SYSTEM_PROMPT,
    IRRELEVANT_QUERY_RESPONSE,
    EMPTY_QUERY_RESPONSE,
)

logger = logging.getLogger("creative-qa-agent.agent")


# -------------------------
# Security & Safety Guards
# -------------------------

PROMPT_INJECTION_PATTERNS = [
    "ignore previous instructions",
    "forget your rules",
    "reveal other users",
    "execute code",
    "system prompt",
    "api key",
    "openai key",
]

MAX_QUERY_LENGTH = 500


# -------------------------
# Environment / LLM Setup
# -------------------------

def load_env():
    """
    Load .env.sample explicitly to support Windows & multi-folder layouts.
    """
    project_root = Path(__file__).parent.parent
    env_path = project_root / ".env.sample"

    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        logger.info(f".env.sample loaded from {env_path}")
    else:
        logger.warning(f".env.sample not found at {env_path}")


def get_llm() -> ChatOpenAI:
    """
    Initialize ChatOpenAI using OpenRouter or OpenAI.
    """
    load_env()

    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")

    if not api_key:
        logger.critical("No API key found in environment variables")
        raise ValueError("OPENROUTER_API_KEY or OPENAI_API_KEY is required")

    return ChatOpenAI(
        model="openai/gpt-4o-mini",
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.2,
    )


# -------------------------
# Utilities
# -------------------------

def sanitize_query(query: str) -> str:
    query = query.strip()
    query = re.sub(r"\s+", " ", query)
    return query[:MAX_QUERY_LENGTH]


def is_prompt_injection(query: str) -> bool:
    q = query.lower()
    return any(pattern in q for pattern in PROMPT_INJECTION_PATTERNS)


# -------------------------
# Agent Orchestration
# -------------------------

def run_agent(user_id: str, user_query: str) -> str:
    """
    Main entry point for the Creative QA Agent.
    """
    llm = get_llm()
    query = sanitize_query(user_query)

    def agent_node(state: Dict):
        # 1️⃣ Hard security check (non-negotiable)
        if is_prompt_injection(query):
            logger.warning(f"Prompt injection blocked for user={user_id}")
            return {
                "answer": "Your request appears unsafe. Please ask a question only about your own creatives."
            }

        # 2️⃣ Intent classification (LLM as tool)
        intent_result = classify_user_intent.run(query)
        intent = intent_result.get("intent")

        logger.info(f"Intent detected: {intent}")

        if intent == "EMPTY_OR_INVALID":
            return {"answer": EMPTY_QUERY_RESPONSE}

        if intent == "IRRELEVANT":
            return {"answer": IRRELEVANT_QUERY_RESPONSE}

        # 3️⃣ Fetch user-scoped creatives (never exposed to LLM)
        creatives = fetch_user_creatives.run(user_id)

        if not creatives:
            return {
                "answer": "You do not have any creatives yet. Please create one to receive feedback."
            }

        creative_text = creatives[0].get("creative_text", "").strip()

        if not creative_text:
            return {"answer": "Your creative appears to be empty."}

        # 4️⃣ Tool-based feedback flow
        if intent == "CREATIVE_FEEDBACK":
            return {"answer": analyze_clarity.run(creative_text)}

        # 5️⃣ Creative Q&A via LLM (safe context)
        try:
            response = llm.invoke(
                [
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=f"Creative:\n{creative_text}"),
                    HumanMessage(content=f"User Question:\n{query}"),
                ]
            )
            return {"answer": response.content or "I could not generate a response."}

        except Exception as exc:
            logger.error(
                f"LLM invocation failed for user={user_id}", exc_info=exc
            )
            return {
                "answer": "There was an internal error while generating the response."
            }

    # -------------------------
    # LangGraph Wiring
    # -------------------------

    graph = StateGraph(dict)
    graph.add_node("agent", agent_node)
    graph.set_entry_point("agent")
    app = graph.compile()

    return app.invoke({})["answer"]
