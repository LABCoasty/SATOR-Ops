"""
Replay Engine Module

Reconstructs system belief state at any point in time.
"""

from .state_machine import StateReconstructor, SystemState
from .timeline import TimelineIndexer, TimelineEvent

__all__ = [
    "StateReconstructor",
    "SystemState",
    "TimelineIndexer",
    "TimelineEvent",
]


class ReplayEngine:
    """
    Main replay engine that enables forensic review of past system states.
    
    Replay is a core system capability - it proves the system understands
    causality by reconstructing what was known at time t.
    """
    
    def __init__(self):
        self.state_reconstructor = StateReconstructor()
        self.timeline_indexer = TimelineIndexer()
    
    async def get_state_at_t(self, timestamp_iso: str) -> dict:
        """
        Reconstruct the system belief state at a specific timestamp.
        
        Returns the exact state seen by the operator at that time:
        - Last known telemetry values for all tags
        - Active Trust Scores and fired Reason Codes
        - Any unresolved Contradiction objects
        - Current operational mode (Observe vs Decision)
        """
        return await self.state_reconstructor.reconstruct(timestamp_iso)
    
    async def get_timeline_events(
        self, 
        start_iso: str | None = None, 
        end_iso: str | None = None,
        event_types: list[str] | None = None
    ) -> list[dict]:
        """
        Get indexed timeline events for the frontend scrubber.
        
        Returns markers for alarms, trust drops, and operator actions.
        """
        return await self.timeline_indexer.get_events(
            start_iso=start_iso,
            end_iso=end_iso,
            event_types=event_types
        )
    
    def index_event(self, event: dict) -> None:
        """Index a new event for timeline display"""
        self.timeline_indexer.index(event)
