# PartSelect Chatbot - Initial Design Document

**Assessment Project for InstaLILY**
**Scope:** Refrigerator & Dishwasher Parts Only

---

## 📋 TABLE OF CONTENTS
1. [Database Schema](#database-schema)
2. [Vector Databases](#vector-databases)
3. [Frontend Design](#frontend-design)
4. [Backend API Endpoints](#backend-api-endpoints)
5. [20 Question Types to Handle](#20-question-types)
6. [Key Learnings & Topics Discussed](#key-learnings--topics-discussed)

---

## 🗄️ DATABASE SCHEMA

### **PostgreSQL/MySQL Tables:**

#### **Table 1: `parts`** (Main Product Catalog)

| Column Name | Type | Description | Example |
|-------------|------|-------------|---------|
| `part_id` | VARCHAR(32) PRIMARY KEY | PartSelect part number | PS11752778 |
| `part_name` | VARCHAR(255) NOT NULL | Name of the part | Door Shelf Bin |
| `manufacturer_part_number` | VARCHAR(64) | Manufacturer's part number | WPW10321304 |
| `brand` | VARCHAR(64) | Manufacturer/Brand | Whirlpool |
| `appliance_type` | VARCHAR(32) | refrigerator or dishwasher | refrigerator |
| `original_price` | DECIMAL(10,2) | Original price (before discount) | 50.00 |
| `current_price` | DECIMAL(10,2) | Current/sale price | 44.95 |
| `has_discount` | BOOLEAN | Whether product has discount | true |
| `rating` | DECIMAL(3,2) | Average rating (0-5) | 4.9 |
| `review_count` | INT | Number of reviews | 127 |
| `description` | TEXT | Part description | This refrigerator door bin... |
| `symptoms` | TEXT | What problems it fixes | Ice maker not working, leaking |
| `replacement_parts` | TEXT | Alternative part numbers | AP6019471, W10321302, ... |
| `installation_difficulty` | VARCHAR(32) | Easy/Medium/Hard | Easy |
| `installation_time` | VARCHAR(64) | Estimated install time | 30-60 mins |
| `delivery_time` | VARCHAR(64) | Estimated delivery | 2-3 business days |
| `availability` | VARCHAR(32) | Stock status | In Stock |
| `image_url` | VARCHAR(512) | Product image URL | https://...jpg |
| `video_url` | VARCHAR(512) | Installation video URL | https://youtube.com/... |
| `product_url` | VARCHAR(512) | PartSelect product page | https://www.partselect.com/... |

---

#### **Table 2: `models`** (Appliance Models)

| Column Name | Type | Description | Example |
|-------------|------|-------------|---------|
| `model_number` | VARCHAR(64) PRIMARY KEY | Appliance model number | WDT780SAEM1 |
| `brand` | VARCHAR(64) | Brand name | Whirlpool |
| `appliance_type` | VARCHAR(32) | refrigerator or dishwasher | dishwasher |
| `description` | TEXT | Model description | Whirlpool Dishwasher Model |
| `model_url` | VARCHAR(512) | PartSelect model page URL | https://... |

---

#### **Table 3: `part_model_mapping`** (Compatibility Cross-Reference)

| Column Name | Type | Description | Example |
|-------------|------|-------------|---------|
| `id` | INT PRIMARY KEY AUTO_INCREMENT | Unique mapping ID | 1 |
| `part_id` | VARCHAR(32) FOREIGN KEY | References parts.part_id | PS11752778 |
| `model_number` | VARCHAR(64) FOREIGN KEY | References models.model_number | WDT780SAEM1 |

**Constraints:**
- UNIQUE (part_id, model_number) - No duplicate mappings
- ON DELETE CASCADE - Delete mappings when part/model deleted
- FOREIGN KEY constraints ensure referential integrity

**Purpose:** Many-to-Many relationship
- One part works with many models
- One model uses many parts

---

## 🔍 VECTOR DATABASES

### **ChromaDB/Pinecone Collections:**

| Collection Name | Purpose | Source | Documents |
|----------------|---------|--------|-----------|
| `refrigerator_repairs` | Repair guides & troubleshooting for refrigerators | Scraped from partselect.com/Repair/Refrigerator/ | ~150-200 |
| `dishwasher_repairs` | Repair guides & troubleshooting for dishwashers | Scraped from partselect.com/Repair/Dishwasher/ | ~150-200 |
| `refrigerator_blogs` | How-to articles & maintenance tips for refrigerators | Scraped from partselect.com/blog/topics/ | ~100-150 |
| `dishwasher_blogs` | How-to articles & maintenance tips for dishwashers | Scraped from partselect.com/blog/topics/ | ~100-150 |
| `policies` | Return policy, warranty, shipping info | Static pages | 3 |

**Usage:** RAG (Retrieval Augmented Generation) for answering repair/troubleshooting questions

---

## 🎨 FRONTEND DESIGN

### **Main Chat Interface:**

```
┌─────────────────────────────────────────────┐
│  PartSelect Chat Assistant                  │
├─────────────────────────────────────────────┤
│                                             │
│  User: "Show me ice maker parts"            │
│                                             │
│  Bot: "Here are some ice maker parts:"      │
│                                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ [Image]  │ │ [Image]  │ │ [Image]  │   │
│  │          │ │          │ │          │   │
│  │Ice Maker │ │Ice Maker │ │Ice Maker │   │
│  │Assembly  │ │Module    │ │Motor     │   │
│  │          │ │          │ │          │   │
│  │$189.99   │ │$124.50   │ │$89.99    │   │
│  │⭐ 4.8    │ │⭐ 4.5    │ │⭐ 4.7    │   │
│  │          │ │          │ │          │   │
│  │[View]    │ │[View]    │ │[View]    │   │
│  └──────────┘ └──────────┘ └──────────┘   │
│                                             │
│  [Type your question...]                    │
└─────────────────────────────────────────────┘
```

---

### **Product Card Component:**

**When to Show:** User asks to search/find parts

**Card Display (4 cards max per response):**

```
┌────────────────────────┐
│   [Product Image]      │ ← image_url
│                        │
│ Part Name              │ ← part_name
│                        │
│ $44.95                 │ ← current_price
│ Original: $50.00       │ ← original_price (if has_discount)
│                        │
│ ⭐ 4.9 (127 reviews)   │ ← rating & review_count
│                        │
│ [View on PartSelect]   │ ← Links to product_url
└────────────────────────┘
```

**Card Data Displayed:**
- Product image (from `image_url`)
- Part name
- Current price
- Original price (if discount exists)
- Rating stars
- Review count
- Link to PartSelect product page (`product_url`)

---

### **Frontend Behavior:**

**Scenario 1: Information Query**
```
User: "Tell me about PS11752778"
Bot: [Text response with part details]
```

**Scenario 2: Search Query**
```
User: "Find ice maker parts for refrigerator"
Bot: "Here are some ice maker parts:"
     [Display 4 product cards]
```

**Scenario 3: Troubleshooting**
```
User: "My dishwasher is leaking"
Bot: [Troubleshooting steps]
     "Recommended parts:"
     [Display 2-3 product cards]
```

---

## 🔌 BACKEND API ENDPOINTS

### **Core Endpoints:**

#### **1. POST `/api/chat`** ⭐ MAIN ENDPOINT
**Purpose:** Main conversational interface
**Input:**
```json
{
  "message": "Show me ice maker parts",
  "conversation_id": "optional-uuid"
}
```
**Output:**
```json
{
  "reply": "Here are some ice maker parts for refrigerators...",
  "metadata": {
    "type": "product_search",
    "products": [
      {
        "part_id": "PS11752158",
        "part_name": "Ice Maker Assembly",
        "current_price": 189.99,
        "original_price": 199.99,
        "has_discount": true,
        "rating": 4.8,
        "review_count": 145,
        "image_url": "https://...",
        "product_url": "https://www.partselect.com/..."
      }
    ]
  }
}
```

**Handles All 20 Question Types:**
- Product information
- Compatibility checking
- Installation guidance
- Troubleshooting
- Policy questions
- General questions

---

#### **2. GET `/health`**
**Purpose:** Health check
**Output:**
```json
{
  "status": "ok",
  "database": "connected",
  "vector_db": "connected",
  "llm": "available"
}
```

---

#### **3. GET `/`**
**Purpose:** API info
**Output:**
```json
{
  "service": "PartSelect Chat Agent",
  "version": "1.0.0",
  "status": "online"
}
```

---

#### **4. GET `/api/part/{part_id}`**
**Purpose:** Direct part lookup (for frontend)
**Input:** Part ID in URL
**Example:** `GET /api/part/PS11752778`
**Output:**
```json
{
  "part_id": "PS11752778",
  "part_name": "Door Shelf Bin",
  "current_price": 44.95,
  "original_price": 50.00,
  "has_discount": true,
  "rating": 4.9,
  "review_count": 127,
  "brand": "Whirlpool",
  "appliance_type": "refrigerator",
  "availability": "In Stock",
  "image_url": "https://...",
  "product_url": "https://...",
  "compatible_models": ["WDT780SAEM1", "WDT780SAEM0", ...]
}
```

**Use Case:** Frontend needs part details when user clicks product card

---

#### **5. DELETE `/api/conversation/{conversation_id}`**
**Purpose:** Clear conversation history
**Output:**
```json
{
  "status": "deleted"
}
```

---

## ❓ 20 QUESTION TYPES TO HANDLE

### **Category 1: Part Information (4 questions)**
1. "Tell me about part number PS11752778"
2. "What is the price of PS11752158?"
3. "Show me water inlet valves for refrigerators"
4. "Do you have ice maker assemblies in stock?"

### **Category 2: Compatibility Checking (4 questions)**
5. "Is part PS11752778 compatible with my WDT780SAEM1 model?"
6. "Will this door gasket work with my Samsung refrigerator RF28R7351SR?"
7. "What parts are compatible with Whirlpool dishwasher WDF520PADM7?"
8. "Can I use PS11752158 on my GE fridge model GNE27JSMSS?"

### **Category 3: Installation Guidance (3 questions)**
9. "How do I install part number PS11752778?"
10. "What tools do I need to replace the ice maker?"
11. "How difficult is it to install a dishwasher door seal?"

### **Category 4: Troubleshooting & Repair (5 questions)**
12. "The ice maker on my Whirlpool fridge is not working. How can I fix it?"
13. "My dishwasher is leaking water from the door"
14. "Refrigerator is making loud noises"
15. "Dishwasher won't drain properly"
16. "What does error code E5 mean on my LG dishwasher?"

### **Category 5: How-To & General (2 questions)**
17. "How do I clean my refrigerator water filter?"
18. "What is the difference between eco mode and normal mode?"

### **Category 6: Policies (2 questions)**
19. "What is your return policy?"
20. "How long does shipping take?"

---

## 📚 KEY LEARNINGS & TOPICS DISCUSSED

### **1. Web Scraping**
- **Tools Used:** BeautifulSoup, Selenium, Puppeteer, Playwright
- **Data Storage:** JSON files first, then load to databases
- **Discount Detection:** Check for `price__discount-badge` class or `sale` class in HTML

**All Data Sources Scraped** (from PartSelect.com):

**1. Parts Catalog:**
- `https://www.partselect.com/Refrigerator-Parts.htm` (General refrigerator parts)
- `https://www.partselect.com/Dishwasher-Parts.htm` (General dishwasher parts)
- Brand-specific parts pages (examples):
  - `https://www.partselect.com/Whirlpool-Refrigerator-Parts.htm`
  - `https://www.partselect.com/GE-Refrigerator-Parts.htm`
  - `https://www.partselect.com/Samsung-Refrigerator-Parts.htm`
  - `https://www.partselect.com/LG-Dishwasher-Parts.htm`
  - `https://www.partselect.com/Bosch-Dishwasher-Parts.htm`
  - (43 brands total - Whirlpool, GE, Samsung, LG, Frigidaire, etc.)

**2. Repair & Troubleshooting Guides:**
- `https://www.partselect.com/Repair/Refrigerator/` (21 refrigerator symptoms)
- `https://www.partselect.com/Repair/Dishwasher/` (21 dishwasher symptoms)
- Examples of symptom pages:
  - `/Repair/Refrigerator/Ice-maker-not-making-ice/`
  - `/Repair/Refrigerator/Refrigerator-water-dispenser-not-working/`
  - `/Repair/Refrigerator/Refrigerator-is-noisy-or-loud/`
  - `/Repair/Dishwasher/Dishwasher-leaking/`
  - `/Repair/Dishwasher/Dishwasher-won-t-drain/`
  - `/Repair/Dishwasher/Dishwasher-not-cleaning-dishes-properly/`

**3. Blog & How-To Articles:**
- `https://www.partselect.com/blog/topics/repair`
- `https://www.partselect.com/blog/topics/error-codes`
- `https://www.partselect.com/blog/topics/how-to-guides`
- `https://www.partselect.com/blog/topics/testing`
- `https://www.partselect.com/blog/topics/use-and-care`

**4. Policy Pages:**
- `https://www.partselect.com/365-Day-Returns.htm` (Return policy)
- `https://www.partselect.com/One-Year-Warranty.htm` (Warranty info)
- `https://www.partselect.com/Fast-Shipping.htm` (Shipping details)

**Data Collected Per Page:**
- **Parts:** part_id, name, price (original + discount), brand, images, ratings, reviews, availability, compatible models, installation difficulty/time, symptoms fixed
- **Repairs:** symptom description, difficulty level, repair time, required tools, step-by-step instructions, video links (YouTube), related parts
- **Blogs:** article title, content, category, published date, author, images
- **Policies:** policy text, terms, conditions

### **2. Database Design (RDBMS)**
- **Primary Key (PK):** Unique identifier for each row (e.g., `part_id`)
- **Foreign Key (FK):** Reference to another table's PK (e.g., `mapping.part_id → parts.part_id`)
- **Composite Key:** Multiple columns as PK (alternative for mapping table)
- **Many-to-Many Relationship:** Requires junction/mapping table
- **Normalization:** 3NF - no redundant data, everything depends on PK
- **Constraints:**
  - NOT NULL - Field required
  - UNIQUE - No duplicates
  - CHECK - Custom validation
  - DEFAULT - Default value
  - ON DELETE CASCADE - Delete dependent rows when parent deleted
- **Referential Integrity:** FK must reference valid PK
- **Index:** Speeds up searches (like book index)

### **3. SQL Operations**
- **JOIN Types:**
  - INNER JOIN - Matching rows from both tables
  - LEFT JOIN - All from left + matching from right
- **Queries:**
  - "Get part details" → `SELECT * FROM parts WHERE part_id = '...'`
  - "Check compatibility" → `SELECT * FROM part_model_mapping WHERE part_id = '...' AND model_number = '...'`
  - "Get compatible models" → `JOIN parts, mapping, models`

### **4. Endpoint Design Principles**
- ❌ **DON'T:** Have endpoint call another endpoint (same app)
  - Slow (HTTP overhead)
  - More failure points
  - Hard to debug
- ✅ **DO:** Use shared functions/services
  - Fast (direct function call)
  - Clean code
  - Easy to test

### **5. Endpoint vs Shared Function**
```python
# GOOD - Both endpoints use SAME shared function
services/part_service.py:
    def get_part_info(part_id):
        return db.query(...)

@app.post("/api/chat"):
    part = get_part_info(part_id)  # Shared function
    return llm_response(part)

@app.get("/api/part/{part_id}"):
    return get_part_info(part_id)  # Same shared function
```

### **6. When to Use Different Endpoints**
- `/api/chat` - Conversational interface (LLM processing)
- `/api/part/{part_id}` - Direct API access (no LLM)
- Different purposes, same underlying logic

### **7. Policy Pages Approach**
- ❌ **NOT** separate SQL tables (over-engineering)
- ❌ **NOT** separate endpoint
- ✅ **Vector DB** - Store in ChromaDB/Pinecone
- ✅ **Retrieve via RAG** in `/api/chat` endpoint

### **8. Architecture Decisions**
- **Intent Routing:** Keyword-based (NOT LLM-based) for speed
- **Hybrid Search:** BM25 (keyword) + Vector (semantic)
- **Caching:** Cache LLM responses and tool results
- **Conversation Memory:** Last 5-10 messages
- **Structured Responses:** Return metadata with product cards
- **Scope Enforcement:** Only refrigerator/dishwasher (reject other appliances)

### **9. Tech Stack Choices**
- **Backend:** FastAPI (Python) - Most projects used this
- **Database:** PostgreSQL or MySQL + SQLAlchemy ORM
- **Vector DB:** ChromaDB (most popular) or Pinecone
- **LLM:** DeepSeek or OpenAI
- **Frontend:** Next.js or React
- **Storage Format:** Scrape → JSON/CSV → Load to DBs

### **10. What NOT to Do**
- ❌ Don't use LLM for intent routing (slow, expensive)
- ❌ Don't create 10+ endpoints (over-engineering)
- ❌ Don't have endpoints call each other via HTTP (same app)
- ❌ Don't store policies in SQL tables
- ❌ Don't return only text (need structured metadata)
- ❌ Don't hardcode values (use env vars)
- ❌ Don't use MongoDB (no projects used it - use SQL!)

### **11. RDBMS Jargon Summary**
| Term | Meaning |
|------|---------|
| Relational Database | Entire database with tables that have relationships |
| Table/Relation | Collection of rows and columns |
| Row/Record/Tuple | Single entry in table |
| Column/Field/Attribute | Property of data |
| Schema | Database structure/blueprint |
| Primary Key | Unique row identifier |
| Foreign Key | Reference to another table's PK |
| Composite Key | Multiple columns as PK |
| One-to-Many | One row → many rows (part → mappings) |
| Many-to-Many | Many → Many (needs junction table) |
| Junction/Mapping Table | Enables many-to-many relationships |
| Index | Speeds up searches |
| Constraint | Data validation rule |
| Referential Integrity | FK must reference valid PK |
| Normalization | Organizing data to reduce redundancy |
| JOIN | Combine tables based on relationship |
| ORM | Map database tables to code objects |
| ACID | Database reliability (Atomicity, Consistency, Isolation, Durability) |

### **12. Data Flow**
```
Web Scraping
    ↓
JSON/CSV files (raw data)
    ↓
Clean & Process
    ↓
Load to Databases:
    - SQL (structured: parts, models, mappings)
    - Vector DB (unstructured: repairs, blogs, policies)
    ↓
API Endpoints Query DBs
    ↓
Frontend Displays Results
```

### **13. Project Stats from Analysis**
- **Total Projects:** 11
- **Used FastAPI:** 9 projects
- **Used SQL:** 5 projects (MySQL, PostgreSQL, SQLite)
- **Used Vector DB:** 6 projects (ChromaDB, Pinecone, FAISS)
- **Used MongoDB:** 0 projects
- **Web Scraping:** 9 projects (all scraped PartSelect.com)
- **Most Common Scrapers:** BeautifulSoup + Selenium

### **14. Important Realizations**
- **Policies:** Static pages, not product-specific → Vector DB, not SQL
- **Endpoint Purpose:** Different endpoints serve different use cases (chat vs direct API)
- **Performance:** Function calls (microseconds) vs HTTP (milliseconds)
- **Architecture:** Keep it simple - 5-6 endpoints is optimal
- **Focus:** 90% effort on `/api/chat` endpoint quality

---

## 🎯 SUCCESS CRITERIA

**To Get Hired:**
1. ✅ Handle all 20 question types
2. ✅ Clean database design (3NF, proper relationships)
3. ✅ Fast intent routing (keyword-based)
4. ✅ Structured responses with product cards
5. ✅ Conversation context awareness
6. ✅ Good error handling
7. ✅ Clean code structure
8. ✅ API documentation
9. ✅ README with setup instructions

**Where to Focus Effort:**
- 90% - `/api/chat` endpoint quality
- 5% - Database design
- 5% - Other endpoints

---

## 📝 NOTES

- This document captures the initial design decisions and learnings
- Database schema may evolve during implementation
- Endpoint list is minimal but complete (can add more if needed)
- All scraping sources are from PartSelect.com
- Scope strictly limited to refrigerator & dishwasher parts

**Last Updated:** Initial Design Phase
**Next Steps:** Start implementation
