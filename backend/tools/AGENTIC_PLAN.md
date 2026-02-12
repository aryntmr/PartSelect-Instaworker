# PartSelect AI Agent - Architecture Plan

## Overview

Autonomous LangChain agent with 2 tools for answering customer queries about refrigerator and dishwasher parts, repairs, and policies.

---

## Agent Architecture

**Type:** Autonomous LangChain Agent (ReAct pattern)

**Model:** DeepSeek/OpenAI (configurable)

**Behavior:**
- Fully autonomous decision-making
- Loops until sufficient information is gathered
- Self-determines when to stop and provide final answer
- Can call tools multiple times in any order
- No external stopping mechanism - agent decides completion

**Scope:**
- Refrigerator and dishwasher parts only
- Rejects out-of-scope queries (other appliances, unrelated topics)

---

## Tools

### 1. SQL Search Tool

**Purpose:** Query PostgreSQL database for structured part data

**Input:**
- Raw SQL query string (no Pydantic validation on query)
- Agent constructs SQL based on user intent

**Output:**
- List of database records (parts, models, compatibility)

**Use Cases:**
- Part information (price, availability, ratings)
- Compatibility checks (part-model mapping)
- Part search by attributes (brand, price range, ratings)
- Stock availability

**Database:**
- PostgreSQL with 3 tables: `parts`, `models`, `part_model_mapping`
- 92 parts, 1,845 models, 2,735 compatibility mappings

**Validation:**
- Field descriptions provided for LLM understanding
- SQL syntax validation at execution

---

### 2. Vector DB Search Tool

**Purpose:** Semantic search across repair guides, blogs, and policies

**Input (Pydantic Validated):**
```python
{
    "query": str,              # Required: 3-500 chars
    "document_type": Optional["repair" | "blog" | "policy"],
    "appliance_type": Optional["refrigerator" | "dishwasher"],
    "top_k": int = 5           # Range: 1-20
}
```

**Output:**
- List of documents with content, metadata, relevance scores

**Use Cases:**
- Repair and troubleshooting guides
- Error code explanations
- How-to and maintenance articles
- Policy information (returns, warranty, shipping)

**Database:**
- ChromaDB with 1 collection: `partselect_docs`
- ~500-700 documents (repairs, blogs, policies)
- Semantic search using embeddings

**Validation:**
- Pydantic model validates input parameters
- Ensures document_type and appliance_type are valid enums
- Validates top_k range (1-20)

---

## Agent Decision Flow

```
User Query
    ↓
Agent Reasoning
    ↓
Decision: Which tool(s) to use?
    ↓
┌─────────────────────┬─────────────────────┐
│   SQL Search Tool   │  Vector DB Tool     │
│   (Structured data) │  (Unstructured)     │
└─────────────────────┴─────────────────────┘
    ↓                       ↓
Tool Response(s)       Tool Response(s)
    ↓                       ↓
Agent Evaluates: Enough information?
    ↓
    ├─ NO → Loop (call more tools)
    └─ YES → Generate final answer
```

**Example Loops:**

**Scenario 1: Simple Query**
```
User: "What's your return policy?"
Loop 1: Vector DB (policy) → Get policy → STOP
```

**Scenario 2: Complex Query**
```
User: "My dishwasher is leaking, what part do I need and how much?"
Loop 1: Vector DB (repair guide) → Extract part_name="Door Gasket"
Loop 2: SQL (search parts) → Get price, availability, ratings → STOP
```

**Scenario 3: Multi-Step**
```
User: "I bought PS11752778, how do I install it and is it in stock?"
Loop 1: SQL (get part details) → Get part_name, appliance_type
Loop 2: SQL (check availability) → Get stock status
Loop 3: Vector DB (installation guide) → Get instructions → STOP
```

---

## Tool Selection Logic

