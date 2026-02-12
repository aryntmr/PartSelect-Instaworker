"""
Main execution script for PartSelect agent
Run interactive session or single query
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.agent_config import create_partselect_agent, run_query


def interactive_mode():
    """
    Run agent in interactive mode - user can ask multiple questions.
    Type 'quit' or 'exit' to stop.
    """
    print("=" * 80)
    print("PartSelect Customer Support Agent")
    print("Autonomous ReAct Agent with SQL + Vector Search Tools")
    print("=" * 80)
    print()
    print("Initializing agent...")

    # Create agent - defaults to Claude 3.5 Sonnet
    agent = create_partselect_agent(
        provider="claude",  # Use "claude" or "openai"
        temperature=0.0,
        max_iterations=10,
        verbose=True
    )

    print("✅ Agent ready! (Claude 3.5 Sonnet)")
    print("Type 'quit' or 'exit' to stop.")
    print()
    print("-" * 80)

    while True:
        # Get user input
        try:
            query = input("\nYour question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nExiting...")
            break

        # Check for exit commands
        if query.lower() in ['quit', 'exit', 'q']:
            print("\nExiting...")
            break

        # Skip empty queries
        if not query:
            continue

        print("\n" + "=" * 80)
        print("AGENT PROCESSING...")
        print("=" * 80 + "\n")

        # Run query
        result = run_query(agent, query)

        # Display result
        print("\n" + "=" * 80)
        print("FINAL ANSWER:")
        print("=" * 80)
        print()
        print(result.get("output", "No answer generated"))
        print()

        # Show tool call summary
        tool_calls = result.get("tool_calls", 0)
        if tool_calls > 0:
            print("-" * 80)
            print(f"Tool calls made: {tool_calls}")
            print("-" * 80)

        print()


def single_query_mode(query: str):
    """
    Run agent for a single query and exit.

    Args:
        query: User question
    """
    print("=" * 80)
    print("PartSelect Customer Support Agent")
    print("=" * 80)
    print()
    print(f"Query: {query}")
    print()
    print("Initializing agent...")

    # Create agent - defaults to Claude 3.5 Sonnet
    agent = create_partselect_agent(
        provider="claude",  # Use "claude" or "openai"
        temperature=0.0,
        max_iterations=10,
        verbose=True
    )

    print()
    print("=" * 80)
    print("AGENT PROCESSING...")
    print("=" * 80 + "\n")

    # Run query
    result = run_query(agent, query)

    # Display result
    print("\n" + "=" * 80)
    print("FINAL ANSWER:")
    print("=" * 80)
    print()
    print(result.get("output", "No answer generated"))
    print()

    # Show tool call summary
    tool_calls = result.get("tool_calls", 0)
    if tool_calls > 0:
        print("-" * 80)
        print(f"Tool calls made: {tool_calls}")

        # Extract tool names from messages
        messages = result.get("messages", [])
        tools_used = []
        for msg in messages:
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    if 'name' in tool_call:
                        tools_used.append(tool_call['name'])

        if tools_used:
            for i, tool in enumerate(tools_used, 1):
                print(f"  {i}. {tool}")
        print("-" * 80)
    print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run PartSelect autonomous agent")
    parser.add_argument(
        "-q", "--query",
        type=str,
        help="Single query to run (if not provided, enters interactive mode)"
    )

    args = parser.parse_args()

    if args.query:
        single_query_mode(args.query)
    else:
        interactive_mode()
