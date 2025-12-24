import os
import logging
from fastapi import FastAPI
from api.routes import router
from contextlib import asynccontextmanager
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("creative-qa-agent")

# Lifespan handler replaces deprecated on_event
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    if not os.getenv("OPENROUTER_API_KEY"):
        logger.warning("OPENROUTER_API_KEY not set. LLM calls will fail.")
    logger.info("Application startup complete.")
    yield
    # Shutdown logic
    logger.info("Application shutdown complete.")

app = FastAPI(title="User Creative Q&A Agent", lifespan=lifespan)
app.include_router(router)

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
