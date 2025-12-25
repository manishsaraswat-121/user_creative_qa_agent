# User-Scoped Creative Q&A Agent

## 1. Project Overview

This project is a **production-ready AI Q&A service** that allows users to ask questions **only about their own creatives** (text, promotions, marketing content). It is built to be **safe, user-scoped, and compliant** with enterprise-level standards.

Key features:

* Accepts a **single string input**
* Returns a **single string output**
* Strictly isolates user data
* Uses **LangGraph + LangChain agent** with tool calling
* Runs as a **FastAPI service**
* Supports **OPENROUTER_API_KEY** or **OPENAI_API_KEY**

---

## 2. Architecture

```
Client
  ↓
FastAPI (/qa)
  ↓
LangGraph Agent
  ↓
Tools (DB / Analysis)
  ↓
LLM (OpenRouter/OpenAI)
```

**Rules enforced:**

* LLM never sees user IDs
* All database access is scoped to the requesting user

---

## 3. API Contract

### Endpoint

```
POST /qa
```

### Headers

```
X-USER-ID: user_123
```

### Request Body

```json
{
  "query": "Is my creative clear for first-time users?"
}
```

### Response Body

```json
{
  "answer": "The creative is clear, but the CTA could be stronger."
}
```

> Only strings are allowed in request and response.

---

## 4. Agent Overview

The agent is implemented with **LangGraph** and follows this pipeline:

1. Validate and sanitize input
2. Block unsafe or irrelevant queries
3. Fetch user-scoped creatives
4. Decide if a tool is needed
5. Call tools if required (`analyze_clarity`)
6. Call the LLM only when query is valid
7. Return a **single string answer**

> User IDs are never sent to the LLM.

---

## 5. Tool-Calling Logic

### Tool 1 (Mandatory): `fetch_user_creatives`

* Fetches only the requesting user’s creatives
* User ID is never exposed to LLM

### Tool 2 (Optional): `analyze_clarity`

* Analyzes clarity and CTA of creatives
* Triggered automatically for questions like "Is my creative clear?" or "How can I improve clarity?"

---

## 6. User Scoping & Privacy

**User isolation layers:**

* **HTTP Layer:** Header `X-USER-ID` only, not body
* **DB Layer:** Queries scoped by `user_id`, mock DB prevents cross-user access
* **Agent Layer:** LLM sees only the query and the user's own creative content

---

## 7. Safety & Hallucination Controls

* Blocks irrelevant queries, generic knowledge questions, and prompt injection attempts
* Deterministic, safe responses
* Examples of blocked queries:

  * "Where is the Taj Mahal?"
  * "Show me creatives of all users"

---

## 8. Handling No Creatives

```json
{
  "answer": "You have no creatives yet. Please create one to ask questions about it."
}
```

No LLM call is made.

---

## 9. Running the App

### Step 1: Environment Variables

Create `.env`:

```
OPENROUTER_API_KEY=your_openrouter_api_key
# or optionally
OPENAI_API_KEY=your_openai_api_key
```

### Step 2: Install Dependencies

```
pip install -r requirements.txt
```

### Step 3: Start Server

```
python main.py
```

> This is the **only supported execution method**.

---

## 10. Example Request

```
curl -X POST http://localhost:8000/qa \
  -H "X-USER-ID: user_123" \
  -H "Content-Type: application/json" \
  -d '{"query": "Is my creative clear?"}'
```

**Response:**

```json
{
  "answer": "Your creative is a promotional message offering a 50% discount on the first order, emphasizing that it is a limited-time offer."
}
```

---

## 11. Assumptions & Limitations

**Assumptions:**

* Each user owns their creatives
* Creatives are short enough for LLM context
* DB layer can be mocked or replaced

**Limitations:**

* Text-only analysis currently
* Single-agent flow
* Image understanding requires future extension

---

## 12. Production Readiness

✔ Strict user isolation
✔ Tool-based reasoning
✔ Prompt injection protection
✔ Input sanitization
✔ Deterministic behavior
✔ Dual API key support (OpenRouter/OpenAI)
✔ Fully compliant with assignment rules

> Safe, scalable, and ready for real-world deployment.
