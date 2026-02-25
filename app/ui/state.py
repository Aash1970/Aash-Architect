"""
UI State Manager — centralises all st.session_state access.
All Streamlit state lives here. Services MUST NOT touch st.session_state.
"""

import streamlit as st
from typing import Optional, Dict, Any


def init_session_state() -> None:
    """Initialises all session state keys with defaults."""
    defaults: Dict[str, Any] = {
        "authenticated": False,
        "user_id": None,
        "user_email": None,
        "user_role": "User",
        "user_tier": "Free",
        "user_name": None,
        "access_token": None,
        "language": "en",
        "current_page": "cv_list",
        "selected_cv_id": None,
        "flash_message": None,
        "flash_type": None,  # "success" | "error" | "warning" | "info"
        "login_attempts": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_user_id() -> Optional[str]:
    return st.session_state.get("user_id")


def get_role() -> str:
    return st.session_state.get("user_role", "User")


def get_tier() -> str:
    return st.session_state.get("user_tier", "Free")


def get_language() -> str:
    return st.session_state.get("language", "en")


def get_access_token() -> Optional[str]:
    return st.session_state.get("access_token")


def is_authenticated() -> bool:
    return bool(st.session_state.get("authenticated", False))


def set_authenticated_user(
    user_id: str,
    email: str,
    role: str,
    tier: str,
    name: str,
    access_token: str,
    language: str = "en",
) -> None:
    """Sets all session fields for an authenticated user."""
    st.session_state["authenticated"] = True
    st.session_state["user_id"] = user_id
    st.session_state["user_email"] = email
    st.session_state["user_role"] = role
    st.session_state["user_tier"] = tier
    st.session_state["user_name"] = name
    st.session_state["access_token"] = access_token
    st.session_state["language"] = language
    st.session_state["login_attempts"] = 0


def clear_session() -> None:
    """Clears all session data (logout)."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_session_state()


def set_flash(message: str, flash_type: str = "info") -> None:
    """Sets a one-time flash message for display."""
    st.session_state["flash_message"] = message
    st.session_state["flash_type"] = flash_type


def consume_flash() -> Optional[Dict[str, str]]:
    """Reads and clears the flash message."""
    msg = st.session_state.get("flash_message")
    flash_type = st.session_state.get("flash_type", "info")
    if msg:
        st.session_state["flash_message"] = None
        st.session_state["flash_type"] = None
        return {"message": msg, "type": flash_type}
    return None


def navigate_to(page: str, cv_id: Optional[str] = None) -> None:
    """Sets the current page and optional CV context."""
    st.session_state["current_page"] = page
    if cv_id is not None:
        st.session_state["selected_cv_id"] = cv_id
