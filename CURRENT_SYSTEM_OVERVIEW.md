# Current System Overview

**Simple text-based chat system for PartSelect parts search**

---

## System Architecture

```
User → Frontend (React) → Backend (FastAPI) → PostgreSQL Database
                             ↓
                      Text Response Only
```

---

## Frontend (Port 3000)

**Location:** `/frontend`
**Tech:** React
**URL:** http://localhost:3000

**Features:**
- Text input field
- Text output display
- Simple chat interface
- **No cards, no images** - pure text conversation

**Files:**
- `src/App.js` - Main app
- `src/components/ChatWindow.js` - Chat interface (cards disabled)
- `src/api/api.js` - Backend API calls

---

## Backend (Port 8000)

**Location:** `/backend`
**Tech:** FastAPI + Python
**URL:** http://localhost:8000
**Docs:** http://localhost:8000/docs

**Active Endpoints:**
- `POST /api/chat` - Main chat endpoint (AI agent-powered)
- `GET /health` - Health check

**Files:**
- `app.py` - FastAPI server
- `routes/chat.py` - Chat endpoint with LangGraph agent
- `routes/health.py` - Health check endpoint
- `services/chat_service.py` - Legacy search logic
- `services/database.py` - Database connection
- `services/tool_call_logger.py` - Session logging
- `agent/agent_config.py` - Agent configuration
- `tools/sql_search_tool.py` - SQL database queries
- `tools/vector_search_tool.py` - Vector similarity search

---

## Database

**Type:** PostgreSQL
**Host:** localhost:5432
**Database:** `partselect_db`
**User:** postgres

**Tables:**
- `parts` - 92 parts (refrigerator/dishwasher only)
- `models` - 1,845 appliance models
- `part_model_mapping` - 2,735 compatibility mappings

**Connection:** Configured via `.env` file

---

## Data Flow

1. User types message in frontend
2. Frontend sends `POST /api/chat` with message and conversation history
3. Backend LangGraph agent processes request:
   - Analyzes user query
   - Calls appropriate tools (SQL or Vector search)
   - Combines information from multiple sources
   - Generates natural language response
4. Agent response logged to session file
5. Frontend displays text response
4. Backend returns text response (may include product data in metadata)
5. Frontend displays **only text** (ignores product metadata)

---

## Current State

✅ **Text-only mode enabled**
❌ **Product cards disabled**
❌ **Part ID endpoint not used**
✅ **All data flows through /api/chat only**

---

## Run Commands

**Backend:**
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python app.py
```

**Frontend:**
```bash
cd frontend
npm start
```

**Database:**
- Ensure PostgreSQL is running on localhost:5432
- Database name: `partselect_db`
