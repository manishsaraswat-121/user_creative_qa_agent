from langchain.tools import tool
from db.repository import get_creatives_for_user

@tool
def fetch_user_creatives(user_id: str) -> list:
    """Fetch all creatives belonging to the requesting user."""
    creatives = get_creatives_for_user(user_id)
    if not creatives:
        return []
    safe_creatives = []
    for c in creatives:
        safe_creatives.append({
            "creative_text": c.get("creative_text", ""),
            "media_url": c.get("media_url", None)
        })
    return safe_creatives

@tool
def analyze_clarity(creative_text: str) -> str:
    """Analyze clarity and call-to-action strength of a creative."""
    if not creative_text:
        return "No creative text found."
    if "off" in creative_text.lower():
        return "The creative is clear, but adding urgency or a stronger CTA could improve it."
    return "The message could be clearer. Consider simplifying the language and adding a CTA."
