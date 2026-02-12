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

**Active Endpoint:**
- `POST /api/chat` - Main chat endpoint (receives text, returns text)

**Inactive Endpoints:**
- `GET /api/part/{part_id}` - Part details (exists but not used)
- `GET /health` - Health check

**Files:**
- `app.py` - FastAPI server
- `routes/chat.py` - Chat endpoint
- `routes/parts.py` - Parts endpoint (disabled in frontend)
- `services/chat_service.py` - Search logic
- `services/database.py` - Database connection

---

## Database

**Type:** PostgreSQL
**Host:** localhost:5432
**Database:** `partselect_db`
**User:** postgres

**Tables:**
- `parts` - 92 parts (refrigerator/dishwasher)
- `models` - 1,845 appliance models
- `part_models` - 2,735 compatibility mappings

**Connection:** Configured via `.env` file

---

## Data Flow

1. User types message in frontend
2. Frontend sends `POST /api/chat` with message text
3. Backend searches PostgreSQL database
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
