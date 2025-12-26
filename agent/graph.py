# agent/graph.py

import os
import re
import logging
from typing import Dict

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
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

MAX_QUERY_LENGTH = 500
PROMPT_INJECTION_PATTERNS = [
    "ignore previous instructions",
    "reveal system prompt",
    "show other users",
    "api key",
]


def sanitize_query(query: str) -> str:
    query = query.strip()
    query = re.sub(r"\s+", " ", query)
    return query[:MAX_QUERY_LENGTH]


def is_prompt_injection(query: str) -> bool:
    q = query.lower()
    return any(p in q for p in PROMPT_INJECTION_PATTERNS)


def get_llm():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY must be set")

    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,
        openai_api_key=api_key,
    )


def run_agent(user_id: str, user_query: str) -> str:
    """
    Main LangGraph-based agent execution entry point.
    """

    llm = get_llm()
    query = sanitize_query(user_query)

    def agent_node(state: Dict):
        # 1. Security guard
        if is_prompt_injection(query):
            return {
                "answer": "I can only help with questions about your own creatives."
            }

        # 2. Intent classification
        intent_result = classify_user_intent.run(query)
        intent = intent_result.get("intent")

        if intent == "EMPTY_OR_INVALID":
            return {"answer": EMPTY_QUERY_RESPONSE}

        if intent == "IRRELEVANT":
            return {"answer": IRRELEVANT_QUERY_RESPONSE}

        # 3. Fetch user-scoped creatives
        creatives = fetch_user_creatives.run(user_id)

        if not creatives:
            return {
                "answer": "You do not have any creatives yet. Please create one first."
            }

        creative_text = creatives[0].get("creative_text", "").strip()

        if not creative_text:
            return {"answer": "Your creative content appears to be empty."}

        # 4. Tool-based feedback
        if intent == "CREATIVE_FEEDBACK":
            return {"answer": analyze_clarity.run(creative_text)}

        # 5. LLM-based Q&A
        response = llm.invoke(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=f"Creative:\n{creative_text}"),
                HumanMessage(content=f"User Question:\n{query}"),
            ]
        )

        return {
            "answer": response.content or "Unable to generate a response."
        }

    # LangGraph wiring
    graph = StateGraph(dict)
    graph.add_node("agent", agent_node)
    graph.set_entry_point("agent")

    app = graph.compile()
    return app.invoke({})["answer"]
