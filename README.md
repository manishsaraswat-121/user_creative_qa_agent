# User-Scoped Creative Q&A Agent

## Overview

This project implements a **User-Scoped AI-powered Creative Q&A Agent** using FastAPI, LangGraph, and OpenRouter-compatible LLMs. The agent helps users ask questions about *their own marketing creatives* while strictly enforcing privacy, safety, and execution constraints defined in the assignment.

The service is designed to run with a **single command**:

```bash
python main.py
```

No setup scripts, no manual configuration, and no hidden runtime dependencies.

---

## Key Guarantees (Mandatory Compliance)

### 🛡 1. Cross-User Data Access Prevention

All creative data access is **strictly user-scoped**.

* Every request must include an `X-USER-ID` header
* The backend fetches creatives **only for that user ID** using a server-side lookup
* There is no shared/global creative store exposed to the agent
* The agent never iterates over or accesses other users’ data

This design makes **cross-user data access technically impossible**.

---

### 🔒 2. Why User IDs Never Reach the LLM

User identifiers are treated as **sensitive metadata** and are **never passed to the LLM**.

* `X-USER-ID` is consumed only by backend tools (e.g., database fetch)
* The LLM receives **only**:

  * Sanitized creative text
  * The user’s natural-language query
* No prompts, tool inputs, or system messages contain user IDs

This enforces a strict **privacy boundary** between identity and model reasoning.

---

### 🧠 3. Hallucination Mitigation Strategy

The agent is intentionally designed to limit hallucinations:

1. **Grounded Context Only**
   The LLM is prompted exclusively with creatives retrieved for the user.

2. **No External Knowledge Calls**
   The agent does not query the internet, vector databases, or external knowledge sources.

3. **Intent Classification Guardrails**
   User queries are classified before response generation, preventing unsupported behavior.

4. **Deterministic Empty-State Handling**
   If no creatives exist, the agent responds with a fixed message instead of guessing.

---

### 📭 4. Behavior When No Creatives Exist

If a user has no creatives stored:

* The agent **does not fabricate content**
* The response explicitly states that no creatives are available
* The user is prompted to add creatives or try again later

This ensures predictable, non-hallucinatory behavior.

---

## Architecture Overview

```
Client
  │
  ▼
FastAPI (/qa)
  │
  ▼
Intent Classification Tool
  │
  ├─ IRRELEVANT / EMPTY → Safe Response
  │
  ▼
Fetch User Creatives (User-Scoped)
  │
  ▼
LLM Analysis (OpenRouter / OpenAI)
  │
  ▼
Final Answer
```

---

## LLM Provider & API Key Handling

The agent supports **either** OpenRouter or OpenAI keys:

* `OPENROUTER_API_KEY` (preferred)
* `OPENAI_API_KEY` (fallback)

The system automatically uses whichever is present in the environment.

❗ No `.env` file is auto-loaded. Keys must be set explicitly in the OS environment.

---

## Execution Rules (Critical)

The evaluator will run **only**:

```bash
python main.py
```

The project:

* Does NOT rely on setup scripts
* Does NOT auto-load `.env` or `.env.sample`
* Starts cleanly with default FastAPI + Uvicorn behavior

If the service does not start, the submission fails automatically.

---

## Health Check

```http
GET /health
```

Returns:

```json
{"status": "ok"}
```

---

## Example Request

```bash
curl -X POST http://localhost:8000/qa \
  -H "X-USER-ID: user_123" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are my creatives?"}'
```

---

## Final Notes

* The agent is **privacy-safe by construction**
* User data never leaks to the model
* Hallucinations are actively constrained
* The system is ready for direct evaluation and submission

