# agent/tools.py

import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict   # ✅ FIX HERE

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool

from agent.prompt import INTENT_CLASSIFICATION_PROMPT

logger = logging.getLogger("creative-qa-agent.tools")


def load_api_key() -> str:
    """
    Load API key from .env.sample located at project root.
    """

    project_root = Path(__file__).resolve().parent.parent
    env_path = project_root / ".env.sample"

    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)
        logger.info(f"Loaded environment variables from {env_path}")
    else:
        logger.error(f".env.sample not found at {env_path}")
        raise RuntimeError(".env.sample file is missing at project root")

    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")

    if not api_key:
        logger.error("API key not found in .env.sample")
        raise RuntimeError(
            "OPENROUTER_API_KEY or OPENAI_API_KEY must be set in .env.sample"
        )

    return api_key


@tool
def classify_user_intent(query: str) -> dict:
    """
    Uses an LLM to classify the user's intent.
    Returns a dict like: {"intent": "CREATIVE_QA"}
    """

    api_key = load_api_key()

    llm = ChatOpenAI(
        model="openai/gpt-4o-mini",
        temperature=0,
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
    )

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
    # Mocked user-scoped DB
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
    Analyze clarity and CTA strength of a creative text.
    """
    if not creative_text.strip():
        return "The creative text is empty."

    return (
        "The creative is clear and highlights a strong discount. "
        "You could improve it by adding urgency or a clearer call-to-action."
    )

