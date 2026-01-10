"""
Session Manager for AI Assistant Conversations

Manages in-memory conversation sessions with automatic TTL-based cleanup.
No database persistence - sessions exist only for the duration of the user's active session.
"""

import uuid
import threading
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field


@dataclass
class ConversationMessage:
    """Represents a single message in a conversation."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    visualization: Optional[Dict] = None
    sources: Optional[List[Dict]] = None


@dataclass
class ConversationSession:
    """Represents a conversation session with message history."""
    session_id: str
    user_id: int
    messages: List[ConversationMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)


class SessionManager:
    """
    Manages conversation sessions in-memory with automatic TTL cleanup.

    Features:
    - Thread-safe session storage
    - Automatic cleanup of expired sessions
    - TTL-based expiration (default: 60 minutes)
    """

    def __init__(self, ttl_minutes: int = 60):
        """
        Initialize the session manager.

        Args:
            ttl_minutes: Time-to-live for sessions in minutes (default: 60)
        """
        self.sessions: Dict[str, ConversationSession] = {}
        self.ttl = timedelta(minutes=ttl_minutes)
        self._lock = threading.Lock()
        self._start_cleanup_timer()

    def create_session(self, user_id: int) -> str:
        """
        Create a new conversation session.

        Args:
            user_id: The ID of the user (member.id)

        Returns:
            session_id: UUID of the created session
        """
        session_id = str(uuid.uuid4())
        with self._lock:
            self.sessions[session_id] = ConversationSession(
                session_id=session_id,
                user_id=user_id
            )
        return session_id

    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """
        Retrieve a session by ID and update last_accessed timestamp.

        Args:
            session_id: UUID of the session

        Returns:
            ConversationSession if found, None otherwise
        """
        with self._lock:
            session = self.sessions.get(session_id)
            if session:
                session.last_accessed = datetime.now()
            return session

    def add_message(self, session_id: str, message: ConversationMessage) -> bool:
        """
        Add a message to a session.

        Args:
            session_id: UUID of the session
            message: ConversationMessage to add

        Returns:
            True if message was added, False if session not found
        """
        with self._lock:
            session = self.sessions.get(session_id)
            if session:
                session.messages.append(message)
                session.last_accessed = datetime.now()
                return True
            return False

    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """
        Get conversation history formatted for LLM context.

        Args:
            session_id: UUID of the session

        Returns:
            List of dicts with 'role' and 'content' keys
        """
        session = self.get_session(session_id)
        if not session:
            return []

        return [
            {'role': msg.role, 'content': msg.content}
            for msg in session.messages
        ]

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session manually.

        Args:
            session_id: UUID of the session

        Returns:
            True if session was deleted, False if not found
        """
        with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                return True
            return False

    def get_session_count(self) -> int:
        """Get the total number of active sessions."""
        with self._lock:
            return len(self.sessions)

    def _cleanup_expired(self):
        """Remove expired sessions based on TTL."""
        with self._lock:
            now = datetime.now()
            expired = [
                sid for sid, session in self.sessions.items()
                if now - session.last_accessed > self.ttl
            ]
            for sid in expired:
                del self.sessions[sid]

            if expired:
                print(f"[SessionManager] Cleaned up {len(expired)} expired sessions")

        # Schedule next cleanup
        self._start_cleanup_timer()

    def _start_cleanup_timer(self):
        """Start a timer for the next cleanup cycle (every 5 minutes)."""
        timer = threading.Timer(300.0, self._cleanup_expired)  # 5 minutes
        timer.daemon = True
        timer.start()


# Singleton instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """
    Get the singleton SessionManager instance.

    Returns:
        The global SessionManager instance
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
