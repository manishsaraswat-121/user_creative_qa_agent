from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Extra
from agent.graph import run_agent
import logging
import re

logger = logging.getLogger("creative-qa-agent.api")
router = APIRouter()

MAX_QUERY_LENGTH = 300  # Limit query length

class QARequest(BaseModel):
    query: str
    class Config:
        extra = Extra.forbid

class QAResponse(BaseModel):
    answer: str

def sanitize_input(query: str) -> str:
    """
    Sanitize user input to prevent prompt injection and unsafe characters.
    """
    # Remove extra whitespace
    query = query.strip()
    # Remove control characters
    query = re.sub(r"[\x00-\x1f\x7f]", "", query)
    # Escape special characters (optional)
    query = re.sub(r"[<>]", "", query)
    return query

@router.post("/qa", response_model=QAResponse)
def qa_endpoint(payload: QARequest, x_user_id: str = Header(..., alias="X-USER-ID")):
    query = sanitize_input(payload.query)
    
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    if len(query) > MAX_QUERY_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Query too long. Maximum allowed length is {MAX_QUERY_LENGTH} characters."
        )

    logger.info("Received QA request", extra={"user_id": x_user_id, "query": query})

    try:
        answer = run_agent(user_id=x_user_id, user_query=query)
    except Exception as e:
        logger.error("Agent execution failed", exc_info=e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

    logger.info("QA response ready", extra={"user_id": x_user_id})
    return {"answer": answer}
