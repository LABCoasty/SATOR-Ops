from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

from ...data.seed_data import (
    generate_telemetry_channels,
    generate_signal_summary,
    DATA_SOURCES,
)


router = APIRouter()


class TelemetryPoint(BaseModel):
    source: str
    metric: str
    value: float
    timestamp: datetime
    unit: Optional[str] = None
    tags: Optional[dict] = None


class TelemetryBatch(BaseModel):
    points: List[TelemetryPoint]


class TelemetryQuery(BaseModel):
    sources: Optional[List[str]] = None
    metrics: Optional[List[str]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    aggregation: Optional[str] = None


class TelemetryChannel(BaseModel):
    id: str
    name: str
    source: str
    value: float
    unit: str
    trend: str
    status: str
    sparkline: List[float]
    summary: str
    min_threshold: float
    max_threshold: float
    timestamp: str


class TelemetryStats(BaseModel):
    source: str
    metric: str
    min: float
    max: float
    avg: float
    count: int
    last_value: float
    last_timestamp: datetime


class DataSource(BaseModel):
    id: str
    name: str
    reliability: float
    last_update: str
    status: str
    type: str


class SignalSummary(BaseModel):
    active_signals: int
    sources_reporting: int
    healthy: int
    warnings: int
    critical: int
    unknown: int
    last_sync: str
    connected: bool


@router.post("/ingest")
async def ingest_telemetry(batch: TelemetryBatch):
    """Ingest a batch of telemetry points."""
    return {"status": "accepted", "count": len(batch.points)}


@router.post("/query", response_model=List[TelemetryPoint])
async def query_telemetry(query: TelemetryQuery):
    """Query historical telemetry data."""
    # For now, return empty - would query database in production
    return []


@router.get("/channels", response_model=List[TelemetryChannel])
async def get_channels():
    """Get all active telemetry channels with current values."""
    return generate_telemetry_channels()


@router.get("/sources", response_model=List[DataSource])
async def list_sources():
    """List all data sources with reliability scores."""
    return DATA_SOURCES


@router.get("/summary", response_model=SignalSummary)
async def get_summary():
    """Get signal summary statistics."""
    return generate_signal_summary()


@router.get("/metrics")
async def list_metrics(source: Optional[str] = None):
    """List available metrics, optionally filtered by source."""
    metrics = [
        "temperature",
        "pressure", 
        "flow_rate",
        "vibration",
        "power",
        "humidity",
    ]
    return {"metrics": metrics}


@router.get("/stats", response_model=List[TelemetryStats])
async def get_stats(source: Optional[str] = None):
    """Get aggregated statistics for telemetry data."""
    channels = generate_telemetry_channels()
    stats = []
    
    for channel in channels:
        sparkline = channel["sparkline"]
        stats.append(TelemetryStats(
            source=channel["source"],
            metric=channel["name"],
            min=min(sparkline),
            max=max(sparkline),
            avg=sum(sparkline) / len(sparkline),
            count=len(sparkline),
            last_value=channel["value"],
            last_timestamp=datetime.fromisoformat(channel["timestamp"]),
        ))
    
    if source:
        stats = [s for s in stats if source.lower() in s.source.lower()]
    
    return stats


@router.get("/health")
async def telemetry_health():
    """Get telemetry system health status."""
    summary = generate_signal_summary()
    sources = DATA_SOURCES
    
    online_count = len([s for s in sources if s["status"] == "online"])
    
    return {
        "status": "healthy" if online_count > len(sources) / 2 else "degraded",
        "sources_active": online_count,
        "sources_total": len(sources),
        "last_ingest": datetime.utcnow().isoformat(),
        "signals": {
            "active": summary["active_signals"],
            "healthy": summary["healthy"],
            "warnings": summary["warnings"],
        },
    }
