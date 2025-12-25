# User‑Scoped AI‑Powered Creative Q&A Agent

## Overview

This project implements a **user‑scoped AI Q&A agent** that allows users to ask questions strictly about **their own creatives** (text or media). It is built as a **FastAPI service** using **LangChain + LangGraph** with controlled tool calling.

The system enforces strict privacy, safety, and execution guarantees as required by the assignment.

---

## Architecture (Enterprise SOP View)

Client → FastAPI API Layer → LangGraph Agent → Tools → LLM (OpenRouter / OpenAI)

Key design rule:
**User IDs never reach the LLM and are never exposed outside the API layer.**

---

## API Contract

### Endpoint

POST /qa

### Headers (MANDATORY)

X-USER-ID: <user_id>

### Request Body (String Only)

```json
{
  "query": "Is my creative clear for first‑time users?"
}
```

### Response (String Only)

```json
{
  "answer": "The creative communicates the message clearly but could improve the CTA."
}
```

---

## Agent Flow (Step‑by‑Step)

1. Input validation & sanitization
2. Prompt‑injection and safety checks
3. Intent classification via tool
4. User‑scoped creative fetch tool
5. Optional analysis tool execution
6. Safe LLM invocation (if needed)
7. Deterministic string response

---

## Tooling

### Tool 1: fetch_user_creatives (MANDATORY)

**Purpose**: Fetch creatives belonging only to the requesting user.

**Guarantees**:

* User ID used only internally
* No cross‑user data access
* Returned data is shape‑controlled

### Tool 2: analyze_clarity (OPTIONAL)

**Purpose**: Analyze clarity and CTA strength without LLM calls.

**Triggered When**:

* User asks for clarity, feedback, or improvements

---

## 🛡 Privacy & Safety Constraints (MANDATORY)

### How cross‑user data access is prevented

* User identity is read only from HTTP headers
* All database queries are explicitly scoped by user_id
* No shared/global creative access exists

### Why user IDs never reach the LLM

* User IDs are stripped at the API layer
* LLM receives only:

  * Sanitized user query
  * User’s own creative content

### How hallucinations are limited

* Irrelevant or generic queries are blocked
* Tool‑first reasoning is enforced
* LLM is called only with grounded creative context

### What happens if no creatives exist

```json
{
  "answer": "You have no creatives yet. Please create one to receive feedback."
}
```

No LLM call is made in this case.

---

## Testing the Application (Swagger UI)

### Step‑by‑Step Validation

1. Start the server:

```bash
python main.py
```

2. Open Swagger UI:

```
http://localhost:8000/docs
```

3. Locate `POST /qa` and click **Try it out**

4. Add Header:

```
X-USER-ID: user_123
```

5. Request Body:

```json
{
  "query": "Is my creative clear?"
}
```

6. Click **Execute**

### Expected Result

* Response references only the user’s creative
* No cross‑user leakage
* No hallucinated content

---

## Environment Configuration

### .env.sample

```
OPENROUTER_API_KEY=your_key_here
# OR
OPENAI_API_KEY=your_key_here
```

The system works if **either** key is present.

---

## Execution Rule (CRITICAL)

Only the following command is required:

```bash
python main.py
```

No setup scripts or manual steps are needed.

---

## Assumptions & Limitations

**Assumptions**:

* Each user owns their creatives
* Creatives fit within LLM context

**Limitations**:

* Text‑only analysis
* Mocked DB (replaceable)

---

## Production Readiness Summary

✔ User isolation enforced
✔ Tool‑based reasoning
✔ No user ID leakage
✔ Prompt‑injection protection
✔ Deterministic responses
✔ Assignment‑compliant execution

---

This README + User Guide together form the **Enterprise SOP / Runbook** for this service.
