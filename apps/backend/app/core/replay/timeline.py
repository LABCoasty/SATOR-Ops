"""
Timeline Indexer Module

Indexes events by timestamp for the frontend scrubber.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from dataclasses import dataclass, field, asdict
from enum import Enum

from config import config


class TimelineEventType(str, Enum):
    """Types of events that appear on the timeline"""
    ALARM = "alarm"
    TRUST_DROP = "trust_drop"
    TRUST_RECOVERY = "trust_recovery"
    CONTRADICTION_DETECTED = "contradiction_detected"
    CONTRADICTION_RESOLVED = "contradiction_resolved"
    MODE_TRANSITION = "mode_transition"
    OPERATOR_ACTION = "operator_action"
    FAILURE_INJECTED = "failure_injected"
    SIMULATION_START = "simulation_start"
    SIMULATION_END = "simulation_end"


class EventSeverity(str, Enum):
    """Severity levels for timeline events"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class TimelineEvent:
    """A single event on the timeline"""
    event_id: str
    timestamp: datetime
    event_type: TimelineEventType
    severity: EventSeverity
    summary: str
    details: dict = field(default_factory=dict)
    related_tags: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "summary": self.summary,
            "details": self.details,
            "related_tags": self.related_tags,
        }


class TimelineIndexer:
    """
    Indexes events by timestamp for the frontend timeline scrubber.
    
    Provides fast access to events within time ranges and filtering
    by event type.
    """
    
    def __init__(self):
        self._events: list[TimelineEvent] = []
        self._event_counter = 0
        self._data_path = Path(config.data_dir) / "events"
    
    def _generate_event_id(self) -> str:
        """Generate a unique event ID"""
        self._event_counter += 1
        return f"evt_{self._event_counter:06d}"
    
    def index(self, event: dict | TimelineEvent) -> str:
        """
        Index a new event.
        
        Returns the event ID.
        """
        if isinstance(event, dict):
            # Convert dict to TimelineEvent
            event_id = event.get("event_id") or self._generate_event_id()
            timeline_event = TimelineEvent(
                event_id=event_id,
                timestamp=self._parse_timestamp(event.get("timestamp", datetime.utcnow())),
                event_type=TimelineEventType(event.get("event_type", "alarm")),
                severity=EventSeverity(event.get("severity", "info")),
                summary=event.get("summary", ""),
                details=event.get("details", {}),
                related_tags=event.get("related_tags", []),
            )
        else:
            timeline_event = event
        
        # Insert in sorted order
        self._insert_sorted(timeline_event)
        
        return timeline_event.event_id
    
    def _parse_timestamp(self, ts: Any) -> datetime:
        """Parse various timestamp formats"""
        if isinstance(ts, datetime):
            return ts
        if isinstance(ts, str):
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return datetime.utcnow()
    
    def _insert_sorted(self, event: TimelineEvent) -> None:
        """Insert event maintaining chronological order"""
        # Binary search for insertion point
        lo, hi = 0, len(self._events)
        while lo < hi:
            mid = (lo + hi) // 2
            if self._events[mid].timestamp < event.timestamp:
                lo = mid + 1
            else:
                hi = mid
        self._events.insert(lo, event)
    
    async def get_events(
        self,
        start_iso: str | None = None,
        end_iso: str | None = None,
        event_types: list[str] | None = None,
        severity: str | None = None,
        tag_id: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """
        Get timeline events with optional filtering.
        
        Args:
            start_iso: Start timestamp (inclusive)
            end_iso: End timestamp (exclusive)
            event_types: Filter by event types
            severity: Filter by severity
            tag_id: Filter by related tag
            limit: Maximum events to return
            
        Returns:
            List of event dictionaries
        """
        result = []
        
        # Parse time bounds
        start_time = self._parse_timestamp(start_iso) if start_iso else None
        end_time = self._parse_timestamp(end_iso) if end_iso else None
        
        # Convert event types filter
        type_filter = None
        if event_types:
            type_filter = set(TimelineEventType(t) for t in event_types)
        
        # Filter events
        for event in self._events:
            # Time bounds
            if start_time and event.timestamp < start_time:
                continue
            if end_time and event.timestamp >= end_time:
                break  # Events are sorted, so we can stop here
            
            # Type filter
            if type_filter and event.event_type not in type_filter:
                continue
            
            # Severity filter
            if severity and event.severity.value != severity:
                continue
            
            # Tag filter
            if tag_id and tag_id not in event.related_tags:
                continue
            
            result.append(event.to_dict())
            
            if len(result) >= limit:
                break
        
        return result
    
    def get_event_markers(
        self,
        start_iso: str | None = None,
        end_iso: str | None = None,
    ) -> list[dict]:
        """
        Get simplified event markers for the timeline scrubber.
        
        Returns minimal data for rendering markers on the timeline.
        """
        start_time = self._parse_timestamp(start_iso) if start_iso else None
        end_time = self._parse_timestamp(end_iso) if end_iso else None
        
        markers = []
        for event in self._events:
            if start_time and event.timestamp < start_time:
                continue
            if end_time and event.timestamp >= end_time:
                break
            
            markers.append({
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type.value,
                "severity": event.severity.value,
            })
        
        return markers
    
    def get_event_by_id(self, event_id: str) -> dict | None:
        """Get a specific event by ID"""
        for event in self._events:
            if event.event_id == event_id:
                return event.to_dict()
        return None
    
    def clear(self) -> None:
        """Clear all indexed events"""
        self._events.clear()
        self._event_counter = 0
    
    def get_stats(self) -> dict:
        """Get timeline statistics"""
        type_counts = {}
        severity_counts = {}
        
        for event in self._events:
            type_counts[event.event_type.value] = type_counts.get(event.event_type.value, 0) + 1
            severity_counts[event.severity.value] = severity_counts.get(event.severity.value, 0) + 1
        
        return {
            "total_events": len(self._events),
            "by_type": type_counts,
            "by_severity": severity_counts,
            "time_range": {
                "start": self._events[0].timestamp.isoformat() if self._events else None,
                "end": self._events[-1].timestamp.isoformat() if self._events else None,
            }
        }
    
    async def save_to_storage(self) -> None:
        """Persist timeline events to storage"""
        self._data_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_path = self._data_path / f"timeline_{timestamp}.json"
        
        data = {
            "saved_at": datetime.utcnow().isoformat(),
            "event_count": len(self._events),
            "events": [e.to_dict() for e in self._events],
        }
        
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
    
    async def load_from_storage(self) -> None:
        """Load timeline events from storage"""
        if not self._data_path.exists():
            return
        
        for file_path in sorted(self._data_path.glob("timeline_*.json")):
            with open(file_path) as f:
                data = json.load(f)
                for event_data in data.get("events", []):
                    self.index(event_data)


# Convenience functions for creating timeline events

def create_alarm_event(
    summary: str,
    severity: EventSeverity = EventSeverity.WARNING,
    tag_id: str | None = None,
    details: dict | None = None,
) -> dict:
    """Create an alarm event"""
    return {
        "timestamp": datetime.utcnow(),
        "event_type": TimelineEventType.ALARM.value,
        "severity": severity.value,
        "summary": summary,
        "details": details or {},
        "related_tags": [tag_id] if tag_id else [],
    }


def create_trust_drop_event(
    tag_id: str,
    old_score: float,
    new_score: float,
    reason_codes: list[str],
) -> dict:
    """Create a trust drop event"""
    severity = EventSeverity.CRITICAL if new_score < 0.4 else EventSeverity.WARNING
    return {
        "timestamp": datetime.utcnow(),
        "event_type": TimelineEventType.TRUST_DROP.value,
        "severity": severity.value,
        "summary": f"Trust dropped: {tag_id} ({old_score:.2f} → {new_score:.2f})",
        "details": {
            "old_score": old_score,
            "new_score": new_score,
            "reason_codes": reason_codes,
        },
        "related_tags": [tag_id],
    }


def create_contradiction_event(
    contradiction_id: str,
    description: str,
    tags: list[str],
) -> dict:
    """Create a contradiction detected event"""
    return {
        "timestamp": datetime.utcnow(),
        "event_type": TimelineEventType.CONTRADICTION_DETECTED.value,
        "severity": EventSeverity.CRITICAL.value,
        "summary": description,
        "details": {"contradiction_id": contradiction_id},
        "related_tags": tags,
    }


def create_mode_transition_event(
    new_mode: str,
    trigger: str | None = None,
) -> dict:
    """Create a mode transition event"""
    return {
        "timestamp": datetime.utcnow(),
        "event_type": TimelineEventType.MODE_TRANSITION.value,
        "severity": EventSeverity.INFO.value if new_mode == "observe" else EventSeverity.WARNING.value,
        "summary": f"Mode changed to {new_mode.upper()}",
        "details": {"mode": new_mode, "trigger": trigger},
        "related_tags": [],
    }
