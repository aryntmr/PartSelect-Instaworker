# Vector Database Search Tool

## Tool Description

**Name:** `vector_search_tool`

**Purpose:** Performs semantic similarity search across repair guides, troubleshooting articles, maintenance blogs, and policy documents using ChromaDB. Returns relevant unstructured content based on meaning and context rather than exact keyword matching.

**Capabilities:**
- Semantic understanding of queries (e.g., "broken" matches "not working")
- Unified search across repair guides, blog articles, and policy documents
- Rich metadata returned with each result for context-aware responses
- Natural language query processing without exact keyword requirements

---

## Input Schema

```python
class VectorSearchInput(BaseModel):
    query: str                                                      # Required: 3-500 chars
    document_type: Optional[Literal["repair", "blog", "policy"]]   # Optional
    appliance_type: Optional[Literal["refrigerator", "dishwasher"]] # Optional
    top_k: int = 5                                                  # Default: 5, Range: 1-20
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | str | Yes | Natural language search query with context. Min 3 chars, max 500 chars. |
| `document_type` | Optional[str] | No | Filter by type: "repair" (troubleshooting/repair guides), "blog" (how-to/maintenance), "policy" (returns/warranty/shipping). Default: None (search all). |
| `appliance_type` | Optional[str] | No | Filter by appliance: "refrigerator" or "dishwasher". Default: None (search both). Note: Ignored for policies. |
| `top_k` | int | No | Number of results (1-20). Default: 5. Use 3-5 for specific queries, 5-10 for broad troubleshooting. |

---

## Output Format

```python
[
    {
        "content": str,              # Document text
        "metadata": {
            "document_type": str,    # "repair" | "blog" | "policy"
            "title": str,
            "url": str,
            # Type-specific fields (category, part_name, topic, etc.)
        },
        "relevance_score": float     # 0-1, higher = more relevant
    }
]
```

---

## Usage Guidelines

### When to Use Vector DB Tool

| Use Case | Examples |
|----------|----------|
| **Repair & Troubleshooting** | "How do I fix a leaking dishwasher?", "Ice maker not working", "Dishwasher won't drain" |
| **Error Codes** | "What does error code E15 mean?", "GE dishwasher H20 error" |
| **How-To & Maintenance** | "How to clean refrigerator water filter?", "Prevent ice buildup in freezer" |
| **Symptom Diagnosis** | "Refrigerator not cooling", "Dishwasher stopping mid-cycle" |
| **Policy Questions** | "What's your return policy?", "How long does shipping take?" |

### When to Use SQL Tool Instead

| Use Case | Examples |
|----------|----------|
| **Part Information** | "Tell me about part PS11752778", "What's the price?", "Is it in stock?" |
| **Compatibility** | "Is part X compatible with model Y?", "What parts work with WDT780SAEM1?" |
| **Part Search** | "Show me Whirlpool parts under $50", "Parts with 5-star ratings" |
| **Purchase/Ordering** | Availability checks, price comparisons, part specifications |

---

## Database Structure

### Collection Overview

Single ChromaDB collection: `partselect_docs`

```
partselect_docs/
├── Repair Documents (~300-400 docs)
│   ├── Refrigerator repairs (21 symptoms × ~7 parts each)
│   └── Dishwasher repairs (21 symptoms × ~7 parts each)
├── Blog Articles (~200-300 docs)
│   ├── Refrigerator blogs (repair guides, how-tos, error codes)
│   └── Dishwasher blogs (repair guides, how-tos, error codes)
└── Policy Documents (3 docs)
    ├── Returns policy
    ├── Warranty information
    └── Shipping details
