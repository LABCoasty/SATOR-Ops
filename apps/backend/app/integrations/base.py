"""
Base classes for sponsor track integrations.

All integrations implement graceful degradation - they return None/no-op
when unavailable rather than failing the core system.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any
from pydantic import BaseModel


class IntegrationStatus(str, Enum):
    """Status of a sponsor integration"""
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"
    NOT_CONFIGURED = "not_configured"


class IntegrationBase(ABC):
    """
    Abstract base class for all sponsor integrations.
    
    Design principle: All integrations are sidecars that do not gate
    correctness or demo viability. If any sponsor API fails, the core
    system remains fully functional.
    """
    
    def __init__(self, enabled: bool = False):
        self._enabled = enabled
        self._status = IntegrationStatus.DISABLED
        self._last_error: str | None = None
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    @property
    def status(self) -> IntegrationStatus:
        return self._status
    
    @property
    def last_error(self) -> str | None:
        return self._last_error
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the integration. Returns True if successful.
        Should set self._status appropriately.
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the integration is healthy and available"""
        pass
    
    def _set_error(self, error: str) -> None:
        """Record an error and update status"""
        self._last_error = error
        self._status = IntegrationStatus.ERROR
    
    def _set_enabled(self) -> None:
        """Mark integration as successfully enabled"""
        self._status = IntegrationStatus.ENABLED
        self._last_error = None


class IntegrationResult(BaseModel):
    """Result wrapper for integration operations"""
    success: bool
    data: Any | None = None
    error: str | None = None
    
    @classmethod
    def ok(cls, data: Any = None) -> "IntegrationResult":
        return cls(success=True, data=data)
    
    @classmethod
    def fail(cls, error: str) -> "IntegrationResult":
        return cls(success=False, error=error)
