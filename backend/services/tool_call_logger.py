"""
Tool Call Logger - Tracks tool usage per session
Logs which tools are called, how many times, and parameters
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from uuid import uuid4


class ToolCallLogger:
    """Logger for tracking tool calls per conversation session"""

    def __init__(self, log_dir: str = None):
        """Initialize logger with log directory"""
        if log_dir is None:
            # Default to logs directory in backend
            self.log_dir = Path(__file__).parent.parent / "logs" / "tool_calls"
        else:
            self.log_dir = Path(log_dir)

        # Create logs directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Session tracking
        self.sessions = {}

    def create_session(self, session_id: str = None) -> str:
        """Create a new session for logging"""
        if session_id is None:
            session_id = str(uuid4())

        self.sessions[session_id] = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "messages": []
        }

        return session_id

    def log_message(
        self,
        session_id: str,
        user_message: str,
        agent_response: str,
        messages: List[Any],
        tool_calls_count: int = 0
    ):
        """
        Log a message exchange with tool call details

        Args:
            session_id: Session identifier
            user_message: User's input message
            agent_response: Agent's response
            messages: Full message history from agent (includes tool calls)
            tool_calls_count: Number of tool calls made
        """
        # Create session if it doesn't exist
        if session_id not in self.sessions:
            self.create_session(session_id)

        # Extract tool call details from messages
        tool_calls = self._extract_tool_calls(messages)

        # Create message log entry
        message_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "agent_response": agent_response[:200] + "..." if len(agent_response) > 200 else agent_response,
            "tool_calls_count": tool_calls_count,
            "tool_calls": tool_calls,
            "total_messages_in_conversation": len(messages)
        }

        # Add to session
        self.sessions[session_id]["messages"].append(message_entry)

        # Save to file immediately
        self._save_session(session_id)

    def _extract_tool_calls(self, messages: List[Any]) -> List[Dict[str, Any]]:
        """Extract tool call information from LangChain/LangGraph message history"""
        tool_calls_list = []

        for msg in messages:
            msg_type = type(msg).__name__

            # AIMessage with tool_calls
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    # Handle both dict and object formats
                    if isinstance(tool_call, dict):
                        tool_info = {
                            "tool_name": tool_call.get('name', 'unknown'),
                            "args": tool_call.get('args', {}),
                            "id": tool_call.get('id', ''),
                            "type": "tool_call"
                        }
                    else:
                        # Object format
                        tool_info = {
                            "tool_name": getattr(tool_call, 'name', 'unknown'),
                            "args": getattr(tool_call, 'args', {}),
                            "id": getattr(tool_call, 'id', ''),
                            "type": "tool_call"
                        }
                    tool_calls_list.append(tool_info)

            # ToolMessage (response from tool execution)
            if msg_type == 'ToolMessage' or (hasattr(msg, 'type') and msg.type == 'tool'):
                content_length = len(str(msg.content)) if hasattr(msg, 'content') else 0
                tool_result = {
                    "tool_name": getattr(msg, 'name', 'unknown'),
                    "type": "tool_result",
                    "result_length": content_length,
                    "tool_call_id": getattr(msg, 'tool_call_id', '')
                }

                # Try to match with previous tool call
                for tc in tool_calls_list:
                    if tc.get('type') == 'tool_call' and tc.get('id') == tool_result['tool_call_id']:
                        tc['result_length'] = content_length
                        tc['result_preview'] = str(msg.content)[:200] if hasattr(msg, 'content') else ""
                        break
                else:
                    # No matching call found, add as separate entry
                    tool_calls_list.append(tool_result)

        return tool_calls_list

    def _save_session(self, session_id: str):
        """Save session log to file"""
        if session_id not in self.sessions:
            return

        session_data = self.sessions[session_id]

        # Create filename with session ID and timestamp
        filename = f"session_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.log_dir / filename

        # Save to JSON file
        with open(filepath, 'w') as f:
            json.dump(session_data, f, indent=2)

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary statistics for a session"""
        if session_id not in self.sessions:
            return {}

        session = self.sessions[session_id]
        messages = session["messages"]

        # Calculate statistics
        total_messages = len(messages)
        total_tool_calls = sum(msg["tool_calls_count"] for msg in messages)

        # Count tool usage
        tool_usage = {}
        for msg in messages:
            for tool_call in msg["tool_calls"]:
                tool_name = tool_call["tool_name"]
                tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1

        return {
            "session_id": session_id,
            "total_messages": total_messages,
            "total_tool_calls": total_tool_calls,
            "avg_tool_calls_per_message": total_tool_calls / total_messages if total_messages > 0 else 0,
            "tool_usage": tool_usage,
            "created_at": session["created_at"]
        }

    def end_session(self, session_id: str):
        """End a session and save final log"""
        if session_id in self.sessions:
            # Add summary to session
            self.sessions[session_id]["summary"] = self.get_session_summary(session_id)
            self.sessions[session_id]["ended_at"] = datetime.now().isoformat()

            # Save final version
            self._save_session(session_id)

            # Remove from active sessions
            del self.sessions[session_id]


# Global logger instance
_logger = None

def get_logger() -> ToolCallLogger:
    """Get or create global logger instance"""
    global _logger
    if _logger is None:
        _logger = ToolCallLogger()
    return _logger
