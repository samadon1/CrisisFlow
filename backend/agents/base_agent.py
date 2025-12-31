"""
Base Agent Class for CrisisFlow Multi-Agent System
Powered by Google Gemini
"""
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
from enum import Enum

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent operational status"""
    IDLE = "idle"
    ACTIVE = "active"
    WORKING = "working"
    ERROR = "error"
    READY = "ready"


class AgentMessage:
    """Message sent between agents"""
    def __init__(self, sender: str, content: str, priority: str = "normal", data: Optional[Dict] = None):
        self.sender = sender
        self.content = content
        self.priority = priority
        self.data = data or {}
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self):
        return {
            "sender": self.sender,
            "content": self.content,
            "priority": self.priority,
            "data": self.data,
            "timestamp": self.timestamp
        }


class BaseAgent:
    """Base class for all CrisisFlow agents"""

    def __init__(self, agent_id: str, name: str, role: str, gemini_client):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.status = AgentStatus.IDLE
        self.gemini = gemini_client
        self.message_history: List[AgentMessage] = []
        self.created_at = datetime.utcnow()

        logger.info(f"🤖 {self.name} agent initialized - Role: {self.role}")

    def set_status(self, status: AgentStatus):
        """Update agent status"""
        old_status = self.status
        self.status = status
        logger.info(f"🔄 {self.name}: {old_status.value} → {status.value}")

    def send_message(self, content: str, priority: str = "normal", data: Optional[Dict] = None) -> AgentMessage:
        """Send a message to other agents"""
        message = AgentMessage(self.name, content, priority, data)
        self.message_history.append(message)
        return message

    def get_status_display(self) -> str:
        """Get formatted status for UI"""
        status_icons = {
            AgentStatus.IDLE: "⏸️",
            AgentStatus.ACTIVE: "🟢",
            AgentStatus.WORKING: "⚙️",
            AgentStatus.ERROR: "🔴",
            AgentStatus.READY: "✅"
        }
        return f"{status_icons.get(self.status, '⚪')} {self.status.value.upper()}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary for API response"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role,
            "status": self.status.value,
            "status_display": self.get_status_display(),
            "uptime": (datetime.utcnow() - self.created_at).total_seconds(),
            "message_count": len(self.message_history)
        }

    async def analyze(self, data: Any) -> Dict[str, Any]:
        """Main analysis method - override in subclasses"""
        raise NotImplementedError("Subclasses must implement analyze()")

    async def ask_gemini(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """Helper method to query Gemini"""
        try:
            self.set_status(AgentStatus.WORKING)

            # Use system instruction if provided
            full_prompt = prompt
            if system_instruction:
                full_prompt = f"{system_instruction}\n\n{prompt}"

            # Use the GeminiClient's model directly
            import asyncio
            response = await asyncio.to_thread(
                self.gemini.model.generate_content,
                full_prompt
            )

            self.set_status(AgentStatus.ACTIVE)
            return response.text

        except Exception as e:
            logger.error(f"❌ {self.name} Gemini error: {e}")
            self.set_status(AgentStatus.ERROR)
            raise
