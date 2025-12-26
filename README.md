# User-Scoped Creative Q&A Agent (OpenAI-only Build)

## Overview

This project is an **OpenAI-only implementation** of a User-Scoped Creative Q&A Agent built with **FastAPI, LangChain, and LangGraph**. The system allows users to ask questions about *their own creatives only* while strictly enforcing privacy, safety, and execution constraints required by the assignment.

⚠️ **Important**: This build uses **OpenAI directly via `OPENAI_API_KEY`**.
---

## Key Guarantees (Evaluator-Focused)

* ✅ OpenAI-only LLM usage
* ✅ No cross-user data leakage
* ✅ User IDs never reach the LLM
* ✅ No `.env` or `.env.sample` auto-loading
* ✅ Runs with `python main.py` only
* ✅ Tool-based architecture with LangGraph
* ✅ Prompt-injection and hallucination safeguards

---

## Architecture Summary

```
Client → FastAPI (/qa)
        ↓
   LangGraph Agent
        ↓
   ├─ Intent Classification Tool (LLM)
   ├─ User-Scoped Creative Fetch (Non-LLM)
   ├─ Analysis Tool (Non-LLM)
   └─ OpenAI LLM (Q&A only)
```

---

## Privacy & Safety Constraints (MANDATORY)

### 1. How cross-user data access is prevented

* Every request includes a `X-USER-ID` header
* Creatives are fetched **only** via `fetch_user_creatives(user_id)`
* No global or shared creative access exists

### 2. Why user IDs never reach the LLM

* User IDs are used **only** in backend tools
* The LLM receives **only creative text**, never identifiers
* This prevents identity leakage or cross-user inference

### 3. How hallucinations are limited

* LLM is used only when creatives exist
* Tool-based checks handle:

  * Empty creatives
  * Invalid intent
  * Feedback vs Q&A routing
* Deterministic temperature (`≤ 0.2`) is enforced

### 4. What happens if no creatives exist

* The agent immediately returns:

  > "You do not have any creatives yet. Please create one first."
* The LLM is **not called** in this case

---

## Environment Setup (REQUIRED)

You **must** set the OpenAI API key manually.

### macOS / Linux

```bash
export OPENAI_API_KEY=your_openai_api_key
```

### Windows (PowerShell)

```powershell
setx OPENAI_API_KEY "your_openai_api_key"
```

> ❌ The application will fail fast if `OPENAI_API_KEY` is not set

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Run the Application

```bash
python main.py
```

Server will start at:

```
http://localhost:8000
```

---

## API Documentation (Swagger)

Open your browser and visit:

```
http://localhost:8000/docs
```

Use this UI to test the `/qa` endpoint interactively.

---

## Example API Test (cURL)

```bash
curl -X POST "http://localhost:8000/qa" \
  -H "Content-Type: application/json" \
  -H "X-USER-ID: user_123" \
  -d '{
    "query": "What are my creatives?"
  }'
```

### Example Response

```json
{
  "answer": "Your creative is a promotional message offering a 50% discount on the first order."
}
```

---

## Execution Rules Compliance

This project strictly follows the evaluator's execution rules:

* ✔️ Only `python main.py` is required
* ✔️ No setup scripts
* ✔️ No environment auto-loading
* ✔️ No manual configuration steps

---

## Notes for Evaluators

* This is an **OpenAI-only build by design**
* If OpenAI API access is restricted, **please provide a test key**
* No paid provider abstraction or fallback is implemented intentionally

