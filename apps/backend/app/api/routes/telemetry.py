from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime


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


class TelemetryStats(BaseModel):
    source: str
    metric: str
    min: float
    max: float
    avg: float
    count: int
    last_value: float
    last_timestamp: datetime


@router.post("/ingest")
async def ingest_telemetry(batch: TelemetryBatch):
    return {"status": "accepted", "count": len(batch.points)}


@router.post("/query", response_model=List[TelemetryPoint])
async def query_telemetry(query: TelemetryQuery):
    return []


@router.get("/sources")
async def list_sources():
    return {"sources": []}


@router.get("/metrics")
async def list_metrics(source: Optional[str] = None):
    return {"metrics": []}


@router.get("/stats", response_model=List[TelemetryStats])
async def get_stats(source: Optional[str] = None):
    return []


@router.get("/health")
async def telemetry_health():
    return {
        "status": "healthy",
        "sources_active": 0,
        "last_ingest": None,
    }
