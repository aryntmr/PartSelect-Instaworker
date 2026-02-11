# PartSelect Backend API

FastAPI backend for appliance parts search and retrieval.

## Tech Stack

- **Framework**: FastAPI 0.128.8
- **Server**: Uvicorn 0.40.0 (ASGI)
- **Database**: PostgreSQL 14+
- **Validation**: Pydantic 2.5.0
- **DB Driver**: psycopg2-binary 2.9.9
- **Environment**: python-dotenv 1.0.0

## Architecture

```
backend/
├── app.py                 # Application entry point
├── config.py              # Environment configuration
├── requirements.txt       # Python dependencies
├── .env                   # Database credentials
├── models/                # Pydantic data models
│   ├── chat.py           # Chat request/response models
│   └── part.py           # Part data model
├── routes/                # API endpoint handlers
│   ├── health.py         # Health check endpoints
│   ├── chat.py           # Search endpoint
│   └── parts.py          # Part details endpoint
├── services/              # Business logic layer
│   ├── database.py       # Database operations
│   └── chat_service.py   # Search service
└── test_backend.py        # Comprehensive test suite
```

## Database Connection

**Location**: `services/database.py`

**Configuration**: Loads from `.env` file
```python
DB_HOST=localhost
DB_PORT=5432
DB_NAME=partselect_db
DB_USER=aryan
DB_PASSWORD=
```

**Connection Pattern**: Connection per request (no pooling implemented)
- Each query creates new connection
- Connections closed after query execution
- RealDictCursor for dict-based results

## API Endpoints

