"""
Base Agent Class

Defines the base class for all autonomous agents in the system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import logging


@dataclass
class AgentMessage:
    """Message passed between agents."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = ""
    receiver: str = ""
    message_type: str = ""
    content: Any = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentState:
    """Agent state information."""
    status: str = "idle"  # idle, working, waiting, error
    current_task: Optional[str] = None
    last_action: Optional[str] = None
    last_action_time: Optional[datetime] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """
    Base class for all autonomous agents.

    Agents are self-contained units that can:
    - Receive and process messages
    - Make autonomous decisions
    - Perform actions
    - Report status and results
    """

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        config: Dict[str, Any] = None
    ):
        """
        Initialize the agent.

        Args:
            agent_id: Unique identifier for the agent
            agent_type: Type of agent (monitor, diagnostic, repair, etc.)
            config: Agent configuration
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.config = config or {}

        self.state = AgentState()
        self.mailbox: List[AgentMessage] = []
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")

        self._initialize()

    def _initialize(self) -> None:
        """Initialize agent-specific resources."""
        self.logger.info(f"Agent {self.agent_id} ({self.agent_type}) initialized")

    @abstractmethod
    def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """
        Process a received message.

        Args:
            message: Message to process

        Returns:
            Response message (if any)
        """
        pass

    @abstractmethod
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task.

        Args:
            task: Task description and parameters

        Returns:
            Task result
        """
        pass

    def receive_message(self, message: AgentMessage) -> None:
        """
        Receive a message and add it to the mailbox.

        Args:
            message: Message to receive
        """
        self.mailbox.append(message)
        self.logger.debug(f"Received message from {message.sender}: {message.message_type}")

    def send_message(
        self,
        receiver: str,
        message_type: str,
        content: Any,
        metadata: Dict[str, Any] = None
    ) -> AgentMessage:
        """
        Send a message to another agent.

        Args:
            receiver: Receiver agent ID
            message_type: Type of message
            content: Message content
            metadata: Additional metadata

        Returns:
            The sent message
        """
        message = AgentMessage(
            sender=self.agent_id,
            receiver=receiver,
            message_type=message_type,
            content=content,
            metadata=metadata or {}
        )

        self.logger.debug(f"Sent message to {receiver}: {message_type}")
        return message

    def process_mailbox(self) -> List[AgentMessage]:
        """
        Process all messages in the mailbox.

        Returns:
            List of response messages
        """
        responses = []

        while self.mailbox:
            message = self.mailbox.pop(0)
            try:
                response = self.process_message(message)
                if response:
                    responses.append(response)
            except Exception as e:
                self.logger.error(f"Error processing message: {e}")
                self.state.status = "error"

        return responses

    def update_state(
        self,
        status: Optional[str] = None,
        current_task: Optional[str] = None,
        last_action: Optional[str] = None
    ) -> None:
        """
        Update agent state.

        Args:
            status: New status
            current_task: Current task description
            last_action: Last action performed
        """
        if status:
            self.state.status = status
        if current_task is not None:
            self.state.current_task = current_task
        if last_action:
            self.state.last_action = last_action
            self.state.last_action_time = datetime.now()

    def get_state(self) -> AgentState:
        """
        Get current agent state.

        Returns:
            Current state
        """
        return self.state

    def get_status(self) -> Dict[str, Any]:
        """
        Get agent status report.

        Returns:
            Status dictionary
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": self.state.status,
            "current_task": self.state.current_task,
            "last_action": self.state.last_action,
            "last_action_time": self.state.last_action_time.isoformat() if self.state.last_action_time else None,
            "mailbox_size": len(self.mailbox),
            "metrics": self.state.metrics
        }

    def record_metric(self, name: str, value: Any) -> None:
        """
        Record a metric.

        Args:
            name: Metric name
            value: Metric value
        """
        self.state.metrics[name] = value

    def __repr__(self) -> str:
        return f"{self.agent_type}Agent(id={self.agent_id}, status={self.state.status})"
