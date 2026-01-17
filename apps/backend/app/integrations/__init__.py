"""
Sponsor Track Integrations

All integrations are optional sidecars that do not gate correctness or demo viability.
If any sponsor API fails, the core system remains fully functional.
"""

from .base import IntegrationBase, IntegrationStatus

__all__ = [
    "IntegrationBase",
    "IntegrationStatus",
]
