# Mocked DB
USER_CREATIVES = {
    "user_123": [
        {"creative_text": "Your creative is a 50% promo.", "media_url": None}
    ],
    "user_456": [
        {"creative_text": "Another user creative.", "media_url": None}
    ]
}

def get_creatives_for_user(user_id: str) -> list:
    """Return list of creatives for the given user ID."""
    return USER_CREATIVES.get(user_id, [])