### 1. Root Endpoint
**GET /**

**Input**: None

**Output**:
```json
{
  "service": "PartSelect Chat Agent",
  "version": "1.0.0",
  "status": "online"
}
```

---

### 2. Health Check
**GET /health**

**Input**: None

**Output**:
```json
{
  "status": "ok",
  "database": "connected",
  "timestamp": "2026-02-11T22:52:01.481331"
}
```

**Purpose**: Database connectivity verification

---

### 3. Chat/Search Endpoint
**POST /api/chat**

**Input**:
```json
{
  "message": "string (required, min_length=1)",
  "conversation_id": "string (optional)"
}
```

**Search Capabilities**:
- Part name (e.g., "ice maker", "water filter")
- PartSelect number (e.g., "PS12364199", "12364199")
- Manufacturer part number
- Keywords with partial matching (ILIKE)
- Full-text search on part names

**Output**:
```json
{
  "reply": "string (context-aware message)",
  "metadata": {
    "type": "product_search",
    "count": 4,
    "products": [
      {
        "part_id": "uuid",
        "part_name": "string",
        "current_price": "decimal",
        "rating": "decimal (nullable)",
        "review_count": "integer",
        "image_url": "string (nullable)",
        "product_url": "string"
      }
    ]
  }
}
```

**Reply Messages**:
- 0 results: "I couldn't find any parts matching your search..."
- 1 result: "I found 1 part that matches your search:"
- N results: "I found {N} parts that match your search:"

**Flow**:
1. `routes/chat.py` → Validates request with Pydantic
2. `services/chat_service.py` → Processes search
3. `services/database.py` → Executes SQL query
4. Returns formatted ChatResponse

**Limit**: Returns max 4 results (ordered by rating DESC)

---

### 4. Part Details Endpoint
**GET /api/part/{part_id}**

**Input**:
- `part_id`: UUID (path parameter)

**Output**:
```json
{
  "part_id": "uuid",
  "part_name": "string",
  "current_price": "float",
  "original_price": "float",
  "has_discount": "boolean",
  "rating": "float (nullable)",
  "review_count": "integer",
  "brand": "string",
  "appliance_type": "string",
  "availability": "string",
  "image_url": "string",
  "product_url": "string",
  "compatible_models": ["string array", "max 10"]
}
```

**Flow**:
1. `routes/parts.py` → Validates UUID format
2. `services/database.py` → get_part_by_id() + get_compatible_models()
3. SQL JOIN with models table
4. Returns 404 if not found

**Errors**:
- 404: Invalid UUID or part not found
- 500: Database error

---

## Pydantic Models

### ChatRequest
```python
message: str           # Required, min_length=1, auto-stripped
conversation_id: str   # Optional, for future conversation tracking
```

**Validation**: Empty/whitespace-only messages rejected with 422

### ChatResponse
```python
reply: str                    # Human-readable message
metadata: ChatMetadata        # Search results
```

### ChatMetadata
```python
type: str                     # Always "product_search"
count: int                    # Number of results
products: List[PartCard]      # Product array
```

### PartCard
```python
part_id: str                  # UUID as string
part_name: str
current_price: Decimal
rating: Optional[Decimal]
review_count: int
image_url: Optional[str]
product_url: str
```

## Services & Functions

### DatabaseService (`services/database.py`)

**Singleton Pattern**: `db_service` instance

#### `get_connection() -> psycopg2.connection`
Creates PostgreSQL connection with RealDictCursor.

#### `test_connection() -> bool`
Verifies database connectivity. Used by health endpoint.

#### `search_parts(search_term: str, limit: int = 4) -> List[Dict]`
**Purpose**: Multi-field part search

**SQL Query**:
```sql
WHERE part_name ILIKE %pattern%
   OR manufacturer_part_number ILIKE %pattern%
   OR part_number ILIKE %pattern%
   OR to_tsvector('english', part_name) @@ to_tsquery('english', %query%)
ORDER BY rating DESC NULLS LAST
```

**Returns**: List of part dicts with all fields

#### `get_part_by_id(part_id: str) -> Optional[Dict]`
**Purpose**: Retrieve single part with compatible models

**SQL**: LEFT JOIN with models table, JSON aggregation

**Returns**: Part dict with compatible_models array or None

#### `get_compatible_models(part_id: str, limit: int = 10) -> List[str]`
**Purpose**: Get model numbers for a part

**Returns**: List of model number strings

---

### ChatService (`services/chat_service.py`)

#### `search(message: str) -> ChatResponse`
**Purpose**: Process search query and format response

**Flow**:
1. Call `db_service.search_parts(message)`
2. Convert DB dicts to PartCard models
3. Generate context-aware reply message
4. Return ChatResponse with metadata

**Error Handling**: Skips malformed parts (KeyError, TypeError, ValueError)

## Current Scope & Limitations

### Implemented
- ✅ Part search by name, PartSelect number, keywords
- ✅ Full-text search on part names
- ✅ Part details with compatible models
- ✅ Database connectivity checks
- ✅ Request validation (422 errors)
- ✅ Error handling (404, 500)
- ✅ CORS enabled for frontend

### Not Implemented
- ❌ Conversation history storage
- ❌ Database connection pooling
- ❌ Authentication/authorization
- ❌ Rate limiting
- ❌ Caching layer
- ❌ Advanced NLP/intent detection
- ❌ Troubleshooting guidance
- ❌ Installation instructions
- ❌ Vector search/embeddings
- ❌ Multi-appliance filtering

### Input Constraints
- Search message: 1-10000 characters (Pydantic default)
- Part ID: Must be valid UUID format
- Search limit: Hardcoded to 4 results
- Compatible models: Hardcoded to 10 models

### Database Requirements
- PostgreSQL must be running on localhost:5432
- Database: `partselect_db`
- Tables: `parts`, `models`, `part_model_mapping`
- Full-text search requires PostgreSQL 9.6+

## Setup & Run

1. **Install dependencies**:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Configure database** (`.env`):
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=partselect_db
DB_USER=aryan
DB_PASSWORD=
```

3. **Start server**:
```bash
python app.py
```

Server runs on **http://localhost:8000**

4. **Access documentation**:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

Run comprehensive test suite:
```bash
python test_backend.py
```

Tests 9 scenarios:
- Root endpoint
- Health check
- Chat search (basic, empty, missing field, conversation ID, various queries)
- Part details (valid/invalid IDs)

## Example Requests

### Search by keyword:
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "water filter"}'
```

### Search by PartSelect number:
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "PS12364199"}'
```

### Get part details:
```bash
curl http://localhost:8000/api/part/f00c3ffe-158b-455c-87a7-fc085a9da4e6
```

## Performance Notes

- No connection pooling: Each request creates new DB connection
- No caching: Every search hits database
- No pagination: Returns fixed limit of 4 results
- Full-text search: Uses PostgreSQL built-in `to_tsvector`
- JOIN overhead: Part details endpoint performs JOIN on every request
