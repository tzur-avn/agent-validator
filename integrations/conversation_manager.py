"""Conversation state manager for multi-turn Slack conversations."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manage conversation state for Slack users."""

    def __init__(self, timeout_minutes: int = 30):
        """
        Initialize conversation manager.

        Args:
            timeout_minutes: Minutes before a conversation times out
        """
        self.conversations: Dict[str, Dict[str, Any]] = {}
        self.timeout_minutes = timeout_minutes
        logger.info(
            f"ConversationManager initialized with {timeout_minutes}min timeout"
        )

    def start_conversation(
        self, user_id: str, agent_name: str, step: str = "url", **kwargs
    ) -> Dict[str, Any]:
        """
        Start a new conversation.

        Args:
            user_id: Slack user ID
            agent_name: Name of the agent
            step: Current conversation step
            **kwargs: Additional conversation data

        Returns:
            Conversation state
        """
        conversation = {
            "user_id": user_id,
            "agent_name": agent_name,
            "step": step,
            "started_at": datetime.now(),
            "last_activity": datetime.now(),
            "data": kwargs,
        }

        self.conversations[user_id] = conversation
        logger.info(f"Started conversation for user {user_id} with agent {agent_name}")

        return conversation

    def get_conversation(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get active conversation for a user.

        Args:
            user_id: Slack user ID

        Returns:
            Conversation state or None if not found/expired
        """
        conversation = self.conversations.get(user_id)

        if not conversation:
            return None

        # Check if conversation has timed out
        last_activity = conversation.get("last_activity")
        if last_activity:
            timeout = timedelta(minutes=self.timeout_minutes)
            if datetime.now() - last_activity > timeout:
                logger.info(f"Conversation for user {user_id} timed out")
                self.end_conversation(user_id)
                return None

        # Update last activity
        conversation["last_activity"] = datetime.now()

        return conversation

    def update_conversation(
        self, user_id: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update conversation data.

        Args:
            user_id: Slack user ID
            data: Data to merge into conversation

        Returns:
            Updated conversation or None if not found
        """
        conversation = self.get_conversation(user_id)

        if not conversation:
            logger.warning(
                f"Cannot update conversation: user {user_id} has no active conversation"
            )
            return None

        # Merge data
        conversation["data"].update(data)
        conversation["last_activity"] = datetime.now()

        logger.debug(f"Updated conversation for user {user_id}: {data.keys()}")

        return conversation

    def update_step(self, user_id: str, step: str) -> Optional[Dict[str, Any]]:
        """
        Update conversation step.

        Args:
            user_id: Slack user ID
            step: New step

        Returns:
            Updated conversation or None if not found
        """
        conversation = self.get_conversation(user_id)

        if not conversation:
            return None

        conversation["step"] = step
        conversation["last_activity"] = datetime.now()

        logger.debug(f"Updated conversation step for user {user_id} to: {step}")

        return conversation

    def end_conversation(self, user_id: str) -> None:
        """
        End a conversation.

        Args:
            user_id: Slack user ID
        """
        if user_id in self.conversations:
            del self.conversations[user_id]
            logger.info(f"Ended conversation for user {user_id}")

    def get_conversation_data(self, user_id: str, key: str, default: Any = None) -> Any:
        """
        Get specific data from conversation.

        Args:
            user_id: Slack user ID
            key: Data key
            default: Default value if not found

        Returns:
            Data value or default
        """
        conversation = self.get_conversation(user_id)

        if not conversation:
            return default

        return conversation.get("data", {}).get(key, default)

    def has_active_conversation(self, user_id: str) -> bool:
        """
        Check if user has an active conversation.

        Args:
            user_id: Slack user ID

        Returns:
            True if active conversation exists
        """
        return self.get_conversation(user_id) is not None

    def cleanup_expired_conversations(self) -> int:
        """
        Clean up expired conversations.

        Returns:
            Number of conversations cleaned up
        """
        timeout = timedelta(minutes=self.timeout_minutes)
        now = datetime.now()

        expired_users = []

        for user_id, conversation in self.conversations.items():
            last_activity = conversation.get("last_activity")
            if last_activity and (now - last_activity > timeout):
                expired_users.append(user_id)

        for user_id in expired_users:
            self.end_conversation(user_id)

        if expired_users:
            logger.info(f"Cleaned up {len(expired_users)} expired conversations")

        return len(expired_users)

    def get_all_conversations(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all active conversations.

        Returns:
            Dictionary of all conversations
        """
        return self.conversations.copy()

    def clear_all_conversations(self) -> None:
        """Clear all conversations."""
        count = len(self.conversations)
        self.conversations.clear()
        logger.info(f"Cleared all {count} conversations")
