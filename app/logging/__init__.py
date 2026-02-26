"""
Structured Logging — Production Grade
Centralised logging for all service operations.
JSON-formatted structured logs for machine parsing.
No UI dependencies. No Streamlit imports.
"""

from app.logging.logger import get_logger, log_event, AuditLogger

__all__ = ["get_logger", "log_event", "AuditLogger"]