| User Query Type | Primary Tool | Secondary Tool | Reason |
|----------------|--------------|----------------|---------|
| Part info, pricing, compatibility | SQL | - | Structured data in database |
| Troubleshooting, repair guides | Vector DB | SQL (if parts mentioned) | Unstructured content |
| Error codes | Vector DB | - | Blog articles |
| Policies (return, warranty, shipping) | Vector DB | - | Policy documents |
| "What part + how much?" | Vector DB → SQL | - | Need both repair guide and pricing |
| "I have part X, how to install?" | SQL → Vector DB | - | Get part details, then instructions |

---

## Validation Strategy

### SQL Tool Validation

**No Input Validation:**
- Tool receives raw SQL query string
- Agent responsible for generating valid SQL

**Field-Level Guidance:**
- Comprehensive field descriptions provided in tool description
- Agent understands what each database column represents
- Prevents querying non-existent fields

**Execution Validation:**
- PostgreSQL validates SQL syntax
- Returns error if invalid query
- Agent can retry with corrected query

### Vector DB Tool Validation

**Pydantic Input Validation:**
```python
class VectorSearchInput(BaseModel):
    query: str = Field(min_length=3, max_length=500)
    document_type: Optional[Literal["repair", "blog", "policy"]] = None
    appliance_type: Optional[Literal["refrigerator", "dishwasher"]] = None
    top_k: int = Field(default=5, ge=1, le=20)
```

**What's Validated:**
- Query length (3-500 characters)
- document_type is valid enum or None
- appliance_type is valid enum or None
- top_k is within range (1-20)

