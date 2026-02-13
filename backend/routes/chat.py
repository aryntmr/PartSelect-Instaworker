"""Chat endpoint for conversational interface."""

from fastapi import APIRouter, HTTPException
from models.chat import ChatRequest, ChatResponse, ChatMetadata
from agent import create_partselect_agent, run_query
from langchain_core.messages import HumanMessage, AIMessage
from services.tool_call_logger import get_logger
from uuid import uuid4


router = APIRouter()

# Initialize agent once at module level (reused for all requests)
agent = create_partselect_agent(
    provider="claude",
    temperature=0.0,
    max_iterations=5,
    verbose=False  # Disable verbose logging for production
)


@router.post(
    "/api/chat",
    response_model=ChatResponse,
    summary="Chat with AI Agent",
    description="Chat with autonomous AI agent. Uses SQL and Vector search tools to answer questions.",
    tags=["Chat"],
    responses={
        200: {
            "description": "Successful AI response",
            "content": {
                "application/json": {
                    "example": {
                        "reply": "Based on my search, here are some ice maker parts...",
                        "metadata": {
                            "type": "agent_response",
                            "count": 0,
                            "products": []
                        }
                    }
                }
            }
        },
        422: {"description": "Validation error - invalid request format"},
        500: {"description": "Internal server error"}
    }
)
def chat(request: ChatRequest):
    """Main chat endpoint - powered by autonomous AI agent with conversation history."""
    try:
        # Get or create session ID
        session_id = request.conversation_id or str(uuid4())

        # Get logger instance
        logger = get_logger()

        # Create session if new
        if session_id not in logger.sessions:
            logger.create_session(session_id)

        # Convert conversation history to LangChain message format
        messages = []
        if request.history:
            for msg in request.history:
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    messages.append(AIMessage(content=msg.content))

        # Add current user message
        messages.append(HumanMessage(content=request.message))

        # Run agent with full conversation context
        result = run_query(agent, messages)

        # Extract agent's text response
        agent_response = result.get("output", "I apologize, but I couldn't generate a response. Please try again.")

        # Get full message history with tool calls
        full_messages = result.get("messages", [])
        tool_calls_count = result.get("tool_calls", 0)

        # Log this message exchange with tool call details
        logger.log_message(
            session_id=session_id,
            user_message=request.message,
            agent_response=agent_response,
            messages=full_messages,
            tool_calls_count=tool_calls_count
        )

        # Return text-only response
        return ChatResponse(
            reply=agent_response,
            metadata=ChatMetadata(
                type="agent_response",
                count=0,
                products=[]  # No products - text-only mode
            )
        )

    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/api/chat/session/{session_id}/end",
    summary="End Chat Session",
    description="End a chat session and save final tool call logs",
    tags=["Chat"]
)
def end_session(session_id: str):
    """End a chat session and save tool call logs"""
    try:
        logger = get_logger()
        logger.end_session(session_id)
        return {"message": f"Session {session_id} ended and logs saved", "session_id": session_id}
    except Exception as e:
        print(f"Error ending session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to end session")


@router.get(
    "/api/chat/session/{session_id}/summary",
    summary="Get Session Summary",
    description="Get tool call summary for a chat session",
    tags=["Chat"]
)
def get_session_summary(session_id: str):
    """Get summary of tool calls for a session"""
    try:
        logger = get_logger()
        summary = logger.get_session_summary(session_id)
        if not summary:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        return summary
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting session summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get session summary")
