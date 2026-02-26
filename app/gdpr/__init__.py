"""
GDPR Compliance Module — Production Grade
Implements:
  - 3-level consent workflow (Essential / Functional / Analytics)
  - Consent audit log
  - Right-to-erasure pipeline
  - Subject-access data export
No UI dependencies. No Streamlit imports.
"""

from app.gdpr.consent import ConsentService, ConsentLevel, ConsentRecord
from app.gdpr.erasure import ErasureService

__all__ = [
    "ConsentService",
    "ConsentLevel",
    "ConsentRecord",
    "ErasureService",
]