**What's NOT Validated (Intentionally):**
- Query content/quality (agent's responsibility)
- Semantic meaning (handled by embeddings)
- Type-specific metadata filters (flexible schema)

### Agent-Level Validation

**Scope Enforcement:**
- Agent system prompt restricts scope to refrigerator/dishwasher
- Rejects queries about other appliances
- Rejects unrelated topics

**Response Validation:**
- Agent checks if tool responses are sufficient
- Decides if additional tool calls needed
- Ensures final answer is comprehensive

---

## Tool Combination Patterns

### Pattern 1: Sequential (Vector → SQL)
**Use Case:** User needs repair guide + part details
```python
# Step 1: Get repair guide
vector_response = vector_search({"query": "dishwasher leaking repair", ...})
part_name = vector_response[0]["metadata"]["part_name"]

# Step 2: Get part details
sql_response = sql_search(f"SELECT * FROM parts WHERE part_name ILIKE '%{part_name}%'")
```

### Pattern 2: Sequential (SQL → Vector)
**Use Case:** User has part, needs installation
```python
# Step 1: Get part info
sql_response = sql_search("SELECT * FROM parts WHERE part_number = 'PS11752778'")
part_name = sql_response[0]["part_name"]

# Step 2: Get installation guide
vector_response = vector_search({"query": f"{part_name} installation", ...})
```

### Pattern 3: Parallel (Both Tools)
**Use Case:** User asks about compatibility + repair
```python
# Call both simultaneously
sql_response = sql_search("SELECT * FROM part_model_mapping WHERE model = '...'")
vector_response = vector_search({"query": "repair guide for...", ...})
```

---

## Models & Configuration

**LLM (Agent):**
- Primary: DeepSeek R1 (cost-effective, powerful reasoning)
- Fallback: OpenAI GPT-4 Turbo
- Temperature: 0.1 (deterministic, factual responses)

**Embeddings (Vector DB):**
- Model: OpenAI text-embedding-3-small
- Dimension: 1536
- Used for semantic search in ChromaDB

**Agent Configuration:**
```python
agent = create_react_agent(
    llm=llm,
    tools=[sql_search_tool, vector_search_tool],
    max_iterations=10,      # Prevent infinite loops
    early_stopping_method="generate",  # Agent decides when to stop
    handle_parsing_errors=True
)
```

---

## Implementation Checklist

**Phase 1: Tool Setup**
- [x] SQL tool description with field documentation
- [x] Vector DB tool description with metadata schema
- [ ] Implement SQL search tool function
- [ ] Implement Vector DB search tool function
- [ ] Test tools independently

**Phase 2: Agent Setup**
- [ ] Create agent system prompt
- [ ] Configure LangChain ReAct agent
- [ ] Add tool descriptions to agent
- [ ] Implement tool calling logic

**Phase 3: Validation**
- [ ] Implement Pydantic validation for Vector DB tool
- [ ] Add scope enforcement in system prompt
- [ ] Test with 20 example question types
- [ ] Verify tool combination patterns work

**Phase 4: Integration**
- [ ] Connect to PostgreSQL database
- [ ] Set up ChromaDB collection
- [ ] Load vector documents with metadata
- [ ] Test end-to-end agent flow

---

## Example Agent Execution

**User Query:** "My Whirlpool refrigerator ice maker isn't working. What part do I need and how much does it cost?"

**Agent Reasoning:**
```
Thought: User has ice maker issue - need repair guide first
Action: Use vector_search_tool
Action Input: {"query": "refrigerator ice maker not working repair", "document_type": "repair", "appliance_type": "refrigerator", "top_k": 5}
```

**Tool Response:**
```json
{
  "content": "The ice maker assembly controls ice production...",
  "metadata": {
    "part_name": "Ice Maker Assembly",
    "part_id": "IceMaker",
    "category": "Ice maker not working"
  }
}
```

**Agent Reasoning:**
```
Thought: Found likely part. Now need pricing and compatibility.
Action: Use sql_search_tool
Action Input: "SELECT * FROM parts WHERE part_name ILIKE '%ice maker assembly%' AND appliance_type = 'refrigerator' AND brand = 'Whirlpool' ORDER BY rating DESC LIMIT 5"
```

**Tool Response:**
```json
[
  {
    "part_id": "PS11752158",
    "part_name": "Ice Maker Assembly",
    "brand": "Whirlpool",
    "current_price": 189.99,
    "rating": 4.8,
    "availability": "In Stock"
  }
]
```

**Agent Reasoning:**
```
Thought: Have repair guide and part details. Sufficient to answer.
Final Answer: Your ice maker issue is likely the Ice Maker Assembly...
[repair instructions] + [part details with pricing]
```

---

## Key Design Decisions

1. **Why autonomous agent?**
   - User queries vary widely - agent adapts better than fixed routing
   - Can handle complex multi-step queries
   - Learns optimal tool selection patterns

2. **Why 2 tools instead of 1?**
   - Clear separation: structured (SQL) vs unstructured (Vector DB)
   - Different query patterns (SQL syntax vs semantic search)
   - Better performance and cost optimization

3. **Why no external stopping mechanism?**
   - Agent has full context to determine sufficiency
   - More flexible than fixed iteration limits
   - Can handle simple (1 tool) and complex (5+ tools) queries

4. **Why Pydantic only for Vector DB?**
   - SQL tool needs flexibility for complex queries
   - Vector DB has simple, fixed schema
   - Field descriptions guide SQL query construction

5. **Why ChromaDB over Pinecone?**
   - Local deployment, no external dependencies
   - Free and open-source
   - Sufficient for ~700 documents
   - Easy to set up and test

---

## Success Metrics

**Agent Performance:**
- Correctly selects appropriate tool(s) for query type
- Minimal unnecessary tool calls (< 2 redundant calls per query)
- Accurate final answers (>90% accuracy on test queries)
- Completes within 5 tool calls for 95% of queries

**Tool Performance:**
- SQL tool: <100ms query execution
- Vector DB tool: <200ms semantic search
- Relevance score >0.7 for top results

**User Experience:**
- Answers complete and accurate
- Response time <5 seconds for simple queries
- Response time <10 seconds for complex queries
- Handles all 20 question types from assessment
