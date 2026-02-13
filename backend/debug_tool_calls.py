#!/usr/bin/env python3
"""
Debug script to see actual message structure from LangGraph agent
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from agent import create_partselect_agent, run_query
from langchain_core.messages import HumanMessage
import json

# Create agent with more iterations
agent = create_partselect_agent(
    provider="claude",
    temperature=0.0,
    max_iterations=7,
    verbose=True
)

# Simple query that should work
messages = [HumanMessage(content="What's your return policy?")]

print("\n" + "="*60)
print("RUNNING SIMPLE QUERY")
print("="*60 + "\n")

result = run_query(agent, messages)

print("\n" + "="*60)
print("FULL RESULT")
print("="*60 + "\n")

print(json.dumps({
    "output": result.get("output", "")[:200],
    "tool_calls_count": result.get("tool_calls", 0),
    "message_count": len(result.get("messages", [])),
    "has_error": "error" in result
}, indent=2))

if "error" in result:
    print(f"\nError: {result['error']}")

print("\n" + "="*60)
print("INSPECTING MESSAGES")
print("="*60 + "\n")

for i, msg in enumerate(result.get("messages", [])):
    print(f"\n--- Message {i} ---")
    print(f"Type: {type(msg).__name__}")

    # Print all attributes
    attrs = [attr for attr in dir(msg) if not attr.startswith('_')]
    print(f"Attributes: {attrs[:10]}...")  # First 10 attrs

    # Check specific attributes
    if hasattr(msg, 'type'):
        print(f"type: {msg.type}")

    if hasattr(msg, 'content'):
        content_preview = str(msg.content)[:150] if msg.content else "None"
        print(f"content: {content_preview}...")

    if hasattr(msg, 'tool_calls') and msg.tool_calls:
        print(f"tool_calls: {msg.tool_calls}")

    if hasattr(msg, 'name'):
        print(f"name: {msg.name}")
