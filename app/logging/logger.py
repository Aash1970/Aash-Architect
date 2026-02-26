"""
Structured Logger — Production Grade
JSON-formatted structured logging for all platform events.
Supports stdout (development) and file output (production).
No UI dependencies. No Streamlit imports.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


# ── Log levels ────────────────────────────────────────────────────────────────
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.environ.get("LOG_FORMAT", "json")   # "json" | "text"
LOG_FILE = os.environ.get("LOG_FILE", "")            # empty = stdout only


class _JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # Merge any extra fields attached to the record
        for key, value in record.__dict__.items():
            if key.startswith("_") or key in {
                "name", "msg", "args", "levelname", "levelno",
                "pathname", "filename", "module", "exc_info",
                "exc_text", "stack_info", "lineno", "funcName",
                "created", "msecs", "relativeCreated", "thread",
                "threadName", "processName", "process", "message",
            }:
                continue
            payload[key] = value

        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def _build_logger(name: str) -> logging.Logger:
    """Creates and configures a named logger."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # Already configured

    level = getattr(logging, LOG_LEVEL, logging.INFO)
    logger.setLevel(level)

    handler: logging.Handler = logging.StreamHandler(sys.stdout)
    if LOG_FORMAT == "json":
        handler.setFormatter(_JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s — %(message)s")
        )
    logger.addHandler(handler)

    if LOG_FILE:
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(_JSONFormatter())
        logger.addHandler(file_handler)

    logger.propagate = False
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Returns a structured logger for the given module name.

    Usage:
        log = get_logger(__name__)
        log.info("CV created", extra={"cv_id": cv_id, "user_id": uid})
    """
    return _build_logger(f"career_architect.{name}")


def log_event(
    event: str,
    level: str = "info",
    **fields: Any,
) -> None:
    """
    Convenience function for fire-and-forget structured event logging.

    Args:
        event:   Semantic event name (e.g. "cv.created", "auth.login_failed")
        level:   Log level string ("debug"|"info"|"warning"|"error"|"critical")
        **fields: Arbitrary key-value pairs to attach to the log record
    """
    logger = get_logger("events")
    log_fn = getattr(logger, level.lower(), logger.info)
    log_fn(event, extra={"event": event, **fields})


# ── Audit Logger ─────────────────────────────────────────────────────────────

class AuditLogger:
    """
    Immutable audit trail for sensitive operations.
    All writes produce a structured JSON log entry that must never be deleted.

    Covers:
      - Auth events (login, logout, register, password change)
      - Permission denials
      - Tier gate events
      - Data exports
      - Data deletions
      - Consent changes
      - Admin operations
    """

    _logger = get_logger("audit")

    @classmethod
    def auth_login(cls, user_id: str, email: str, success: bool, ip: str = "") -> None:
        cls._logger.info(
            "auth.login",
            extra={
                "event": "auth.login",
                "user_id": user_id,
                "email": email,
                "success": success,
                "ip": ip,
            },
        )

    @classmethod
    def auth_register(cls, user_id: str, email: str, role: str, tier: str) -> None:
        cls._logger.info(
            "auth.register",
            extra={
                "event": "auth.register",
                "user_id": user_id,
                "email": email,
                "role": role,
                "tier": tier,
            },
        )

    @classmethod
    def auth_logout(cls, user_id: str) -> None:
        cls._logger.info(
            "auth.logout",
            extra={"event": "auth.logout", "user_id": user_id},
        )

    @classmethod
    def permission_denied(cls, user_id: str, role: str, permission: str, resource: str = "") -> None:
        cls._logger.warning(
            "auth.permission_denied",
            extra={
                "event": "auth.permission_denied",
                "user_id": user_id,
                "role": role,
                "permission": permission,
                "resource": resource,
            },
        )

    @classmethod
    def tier_gate(cls, user_id: str, tier: str, feature: str, required_tier: str) -> None:
        cls._logger.warning(
            "tier.gate_blocked",
            extra={
                "event": "tier.gate_blocked",
                "user_id": user_id,
                "tier": tier,
                "feature": feature,
                "required_tier": required_tier,
            },
        )

    @classmethod
    def cv_created(cls, user_id: str, cv_id: str, tier: str) -> None:
        cls._logger.info(
            "cv.created",
            extra={
                "event": "cv.created",
                "user_id": user_id,
                "cv_id": cv_id,
                "tier": tier,
            },
        )

    @classmethod
    def cv_exported(cls, user_id: str, cv_id: str, fmt: str, checksum: str) -> None:
        cls._logger.info(
            "cv.exported",
            extra={
                "event": "cv.exported",
                "user_id": user_id,
                "cv_id": cv_id,
                "format": fmt,
                "checksum": checksum,
            },
        )

    @classmethod
    def cv_deleted(cls, user_id: str, cv_id: str, hard: bool = False) -> None:
        cls._logger.info(
            "cv.deleted",
            extra={
                "event": "cv.deleted",
                "user_id": user_id,
                "cv_id": cv_id,
                "hard_delete": hard,
            },
        )

    @classmethod
    def gdpr_erasure_requested(cls, user_id: str, requester_id: str) -> None:
        cls._logger.warning(
            "gdpr.erasure_requested",
            extra={
                "event": "gdpr.erasure_requested",
                "user_id": user_id,
                "requester_id": requester_id,
            },
        )

    @classmethod
    def gdpr_erasure_completed(cls, user_id: str, records_deleted: int) -> None:
        cls._logger.warning(
            "gdpr.erasure_completed",
            extra={
                "event": "gdpr.erasure_completed",
                "user_id": user_id,
                "records_deleted": records_deleted,
            },
        )

    @classmethod
    def consent_recorded(cls, user_id: str, level: int, granted: bool) -> None:
        cls._logger.info(
            "gdpr.consent_recorded",
            extra={
                "event": "gdpr.consent_recorded",
                "user_id": user_id,
                "consent_level": level,
                "granted": granted,
            },
        )

    @classmethod
    def admin_action(cls, admin_id: str, action: str, target_id: str, detail: str = "") -> None:
        cls._logger.info(
            "admin.action",
            extra={
                "event": "admin.action",
                "admin_id": admin_id,
                "action": action,
                "target_id": target_id,
                "detail": detail,
            },
        )
