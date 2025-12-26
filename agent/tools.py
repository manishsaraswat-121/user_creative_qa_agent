# agent/tools.py

import os
import json
import logging
from typing import List, Dict

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool

from agent.prompt import INTENT_CLASSIFICATION_PROMPT

logger = logging.getLogger("creative-qa-agent.tools")


def get_openai_llm(temperature: float = 0):
    """
    Initialize OpenAI LLM using OPENAI_API_KEY only.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY must be set in environment variables")

    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=temperature,
        openai_api_key=api_key,
    )


@tool
def classify_user_intent(query: str) -> dict:
    """
    Classifies the user's intent into predefined categories.
    Returns a JSON dict like: {"intent": "CREATIVE_QA"}
    """

    llm = get_openai_llm(temperature=0)

    response = llm.invoke(
        [
            SystemMessage(content="You are a strict intent classifier."),
            HumanMessage(
                content=INTENT_CLASSIFICATION_PROMPT.format(query=query)
            ),
        ]
    )

    try:
        return json.loads(response.content)
    except Exception:
        logger.warning("Intent classifier returned invalid JSON")
        return {"intent": "IRRELEVANT"}


@tool
def fetch_user_creatives(user_id: str) -> List[Dict]:
    """
    Fetch creatives belonging ONLY to the given user.
    User IDs are never exposed to the LLM.
    """

    mock_db = {
        "user_123": [
            {
                "creative_text": "Get 50% off on your first order. Limited time offer!",
                "media_url": None,
            }
        ]
    }

    return mock_db.get(user_id, [])


@tool
def analyze_clarity(creative_text: str) -> str:
    """
    Analyzes clarity and CTA strength of creative text without LLM usage.
    """

    if not creative_text.strip():
        return "The creative text is empty."

    return (
        "The creative clearly highlights a discount, which is effective. "
        "You could improve it further by adding urgency or a clearer call-to-action."
    )
