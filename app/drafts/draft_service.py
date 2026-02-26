"""
Draft Service — Production Grade
Provides server-side autosave for the CV builder.
Drafts are independent of published CVs.
A user has at most one active draft per CV (or one "new CV" draft).
No UI dependencies. No Streamlit imports.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional


class DraftError(Exception):
    """Raised on draft service operation failures."""


class DraftService:
    """
    Manages autosave drafts for the CV builder.

    A draft is a partial, unvalidated snapshot of CV form data.
    Drafts are stored to the data layer independently of published CVs.
    The UI triggers save_draft() on each meaningful change.

    Draft lifecycle:
      1. User opens CV builder → load_draft() restores last autosave
      2. User types → UI calls save_draft() (debounced)
      3. User clicks Save → CV is validated and published; discard_draft() called
      4. User closes browser → draft persists for next session
    """

    def __init__(self, data_service):
        self._ds = data_service

    def save_draft(
        self,
        user_id: str,
        draft_data: Dict[str, Any],
        cv_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Saves or updates an autosave draft for the given user.

        Args:
            user_id:    Owner of the draft
            draft_data: Partial CV section data from the builder form
            cv_id:      If editing an existing CV, its ID; None for new CV drafts

        Returns:
            Stored draft dict with draft_id and saved_at
        """
        if not user_id:
            raise DraftError("user_id is required to save a draft.")

        existing = self._ds.get_draft(user_id, cv_id)

        draft = {
            "draft_id": existing.get("draft_id", str(uuid.uuid4())) if existing else str(uuid.uuid4()),
            "user_id": user_id,
            "cv_id": cv_id,
            "data": draft_data,
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }

        self._ds.upsert_draft(draft)
        return draft

    def load_draft(
        self,
        user_id: str,
        cv_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Loads the most recent autosave draft for a user.

        Args:
            user_id: Owner of the draft
            cv_id:   CV being edited, or None for new CV drafts

        Returns:
            Draft dict or None if no draft exists
        """
        return self._ds.get_draft(user_id, cv_id)

    def discard_draft(
        self,
        user_id: str,
        cv_id: Optional[str] = None,
    ) -> bool:
        """
        Deletes the autosave draft after a successful CV save.

        Args:
            user_id: Owner of the draft
            cv_id:   CV the draft was for

        Returns:
            True if a draft was found and deleted, False if nothing to delete
        """
        return self._ds.delete_draft(user_id, cv_id)

    def get_draft_age_seconds(
        self,
        user_id: str,
        cv_id: Optional[str] = None,
    ) -> Optional[float]:
        """
        Returns the age of the current draft in seconds, or None if no draft.
        Used by the UI to display "Last autosaved X seconds ago".
        """
        draft = self._ds.get_draft(user_id, cv_id)
        if not draft:
            return None

        saved_at_str = draft.get("saved_at", "")
        if not saved_at_str:
            return None

        try:
            saved_at = datetime.fromisoformat(saved_at_str)
            if saved_at.tzinfo is None:
                saved_at = saved_at.replace(tzinfo=timezone.utc)
            delta = datetime.now(timezone.utc) - saved_at
            return delta.total_seconds()
        except (ValueError, TypeError):
            return None
