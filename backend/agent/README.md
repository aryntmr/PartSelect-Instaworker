# PartSelect Autonomous Agent

Autonomous ReAct agent with SQL and Vector search tools for customer support.

## Quick Start

### Interactive Mode
```bash
python agent/run_agent.py
```

### Single Query
```bash
python agent/run_agent.py -q "My ice maker stopped working"
```

### Run Tests
```bash
python agent/test_agent.py
```

## Architecture

**Pattern:** ReAct (Reasoning + Acting)
- Agent loops until sufficient information gathered
- Max 10 iterations
- Stops early when answer is complete

**Tools:**
1. `sql_search_tool` - Structured part data (pricing, compatibility, specs)
2. `vector_search_tool` - Unstructured content (repair guides, blogs, policies)

**Scope:** Refrigerator and dishwasher only

## Files

- `system_prompt.py` - Agent prompt template
- `agent_config.py` - Agent initialization
- `run_agent.py` - Interactive/single query execution
- `test_agent.py` - Comprehensive test suite

## Usage

```python
from agent import create_partselect_agent, run_query

# Create agent with Claude (default - recommended)
agent = create_partselect_agent(
    provider="claude",
    temperature=0.0,
    max_iterations=10
)

# Or use OpenAI
agent = create_partselect_agent(
    provider="openai",
    model_name="gpt-4o"
)

# Run query
result = run_query(agent, "How do I fix a leaking dishwasher?")
print(result["output"])
```

## Configuration

**Environment Variables:**
- `ANTHROPIC_API_KEY` - For Claude models (default, recommended)
- `OPENAI_API_KEY` - For OpenAI models (alternative)

Get API key: https://console.anthropic.com/
Note: Claude Pro subscription ≠ API access. Purchase API credits separately.

**Agent Parameters:**
- `provider` - "claude" or "openai" (default: "claude")
- `model_name` - Model override (defaults: claude-3-5-sonnet-20241022 or gpt-4o)
- `temperature` - Model temperature (default: 0.0)
- `max_iterations` - Max tool calls (default: 10)
- `verbose` - Print reasoning steps (default: True)

## Examples

**Troubleshooting:**
```
Query: "My refrigerator is not cooling"
Tools: vector_search_tool → repair guides
Result: Troubleshooting steps + common causes
```

**Part Lookup:**
```
Query: "Tell me about part PS11752778"
Tools: sql_search_tool → part details
Result: Price, compatibility, specs, availability
```

**Combined:**
```
Query: "Dishwasher leaking, what part and price?"
Tools: vector_search_tool → repair guide → sql_search_tool → part details
Result: Diagnosis + part options with prices
```
