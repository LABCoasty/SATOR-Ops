"""
Database Module

MongoDB Atlas connection and data management.
"""

from .connection import MongoDBConnection, get_db
from .repository import (
    TelemetryRepository,
    AuditRepository,
    IncidentRepository,
    SimulationRepository,
)

__all__ = [
    "MongoDBConnection",
    "get_db",
    "TelemetryRepository",
    "AuditRepository",
    "IncidentRepository",
    "SimulationRepository",
]
