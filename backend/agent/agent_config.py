"""
Agent configuration and initialization
Sets up LangGraph ReAct agent with SQL and Vector tools
Supports both OpenAI and Claude/Anthropic models
"""

import sys
from pathlib import Path
from typing import Optional, Literal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

from tools.sql_search_tool import sql_search_tool
from tools.vector_search_tool import vector_search_tool


# System prompt for agent
SYSTEM_PROMPT = """You are a PartSelect customer support agent for refrigerator and dishwasher parts.

Your job: Answer user questions using the available tools. Loop and call tools until you have sufficient information to provide a complete answer.

Instructions:
- Call tools to gather information
- After each tool call, read the response carefully
- Think: Do I have enough information to answer?
  - YES → Provide final answer with sources
  - NO → Make another tool call
- Combine tools when helpful (e.g., repair guide from vector + part details from SQL)
- If results are empty or irrelevant, try different query or different tool
- Max 10 tool calls - use them efficiently
- Cite sources (URLs) in your final answer
- Only refrigerator and dishwasher - reject other appliances

That's it. Start helping users."""


def create_partselect_agent(
    provider: Literal["openai", "anthropic", "claude"] = "claude",
    model_name: Optional[str] = None,
    temperature: float = 0.0,
    max_iterations: int = 10,
    verbose: bool = True,
    api_key: Optional[str] = None
):
    """
    Create and configure the PartSelect autonomous agent using LangGraph.

    Args:
        provider: LLM provider - "openai", "anthropic", or "claude" (default: "claude")
        model_name: Model to use (optional, defaults based on provider)
            - OpenAI: "gpt-4o"
            - Claude/Anthropic: "claude-3-5-sonnet-20241022"
        temperature: Model temperature (default: 0 for deterministic)
        max_iterations: Max tool calls before stopping (default: 10)
        verbose: Print agent reasoning steps (default: True)
        api_key: API key (optional, uses OPENAI_API_KEY or ANTHROPIC_API_KEY env var)

    Returns:
        Configured LangGraph agent ready to handle queries
    """
    # Normalize provider name
    if provider == "claude":
        provider = "anthropic"

    # Set default model names
    if model_name is None:
        if provider == "openai":
            model_name = "gpt-4o"
        elif provider == "anthropic":
            model_name = "claude-sonnet-4-5-20250929"  # Current Claude Sonnet 4.5
        else:
            raise ValueError(f"Unknown provider: {provider}")

    # Initialize LLM based on provider
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        llm_kwargs = {"model": model_name, "temperature": temperature}
        if api_key:
            llm_kwargs["api_key"] = api_key
        llm = ChatOpenAI(**llm_kwargs)

    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        llm_kwargs = {"model": model_name, "temperature": temperature}
        if api_key:
            llm_kwargs["api_key"] = api_key
        llm = ChatAnthropic(**llm_kwargs)

    else:
        raise ValueError(f"Unsupported provider: {provider}. Use 'openai' or 'anthropic'")

    # Tools list
    tools = [sql_search_tool, vector_search_tool]

    # Create ReAct agent with LangGraph
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=SYSTEM_PROMPT  # Changed from state_modifier to prompt
    )

    return agent


def run_query(agent, query: str) -> dict:
    """
    Run a single query through the agent.

    Args:
        agent: Configured LangGraph agent
        query: User question

    Returns:
        Dict with 'output' (final answer) and 'messages' (conversation history)
    """
    try:
        # Run agent with query
        result = agent.invoke(
            {"messages": [HumanMessage(content=query)]},
            config={"recursion_limit": 10}  # Max iterations
        )

        # Extract final answer from messages
        messages = result.get("messages", [])

        # Get the last AI message as the output
        output = ""
        for msg in reversed(messages):
            if hasattr(msg, 'content') and msg.content:
                output = msg.content
                break

        # Count tool calls
        tool_calls = sum(1 for msg in messages if hasattr(msg, 'tool_calls') and msg.tool_calls)

        return {
            "output": output,
            "messages": messages,
            "tool_calls": tool_calls
        }
    except Exception as e:
        return {
            "output": f"Error executing query: {str(e)}",
            "messages": [],
            "tool_calls": 0,
            "error": str(e)
        }
