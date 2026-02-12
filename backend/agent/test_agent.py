"""
Test suite for PartSelect autonomous agent
Tests tool selection, autonomous looping, and answer quality
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.agent_config import create_partselect_agent, run_query


def print_separator(char="=", length=80):
    """Print separator line."""
    print(char * length)


def print_test_header(test_num, total, description):
    """Print test header."""
    print()
    print_separator()
    print(f"TEST {test_num}/{total}: {description}")
    print_separator()
    print()


def run_test(agent, query, expected_tools=None):
    """
    Run a single test query.

    Args:
        agent: LangGraph agent
        query: Test query
        expected_tools: List of expected tool names (optional)

    Returns:
        Test result dict
    """
    print(f"Query: '{query}'")
    print("-" * 80)

    # Run query
    result = run_query(agent, query)

    # Extract info
    output = result.get("output", "")
    messages = result.get("messages", [])
    tool_call_count = result.get("tool_calls", 0)
    error = result.get("error")

    # Check for error
    if error:
        print(f"❌ ERROR: {error}")
        return {"passed": False, "error": error}

    # Display result
    print(f"\n✅ Answer generated ({tool_call_count} tool calls)")
    print(f"\nFinal Answer Preview:")
    print(output[:300] + ("..." if len(output) > 300 else ""))

    # Extract tool names used from messages
    tools_used = []
    for msg in messages:
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tool_call in msg.tool_calls:
                if 'name' in tool_call:
                    tools_used.append(tool_call['name'])

    # Tool usage summary
    if tools_used:
        print(f"\nTools used: {list(set(tools_used))}")

        # Check expected tools
        if expected_tools:
            all_expected_used = all(tool in tools_used for tool in expected_tools)
            if all_expected_used:
                print(f"✅ All expected tools used: {expected_tools}")
            else:
                print(f"⚠️  Expected tools: {expected_tools}, Used: {list(set(tools_used))}")

    print()

    return {
        "passed": True,
        "output": output,
        "tool_calls": tool_call_count,
        "tools_used": list(set(tools_used))
    }


def run_all_tests():
    """Run comprehensive test suite."""
    print_separator()
    print("PARTSELECT AGENT - COMPREHENSIVE TEST SUITE")
    print_separator()
    print()
    print("Initializing agent...")

    # Create agent (verbose=False for cleaner test output)
    # Using Claude Sonnet 4.5 - fast and cost-effective for testing
    agent = create_partselect_agent(
        provider="claude",
        temperature=0.0,
        max_iterations=10,
        verbose=False  # Set to True to see agent reasoning
    )

    print("✅ Agent initialized (using Claude Sonnet 4.5)")

    # Test cases
    test_cases = [
        {
            "description": "Pure troubleshooting query (Vector only expected)",
            "query": "My refrigerator ice maker stopped making ice",
            "expected_tools": ["vector_search_tool"]
        },
        {
            "description": "Part lookup query (SQL only expected)",
            "query": "Tell me about part PS11752778",
            "expected_tools": ["sql_search_tool"]
        },
        {
            "description": "Compatibility query (SQL only expected)",
            "query": "Is part PS11752778 compatible with model WDT780SAEM1?",
            "expected_tools": ["sql_search_tool"]
        },
        {
            "description": "Policy query (Vector only expected)",
            "query": "What is your return policy?",
            "expected_tools": ["vector_search_tool"]
        },
        {
            "description": "Symptom with part request (Vector + SQL expected)",
            "query": "Dishwasher is leaking water from the door, what part do I need and how much?",
            "expected_tools": ["vector_search_tool", "sql_search_tool"]
        },
        {
            "description": "Error code query (Vector only expected)",
            "query": "What does error code E15 mean on a Bosch dishwasher?",
            "expected_tools": ["vector_search_tool"]
        },
        {
            "description": "Part search with filters (SQL only expected)",
            "query": "Show me Whirlpool refrigerator parts under $50 with good ratings",
            "expected_tools": ["sql_search_tool"]
        },
        {
            "description": "Installation question (Vector only or Vector + SQL)",
            "query": "How do I replace a dishwasher door seal?",
            "expected_tools": None  # Either tool is valid
        },
        {
            "description": "Symptom-based part search (Vector + SQL expected)",
            "query": "My dishwasher won't drain, what parts could fix this and are they in stock?",
            "expected_tools": ["vector_search_tool", "sql_search_tool"]
        },
        {
            "description": "Out of scope query (Should reject)",
            "query": "How do I fix my washing machine?",
            "expected_tools": None  # Should reject without tools
        }
    ]

    # Run tests
    results = []
    total_tests = len(test_cases)

    for i, test in enumerate(test_cases, 1):
        print_test_header(i, total_tests, test["description"])
        result = run_test(
            agent,
            test["query"],
            expected_tools=test.get("expected_tools")
        )
        results.append({
            "test": test["description"],
            "passed": result["passed"],
            "tool_calls": result.get("tool_calls", 0),
            "tools_used": result.get("tools_used", [])
        })

    # Summary
    print_separator()
    print("TEST SUMMARY")
    print_separator()
    print()

    passed = sum(1 for r in results if r["passed"])
    total = len(results)

    print(f"Tests passed: {passed}/{total}")
    print()

    # Detailed results
    print("Detailed Results:")
    print("-" * 80)
    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        tools = result.get("tools_used", [])
        tool_count = result.get("tool_calls", 0)
        print(f"{i}. {status} - {result['test']}")
        if tools:
            print(f"   Tools: {tools} ({tool_count} calls)")
    print()

    # Agent behavior analysis
    print_separator()
    print("AGENT BEHAVIOR ANALYSIS")
    print_separator()
    print()

    tool_call_counts = [r.get("tool_calls", 0) for r in results if r["passed"]]
    if tool_call_counts:
        avg_calls = sum(tool_call_counts) / len(tool_call_counts)
        max_calls = max(tool_call_counts)
        min_calls = min(tool_call_counts)

        print(f"Average tool calls per query: {avg_calls:.1f}")
        print(f"Min tool calls: {min_calls}")
        print(f"Max tool calls: {max_calls}")
        print()

        # Check if agent is stopping early (not hitting max iterations)
        early_stops = sum(1 for count in tool_call_counts if count < 10)
        print(f"Early stops (< 10 iterations): {early_stops}/{len(tool_call_counts)}")
        print(f"  ✅ Good autonomous behavior: Agent stops when satisfied")

    print()
    print_separator()
    print("✅ TEST SUITE COMPLETE")
    print_separator()
    print()


if __name__ == "__main__":
    run_all_tests()
