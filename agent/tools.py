import os
import json
import logging
from typing import List, Dict

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool

from agent.prompt import INTENT_CLASSIFICATION_PROMPT

logger = logging.getLogger("creative-qa-agent.tools")


def get_api_key_and_base() -> Dict[str, str]:
    """
    Returns a dictionary with api_key and openai_api_base (if applicable).
    Prioritizes OpenRouter over OpenAI. Raises RuntimeError if neither is set.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key:
        return {"api_key": api_key, "api_base": "https://openrouter.ai/api/v1"}
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return {"api_key": api_key, "api_base": None}
    logger.critical("Neither OPENROUTER_API_KEY nor OPENAI_API_KEY is set")
    raise RuntimeError(
        "You must set either OPENROUTER_API_KEY or OPENAI_API_KEY in environment."
    )


@tool
def classify_user_intent(query: str) -> dict:
    """
    Classifies the user's query intent into one of:
    CREATIVE_QA, CREATIVE_FEEDBACK, IRRELEVANT, EMPTY_OR_INVALID.
    Returns a dictionary: {"intent": "CREATIVE_QA"}.
    """
    keys = get_api_key_and_base()
    llm = ChatOpenAI(
        model="openai/gpt-4o-mini",
        temperature=0,
        openai_api_key=keys["api_key"],
        openai_api_base=keys["api_base"],
    )

    response = llm.invoke(
        [
            SystemMessage(content="You are a strict intent classifier."),
            HumanMessage(content=INTENT_CLASSIFICATION_PROMPT.format(query=query)),
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
    Fetches creatives belonging only to the given user.
    Returns a list of dictionaries: [{"creative_text": ..., "media_url": ...}].
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
    Analyzes the clarity and call-to-action (CTA) of the creative text.
    Returns a string feedback.
    """
    if not creative_text.strip():
        return "The creative text is empty."
    return (
        "The creative is clear and highlights a strong discount. "
        "You could improve it by adding urgency or a clearer call-to-action."
    )