```

### Document Type Details

**Repair Documents (document_type="repair"):**
- Symptom-specific troubleshooting and repair guides with part testing procedures
- Coverage: 42 total symptoms (21 refrigerator, 21 dishwasher), ~7 parts per symptom
- Refrigerator symptoms: Ice maker not working, Water dispenser issues, Leaking, Not cooling, Noisy/loud, Will not start, Freezing food, Ice buildup, Door not closing, Light not working, Temperature control issues, Defrost problems
- Dishwasher symptoms: Leaking, Won't drain, Not cleaning properly, Won't start, Stopping mid-cycle, No water/not filling, Not drying, Noisy, Door issues, Control panel problems, Detergent dispenser issues

**Blog Articles (document_type="blog"):**
- In-depth how-to guides, maintenance tips, error code explanations, appliance care articles
- 5 topics: "repair", "error-codes", "how-to-guides", "testing", "use-and-care"
- "repair": Step-by-step repair guides (e.g., "Why Your Dishwasher is Stopping Mid-Cycle")
- "error-codes": Brand-specific error explanations (e.g., "Bosch E15 Error", "GE H20 Error")
- "how-to-guides": Installation and replacement procedures
- "testing": Part testing with multimeters
- "use-and-care": Maintenance tips and preventive care

**Policy Documents (document_type="policy"):**
- Company policies: returns, warranty, shipping
- "returns": 365-day return period, conditions, refund process, return shipping
- "warranty": One-year warranty coverage, terms, conditions, exclusions
- "shipping": Delivery timeframes (avg 1.8 business days), same-day shipping, shipping methods

---

## Metadata Schema

### Common Fields (All Documents)

- `document_type`: "repair" | "blog" | "policy"
- `title`: Document title
- `content`: Full text content (primary search field)
- `url`: Source URL
- `content_length`: Character count
- `scraped_at`: Timestamp

### Repair Document Fields

```python
{
    "document_type": "repair",
    "appliance_type": "refrigerator" | "dishwasher",
    "category": str,           # Symptom category (e.g., "Leaking")
    "title": str,
    "part_name": str,          # Part discussed in guide
    "part_id": str,            # Use to query SQL database
    "difficulty": str,         # "Easy" | "Moderate" | "Difficult" | ""
    "repair_time": str,        # "15-30 minutes" | "1-2 hours" | ""
    "has_video": bool,
    "video_urls": str,
    "video_count": int,
    "symptom_url": str,
    "content": str
}
```

### Blog Document Fields

```python
{
    "document_type": "blog",
    "appliance_type": "refrigerator" | "dishwasher",
    "title": str,
    "topic": "repair" | "error-codes" | "how-to-guides" | "testing" | "use-and-care",
    "author": str,
    "excerpt": str,
    "meta_description": str,
    "topic_source": str,
    "content": str
}
```

### Policy Document Fields

```python
{
    "document_type": "policy",
    "policy_type": "returns" | "warranty" | "shipping",
    "title": str,
    "meta_description": str,
    "section_headings": List[str],
    "full_content": str
    # No appliance_type - policies apply universally
}
```

---

## Query Construction Best Practices

### 1. Query Specificity

**Poor Queries:**
- `"leaking"`
- `"broken"`
- `"error code"`

**Effective Queries:**
- `"dishwasher leaking water from door seal gasket repair guide"`
- `"refrigerator ice maker not working not making ice troubleshooting"`
- `"Bosch dishwasher E15 error code meaning how to fix"`

**Include:**
- Appliance type (if known)
- Specific symptom or problem
- Desired outcome (repair, fix, troubleshoot)
- Relevant keywords (error codes, part names)

### 2. Filter Strategy

**document_type Filter:**
- Specify when intent is clear (policy questions → "policy", troubleshooting → "repair", how-to → "blog")
- Leave as `None` for ambiguous queries or broad searches

**appliance_type Filter:**
- Specify when user mentions specific appliance
- Leave as `None` for policies or unspecified queries

### 3. top_k Guidelines

| Query Type | Recommended top_k |
|-----------|-------------------|
| Specific error codes | 3 |
| Policy questions | 3 |
| Symptom troubleshooting | 5-7 |
| Broad "how to" questions | 5-10 |
| Default | 5 |

### 4. Metadata Utilization

Extract and use metadata from results:
- `has_video`: Inform user of video availability
- `part_name`, `part_id`: Query SQL tool for part details
- `difficulty`: Communicate repair complexity
- `category`: Provide symptom context
- `topic`: Distinguish repair guides from maintenance tips

---

## Tool Combination Patterns

### Pattern 1: Repair Guide → Part Details

**Scenario:** User needs troubleshooting AND part information

1. **Vector DB:** Search for repair guide → Extract `part_name`, `part_id` from metadata
2. **SQL Tool:** Query parts table using extracted part information
3. **Response:** Combine repair instructions with part details (price, availability, ratings)

**Example:**
```
User: "My dishwasher is leaking water from the door"

