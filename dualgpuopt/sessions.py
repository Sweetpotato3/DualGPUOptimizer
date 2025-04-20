"""
Sessions module for DualGPUOptimizer
Handles chat sessions and message history
"""
import json
import time
import uuid
from pathlib import Path
import logging
from typing import Dict, List, Optional

logger = logging.getLogger("DualGPUOpt.Sessions")

def get_sessions_dir():
    """Get the directory for storing sessions

    Returns:
        Path: Path to the sessions directory
    """
    # Try to use home directory for sessions
    home_dir = Path.home() / ".dualgpuopt" / "sessions"

    # Create directory if it doesn't exist
    try:
        home_dir.mkdir(parents=True, exist_ok=True)
        return home_dir
    except Exception as e:
        logger.warning(f"Failed to create sessions directory in home: {e}")

    # Fallback to current directory if home directory is not accessible
    local_dir = Path("sessions")
    local_dir.mkdir(exist_ok=True)
    return local_dir

def create(title: str = None) -> Dict:
    """Create a new session

    Args:
        title: Optional title for the session

    Returns:
        dict: New session object
    """
    session_id = str(uuid.uuid4())
    timestamp = int(time.time())

    session = {
        "id": session_id,
        "title": title or f"Session {time.strftime('%Y-%m-%d %H:%M')}",
        "created": timestamp,
        "updated": timestamp,
        "messages": []
    }

    # Save the session
    save_session(session)

    logger.info(f"Created new session: {session['title']} ({session_id})")
    return session

def list_sessions() -> List[Dict]:
    """List all available sessions

    Returns:
        list: List of session summaries (without messages)
    """
    sessions_dir = get_sessions_dir()
    sessions = []

    try:
        for file_path in sessions_dir.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    session = json.load(f)
                    # Include summary without messages
                    sessions.append({
                        "id": session["id"],
                        "title": session["title"],
                        "created": session["created"],
                        "updated": session["updated"],
                        "message_count": len(session["messages"])
                    })
            except Exception as e:
                logger.error(f"Error loading session {file_path}: {e}")
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")

    # Sort by updated timestamp (newest first)
    return sorted(sessions, key=lambda s: s["updated"], reverse=True)

def get_session(session_id: str) -> Optional[Dict]:
    """Get a specific session by ID

    Args:
        session_id: ID of the session to get

    Returns:
        dict: Session object or None if not found
    """
    sessions_dir = get_sessions_dir()
    session_path = sessions_dir / f"{session_id}.json"

    try:
        if session_path.exists():
            with open(session_path, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading session {session_id}: {e}")

    return None

def save_session(session: Dict) -> bool:
    """Save a session to disk

    Args:
        session: Session object to save

    Returns:
        bool: True if successful, False otherwise
    """
    sessions_dir = get_sessions_dir()
    session_path = sessions_dir / f"{session['id']}.json"

    try:
        with open(session_path, "w") as f:
            json.dump(session, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving session {session['id']}: {e}")
        return False

def append(session_id: str, content: str, role: str = "assistant") -> bool:
    """Append a message to a session

    Args:
        session_id: ID of the session to append to
        content: Message content
        role: Message role (user, assistant, system)

    Returns:
        bool: True if successful, False otherwise
    """
    session = get_session(session_id)

    if not session:
        logger.error(f"Session {session_id} not found")
        return False

    # Add message
    message = {
        "role": role,
        "content": content,
        "timestamp": int(time.time())
    }

    session["messages"].append(message)
    session["updated"] = int(time.time())

    # Save updated session
    return save_session(session)

def delete_session(session_id: str) -> bool:
    """Delete a session

    Args:
        session_id: ID of the session to delete

    Returns:
        bool: True if successful, False otherwise
    """
    sessions_dir = get_sessions_dir()
    session_path = sessions_dir / f"{session_id}.json"

    try:
        if session_path.exists():
            session_path.unlink()
            logger.info(f"Deleted session {session_id}")
            return True
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}")

    return False