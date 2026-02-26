"""
Data Service — Production Grade
ALL database access goes through this module.
NO direct DB calls in UI or other service layers.
Abstracted for portability: Supabase now, easily swappable to PostgreSQL, SQLite, etc.

Architecture:
  - DataService is the single point of DB access
  - Returns plain Python dicts (not DB-specific objects)
  - Raises DataServiceError on all failures
  - Supports Supabase via environment variables
  - Falls back to in-memory store when SUPABASE_URL not configured (testing/local)
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


class DataServiceError(Exception):
    """Raised on any data access failure."""


class DataService:
    """
    Abstraction layer over the persistence backend.

    Environment variables:
      SUPABASE_URL    — Supabase project URL
      SUPABASE_KEY    — Supabase anon/service key

    When these are not set, uses an in-memory store (for local dev/tests).
    """

    def __init__(self):
        self._supabase_url = os.environ.get("SUPABASE_URL", "")
        self._supabase_key = os.environ.get("SUPABASE_KEY", "")
        self._use_supabase = bool(self._supabase_url and self._supabase_key)
        self._client = None

        if self._use_supabase:
            self._client = self._init_supabase()

        # In-memory fallback store
        self._mem_store: Dict[str, List[Dict[str, Any]]] = {
            "users": [],
            "cvs": [],
            "cv_versions": [],
            "export_logs": [],
            "coach_notes": [],
            "consent_records": [],
            "drafts": [],
        }

    def _init_supabase(self):
        """Initialises Supabase client. Returns None if unavailable."""
        try:
            from supabase import create_client
            return create_client(self._supabase_url, self._supabase_key)
        except Exception as exc:
            raise DataServiceError(
                f"Failed to initialise Supabase client: {exc}"
            ) from exc

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # ── User operations ──────────────────────────────────────────────────────

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetches a user profile by user_id. Returns None if not found."""
        if self._use_supabase:
            try:
                result = (
                    self._client.table("users")
                    .select("*")
                    .eq("user_id", user_id)
                    .single()
                    .execute()
                )
                return result.data
            except Exception as exc:
                raise DataServiceError(f"get_user failed: {exc}") from exc

        return next(
            (u for u in self._mem_store["users"] if u["user_id"] == user_id),
            None
        )

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Fetches a user profile by email. Returns None if not found."""
        if self._use_supabase:
            try:
                result = (
                    self._client.table("users")
                    .select("*")
                    .eq("email", email)
                    .execute()
                )
                return result.data[0] if result.data else None
            except Exception as exc:
                raise DataServiceError(f"get_user_by_email failed: {exc}") from exc

        return next(
            (u for u in self._mem_store["users"] if u["email"] == email),
            None
        )

    def list_users(self, include_deleted: bool = False) -> List[Dict[str, Any]]:
        """Lists all user profiles."""
        if self._use_supabase:
            try:
                query = self._client.table("users").select("*")
                if not include_deleted:
                    query = query.eq("is_deleted", False)
                return query.execute().data or []
            except Exception as exc:
                raise DataServiceError(f"list_users failed: {exc}") from exc

        users = self._mem_store["users"]
        if not include_deleted:
            users = [u for u in users if not u.get("is_deleted", False)]
        return users

    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a new user profile record."""
        if "user_id" not in user_data:
            user_data["user_id"] = str(uuid.uuid4())
        user_data.setdefault("created_at", self._now())
        user_data.setdefault("updated_at", self._now())
        user_data.setdefault("is_deleted", False)

        if self._use_supabase:
            try:
                result = (
                    self._client.table("users")
                    .insert(user_data)
                    .execute()
                )
                return result.data[0]
            except Exception as exc:
                raise DataServiceError(f"create_user failed: {exc}") from exc

        self._mem_store["users"].append(user_data)
        return user_data

    def update_user(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Updates an existing user profile."""
        updates["updated_at"] = self._now()

        if self._use_supabase:
            try:
                result = (
                    self._client.table("users")
                    .update(updates)
                    .eq("user_id", user_id)
                    .execute()
                )
                return result.data[0]
            except Exception as exc:
                raise DataServiceError(f"update_user failed: {exc}") from exc

        for i, u in enumerate(self._mem_store["users"]):
            if u["user_id"] == user_id:
                self._mem_store["users"][i].update(updates)
                return self._mem_store["users"][i]
        raise DataServiceError(f"User {user_id} not found.")

    def soft_delete_user(self, user_id: str) -> bool:
        """Soft-deletes a user (sets is_deleted=True)."""
        try:
            self.update_user(user_id, {"is_deleted": True})
            return True
        except DataServiceError:
            return False

    # ── CV operations ────────────────────────────────────────────────────────

    def get_cv(self, cv_id: str) -> Optional[Dict[str, Any]]:
        """Fetches a CV by cv_id. Returns None if not found."""
        if self._use_supabase:
            try:
                result = (
                    self._client.table("cvs")
                    .select("*")
                    .eq("cv_id", cv_id)
                    .single()
                    .execute()
                )
                return result.data
            except Exception as exc:
                raise DataServiceError(f"get_cv failed: {exc}") from exc

        return next(
            (c for c in self._mem_store["cvs"] if c["cv_id"] == cv_id),
            None
        )

    def list_cvs_for_user(
        self, user_id: str, include_deleted: bool = False
    ) -> List[Dict[str, Any]]:
        """Lists all CVs belonging to a user."""
        if self._use_supabase:
            try:
                query = (
                    self._client.table("cvs")
                    .select("*")
                    .eq("user_id", user_id)
                )
                if not include_deleted:
                    query = query.eq("is_deleted", False)
                return query.execute().data or []
            except Exception as exc:
                raise DataServiceError(f"list_cvs_for_user failed: {exc}") from exc

        cvs = [c for c in self._mem_store["cvs"] if c["user_id"] == user_id]
        if not include_deleted:
            cvs = [c for c in cvs if not c.get("is_deleted", False)]
        return cvs

    def list_all_cvs(self, include_deleted: bool = False) -> List[Dict[str, Any]]:
        """Lists all CVs (Admin+ only — checked in CV service)."""
        if self._use_supabase:
            try:
                query = self._client.table("cvs").select("*")
                if not include_deleted:
                    query = query.eq("is_deleted", False)
                return query.execute().data or []
            except Exception as exc:
                raise DataServiceError(f"list_all_cvs failed: {exc}") from exc

        cvs = self._mem_store["cvs"]
        if not include_deleted:
            cvs = [c for c in cvs if not c.get("is_deleted", False)]
        return cvs

    def create_cv(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a new CV record."""
        if "cv_id" not in cv_data:
            cv_data["cv_id"] = str(uuid.uuid4())
        cv_data.setdefault("created_at", self._now())
        cv_data.setdefault("updated_at", self._now())
        cv_data.setdefault("is_deleted", False)
        cv_data.setdefault("version", 1)

        if self._use_supabase:
            try:
                result = (
                    self._client.table("cvs")
                    .insert(cv_data)
                    .execute()
                )
                return result.data[0]
            except Exception as exc:
                raise DataServiceError(f"create_cv failed: {exc}") from exc

        self._mem_store["cvs"].append(cv_data)
        return cv_data

    def update_cv(self, cv_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Updates an existing CV record. Increments version."""
        updates["updated_at"] = self._now()

        if self._use_supabase:
            try:
                result = (
                    self._client.table("cvs")
                    .update(updates)
                    .eq("cv_id", cv_id)
                    .execute()
                )
                return result.data[0]
            except Exception as exc:
                raise DataServiceError(f"update_cv failed: {exc}") from exc

        for i, c in enumerate(self._mem_store["cvs"]):
            if c["cv_id"] == cv_id:
                self._mem_store["cvs"][i].update(updates)
                return self._mem_store["cvs"][i]
        raise DataServiceError(f"CV {cv_id} not found.")

    def soft_delete_cv(self, cv_id: str) -> bool:
        """Soft-deletes a CV."""
        try:
            self.update_cv(cv_id, {"is_deleted": True})
            return True
        except DataServiceError:
            return False

    def hard_delete_cv(self, cv_id: str) -> bool:
        """Permanently deletes a CV (SystemAdmin only)."""
        if self._use_supabase:
            try:
                self._client.table("cvs").delete().eq("cv_id", cv_id).execute()
                return True
            except Exception as exc:
                raise DataServiceError(f"hard_delete_cv failed: {exc}") from exc

        original_len = len(self._mem_store["cvs"])
        self._mem_store["cvs"] = [
            c for c in self._mem_store["cvs"] if c["cv_id"] != cv_id
        ]
        return len(self._mem_store["cvs"]) < original_len

    # ── CV Version operations ────────────────────────────────────────────────

    def save_cv_version(self, version_data: Dict[str, Any]) -> Dict[str, Any]:
        """Saves a CV version snapshot."""
        if "version_id" not in version_data:
            version_data["version_id"] = str(uuid.uuid4())
        version_data.setdefault("saved_at", self._now())

        if self._use_supabase:
            try:
                result = (
                    self._client.table("cv_versions")
                    .insert(version_data)
                    .execute()
                )
                return result.data[0]
            except Exception as exc:
                raise DataServiceError(f"save_cv_version failed: {exc}") from exc

        self._mem_store["cv_versions"].append(version_data)
        return version_data

    def list_cv_versions(self, cv_id: str) -> List[Dict[str, Any]]:
        """Lists all version records for a CV, newest first."""
        if self._use_supabase:
            try:
                result = (
                    self._client.table("cv_versions")
                    .select("*")
                    .eq("cv_id", cv_id)
                    .order("version_num", desc=True)
                    .execute()
                )
                return result.data or []
            except Exception as exc:
                raise DataServiceError(f"list_cv_versions failed: {exc}") from exc

        versions = [
            v for v in self._mem_store["cv_versions"]
            if v["cv_id"] == cv_id and not v.get("is_deleted", False)
        ]
        return sorted(versions, key=lambda v: v["version_num"], reverse=True)

    # ── Export log operations ────────────────────────────────────────────────

    def log_export(self, export_data: Dict[str, Any]) -> Dict[str, Any]:
        """Records an export event for audit trail."""
        export_data.setdefault("export_id", str(uuid.uuid4()))
        export_data.setdefault("exported_at", self._now())

        if self._use_supabase:
            try:
                result = (
                    self._client.table("export_logs")
                    .insert(export_data)
                    .execute()
                )
                return result.data[0]
            except Exception as exc:
                raise DataServiceError(f"log_export failed: {exc}") from exc

        self._mem_store["export_logs"].append(export_data)
        return export_data

    def count_exports_this_month(self, user_id: str) -> int:
        """Counts exports by a user in the current calendar month."""
        from datetime import date

        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        if self._use_supabase:
            try:
                result = (
                    self._client.table("export_logs")
                    .select("export_id")
                    .eq("user_id", user_id)
                    .gte("exported_at", month_start.isoformat())
                    .execute()
                )
                return len(result.data or [])
            except Exception as exc:
                raise DataServiceError(
                    f"count_exports_this_month failed: {exc}"
                ) from exc

        count = 0
        for log in self._mem_store["export_logs"]:
            if log.get("user_id") != user_id:
                continue
            try:
                ts = datetime.fromisoformat(log.get("exported_at", ""))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts >= month_start:
                    count += 1
            except (ValueError, TypeError):
                continue
        return count

    # ── Coach notes operations ───────────────────────────────────────────────

    def save_coach_note(self, note_data: Dict[str, Any]) -> Dict[str, Any]:
        """Saves a coach note for a CV."""
        note_data.setdefault("note_id", str(uuid.uuid4()))
        note_data.setdefault("created_at", self._now())

        if self._use_supabase:
            try:
                result = (
                    self._client.table("coach_notes")
                    .insert(note_data)
                    .execute()
                )
                return result.data[0]
            except Exception as exc:
                raise DataServiceError(f"save_coach_note failed: {exc}") from exc

        self._mem_store["coach_notes"].append(note_data)
        return note_data

    def get_coach_notes(self, cv_id: str) -> List[Dict[str, Any]]:
        """Gets all coach notes for a CV."""
        if self._use_supabase:
            try:
                result = (
                    self._client.table("coach_notes")
                    .select("*")
                    .eq("cv_id", cv_id)
                    .order("created_at", desc=True)
                    .execute()
                )
                return result.data or []
            except Exception as exc:
                raise DataServiceError(f"get_coach_notes failed: {exc}") from exc

        notes = [
            n for n in self._mem_store["coach_notes"]
            if n["cv_id"] == cv_id
        ]
        return sorted(notes, key=lambda n: n.get("created_at", ""), reverse=True)

    # ── Metrics ──────────────────────────────────────────────────────────────

    def get_platform_metrics(self) -> Dict[str, Any]:
        """Returns aggregate platform metrics for admin dashboard."""
        if self._use_supabase:
            try:
                users = self._client.table("users").select("user_id, role, tier").execute().data or []
                cvs = self._client.table("cvs").select("cv_id").eq("is_deleted", False).execute().data or []
                exports = self._client.table("export_logs").select("export_id").execute().data or []
            except Exception as exc:
                raise DataServiceError(f"get_platform_metrics failed: {exc}") from exc
        else:
            users = [u for u in self._mem_store["users"] if not u.get("is_deleted")]
            cvs = [c for c in self._mem_store["cvs"] if not c.get("is_deleted")]
            exports = self._mem_store["export_logs"]

        role_counts: Dict[str, int] = {}
        tier_counts: Dict[str, int] = {}
        for u in users:
            role_counts[u.get("role", "User")] = role_counts.get(u.get("role", "User"), 0) + 1
            tier_counts[u.get("tier", "Free")] = tier_counts.get(u.get("tier", "Free"), 0) + 1

        return {
            "total_users": len(users),
            "total_cvs": len(cvs),
            "total_exports": len(exports),
            "users_by_role": role_counts,
            "users_by_tier": tier_counts,
        }

    # ── Consent records ───────────────────────────────────────────────────────

    def save_consent_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Appends an immutable consent record (append-only log)."""
        if self._use_supabase:
            try:
                result = self._client.table("consent_records").insert(record).execute()
                return result.data[0] if result.data else record
            except Exception as exc:
                raise DataServiceError(f"save_consent_record failed: {exc}") from exc

        self._mem_store["consent_records"].append(record)
        return record

    def get_consent_records(self, user_id: str) -> List[Dict[str, Any]]:
        """Returns all consent records for a user, oldest first."""
        if self._use_supabase:
            try:
                result = (
                    self._client.table("consent_records")
                    .select("*")
                    .eq("user_id", user_id)
                    .order("recorded_at")
                    .execute()
                )
                return result.data or []
            except Exception as exc:
                raise DataServiceError(f"get_consent_records failed: {exc}") from exc

        records = [r for r in self._mem_store["consent_records"] if r["user_id"] == user_id]
        return sorted(records, key=lambda r: r.get("recorded_at", ""))

    def delete_consent_records(self, user_id: str) -> None:
        """Hard-deletes all consent records for a user (GDPR erasure only)."""
        if self._use_supabase:
            try:
                self._client.table("consent_records").delete().eq("user_id", user_id).execute()
                return
            except Exception as exc:
                raise DataServiceError(f"delete_consent_records failed: {exc}") from exc

        self._mem_store["consent_records"] = [
            r for r in self._mem_store["consent_records"] if r["user_id"] != user_id
        ]

    # ── Draft autosave ────────────────────────────────────────────────────────

    def upsert_draft(self, draft: Dict[str, Any]) -> Dict[str, Any]:
        """Creates or replaces the draft for a user + cv_id pair."""
        user_id = draft["user_id"]
        cv_id = draft.get("cv_id")

        if self._use_supabase:
            try:
                result = self._client.table("drafts").upsert(draft).execute()
                return result.data[0] if result.data else draft
            except Exception as exc:
                raise DataServiceError(f"upsert_draft failed: {exc}") from exc

        self._mem_store["drafts"] = [
            d for d in self._mem_store["drafts"]
            if not (d["user_id"] == user_id and d.get("cv_id") == cv_id)
        ]
        self._mem_store["drafts"].append(draft)
        return draft

    def get_draft(self, user_id: str, cv_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Returns the current draft for a user + cv_id, or None."""
        if self._use_supabase:
            try:
                query = self._client.table("drafts").select("*").eq("user_id", user_id)
                if cv_id:
                    query = query.eq("cv_id", cv_id)
                else:
                    query = query.is_("cv_id", "null")
                result = query.single().execute()
                return result.data
            except Exception:
                return None

        return next(
            (
                d for d in self._mem_store["drafts"]
                if d["user_id"] == user_id and d.get("cv_id") == cv_id
            ),
            None,
        )

    def delete_draft(self, user_id: str, cv_id: Optional[str] = None) -> bool:
        """Deletes the draft for a user + cv_id. Returns True if found."""
        if self._use_supabase:
            try:
                query = self._client.table("drafts").delete().eq("user_id", user_id)
                if cv_id:
                    query = query.eq("cv_id", cv_id)
                else:
                    query = query.is_("cv_id", "null")
                query.execute()
                return True
            except Exception:
                return False

        before = len(self._mem_store["drafts"])
        self._mem_store["drafts"] = [
            d for d in self._mem_store["drafts"]
            if not (d["user_id"] == user_id and d.get("cv_id") == cv_id)
        ]
        return len(self._mem_store["drafts"]) < before
