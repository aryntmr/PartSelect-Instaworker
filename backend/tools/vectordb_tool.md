# Vector Database Search Tool - Complete Reference

## Overview

The Vector Database Search Tool performs semantic similarity search across repair guides, troubleshooting articles, maintenance blogs, and policy documents. It uses ChromaDB with embeddings to find the most relevant unstructured content based on meaning and context, not just keyword matching.

## Tool Interface

### Input Parameters

```python
class VectorSearchInput(BaseModel):
    query: str                                    # Required: 3-500 characters
    document_type: Optional[Literal["repair", "blog", "policy"]]  # Optional filter
    appliance_type: Optional[Literal["refrigerator", "dishwasher"]]  # Optional filter
    top_k: int = 5                                # Optional: 1-20, default 5
```

**Parameter Details:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | str | ✅ Yes | Natural language search query. Should be descriptive and include context (e.g., "dishwasher leaking water from door repair guide"). Min 3 chars, max 500 chars. |
| `document_type` | Optional[str] | ❌ No | Filter results by document type. Use "repair" for troubleshooting/repair guides, "blog" for how-to articles, "policy" for returns/warranty/shipping info. Leave `None` to search all types. |
| `appliance_type` | Optional[str] | ❌ No | Filter by appliance. Use "refrigerator" for fridge/freezer content, "dishwasher" for dishwasher content. Leave `None` to search both. (Note: Policies have no appliance_type as they apply universally) |
| `top_k` | int | ❌ No | Number of results to return. Range: 1-20. Default: 5. Use 3-5 for specific queries, 5-10 for broader troubleshooting. |

## Understanding the Vector Database Structure

### One Collection, Three Document Types

All documents live in a single ChromaDB collection called `partselect_docs`. Documents are differentiated by the `document_type` metadata field.

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

### Metadata Schema by Document Type

#### Common Metadata (All Documents)

Every document has these fields regardless of type:

- **document_type**: "repair" | "blog" | "policy"
- **title**: Document title/heading
- **content**: Full text content (primary search field)
- **url**: Source URL on PartSelect.com
- **content_length**: Character count
- **scraped_at**: Timestamp when added

```
partselect_docs/
├── Repair Documents
│   ├── Refrigerator repairs
│   └── Dishwasher repairs
├── Blog Articles
│   ├── Refrigerator blogs
│   └── Dishwasher blogs
└── Policy Documents
    ├── Returns policy
    ├── Warranty information
    └── Shipping details
```

**What's in Each Document Type:**

**Repair Documents (document_type="repair"):**
- Symptom-specific troubleshooting and repair guides with part testing procedures and diagnostic steps
- Covers symptoms
- Refrigerator symptoms include: Ice maker not working, Water dispenser issues, Leaking, Not cooling, Noisy/loud, Will not start, Freezing food, Ice buildup, Door not closing, Light not working, Temperature control issues, Defrost problems, and more
- Dishwasher symptoms include: Leaking, Won't drain, Not cleaning properly, Won't start, Stopping mid-cycle, No water/not filling, Not drying, Noisy, Door issues, Control panel problems, Detergent dispenser issues, and more

**Blog Articles (document_type="blog"):**
- In-depth how-to guides, maintenance tips, error code explanations, and appliance care articles
- Organized into 5 blog topics: "repair", "error-codes", "how-to-guides", "testing", "use-and-care"
- "repair" topic: Step-by-step repair guides for common issues
- "error-codes" topic: Detailed explanations of brand-specific error codes
- "how-to-guides" topic: Instructional content for installations and replacements
- "testing" topic: Guides for testing parts with multimeters
- "use-and-care" topic: Maintenance tips and preventive care

**Policy Documents (document_type="policy"):**
- Company policies covering returns, warranty, and shipping with terms, conditions, and processes
- "returns" policy: 365-day return period with conditions, resaleable criteria, refund process, and return shipping details
- "warranty" policy: One-year warranty coverage on all parts with terms, conditions, and exclusions
- "shipping" policy: Fast shipping information including delivery timeframes (avg 1.8 business days), same-day shipping availability, and shipping methods