Vector DB → part_name="Door Gasket", part_id="DoorGasketsOr"
SQL Tool → Price: $24.95, Rating: 4.8/5, In Stock
Response: Repair instructions + part details + purchase link
```

### Pattern 2: Part → Installation Guide

**Scenario:** User has part, needs installation instructions

1. **SQL Tool:** Get part details (name, type, appliance)
2. **Vector DB:** Search for installation guide using part name and appliance type
3. **Response:** Installation instructions with video links

---

## Example Queries

### Repair & Troubleshooting
```python
{"query": "dishwasher leaking water from bottom door seal repair", "document_type": "repair", "appliance_type": "dishwasher", "top_k": 5}
{"query": "refrigerator not cooling properly fridge warm troubleshooting", "document_type": "repair", "appliance_type": "refrigerator", "top_k": 5}
{"query": "refrigerator ice maker not working not making ice cubes", "document_type": "repair", "appliance_type": "refrigerator", "top_k": 5}
```

### Error Codes
```python
{"query": "Bosch dishwasher E15 error code meaning fix water leak", "document_type": "blog", "appliance_type": "dishwasher", "top_k": 3}
{"query": "GE dishwasher H20 error code water supply issue fix", "document_type": "blog", "appliance_type": "dishwasher", "top_k": 3}
```

### Maintenance
```python
{"query": "how to clean refrigerator water filter replacement maintenance", "document_type": "blog", "appliance_type": "refrigerator", "top_k": 5}
{"query": "prevent ice buildup freezer frost formation tips maintenance", "document_type": "blog", "appliance_type": "refrigerator", "top_k": 5}
```

### Policies
```python
{"query": "return policy refund how to return parts process", "document_type": "policy", "appliance_type": None, "top_k": 3}
{"query": "warranty coverage parts one year warranty information", "document_type": "policy", "appliance_type": None, "top_k": 3}
{"query": "shipping delivery time fast shipping how long", "document_type": "policy", "appliance_type": None, "top_k": 3}
```

### Ambiguous (No Filters)
```python
{"query": "dishwasher won't start not turning on power issue", "document_type": None, "appliance_type": "dishwasher", "top_k": 7}
{"query": "refrigerator making loud noise sounds rattling humming", "document_type": None, "appliance_type": "refrigerator", "top_k": 7}
```

---

## Semantic Search Fundamentals

### Capability Comparison

**Traditional Keyword Search:**
- Exact term matching only
- "ice maker broken" ≠ "ice maker not working"
- Misses synonyms and related concepts

**Semantic Search (Embeddings):**
- Meaning-based matching
- "ice maker broken" ≈ "ice maker not working"
- Context understanding: "fridge" = "refrigerator", "not cooling" ≈ "warm"
- Concept matching beyond specific words

### Semantic Matching Examples

| User Query | Matches Documents With |
|-----------|------------------------|
| "dishwasher leaking" | "water pooling", "wet floor", "leak detection" |
| "ice maker broken" | "ice maker not working", "no ice cubes", "ice production stopped" |
| "loud noise" | "rattling sound", "humming", "buzzing", "noisy compressor" |
| "won't start" | "not turning on", "no power", "dead", "doesn't run" |

### Relevance Scores

| Score Range | Interpretation | Action |
|------------|----------------|--------|
| 0.9-1.0 | Highly relevant, near-exact semantic match | Prioritize in response |
| 0.8-0.9 | Very relevant, strong conceptual match | Include in response |
| 0.7-0.8 | Relevant, good match with context | Include if top_k allows |
| 0.6-0.7 | Moderately relevant, tangential | Consider filtering |
| <0.6 | Low relevance | Filter out, may need SQL tool |

---

## Common Issues & Solutions

### Issue 1: Overly Generic Queries
**Problem:** Query lacks context (e.g., `"leaking"`)
**Solution:** Add appliance type, symptom details, desired outcome

### Issue 2: Wrong Tool Selection
**Problem:** Using Vector DB for part pricing, availability
**Solution:** Use SQL tool for structured data queries

### Issue 3: Ignoring Metadata
**Problem:** Returning raw content without leveraging metadata
**Solution:** Extract metadata fields to enhance response quality

### Issue 4: Single-Tool Usage
**Problem:** Using only Vector DB when user needs part details AND repair guide
**Solution:** Chain Vector DB (repair guide) → SQL (part details) for comprehensive responses

---

## Summary

**Primary Use Cases:**
- Repair guides and troubleshooting
- How-to articles and maintenance tips
- Error code explanations
- Policy information (returns, warranty, shipping)
- Symptom-based diagnosis

**Key Features:**
- Semantic understanding (concept matching, not keywords)
- Rich metadata for context-aware responses
- Tool combination capability with SQL tool
- Natural language query support

**Critical Requirements:**
- Write descriptive queries with context
- Apply filters strategically based on query intent
- Leverage metadata to enhance responses
- Combine with SQL tool for complete answers (repair + part details)
- Adjust top_k based on query specificity
