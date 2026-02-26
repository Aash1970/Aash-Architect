"""
Autosave Draft Engine — Production Grade
Server-side draft persistence for CV builder.
Drafts are separate from saved CVs — they survive browser reloads.
Drafts are per-user, per-section, keyed by user_id.
No UI dependencies. No Streamlit imports.
"""

from app.drafts.draft_service import DraftService, DraftError

__all__ = ["DraftService", "DraftError"]
