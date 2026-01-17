"""
Repository Classes for MongoDB

Provides data access patterns for each entity type.
"""

from datetime import datetime
from typing import Any, Optional
from bson import ObjectId

from .connection import get_db


class BaseRepository:
    """Base repository with common CRUD operations"""
    
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
    
    def _get_collection(self):
        """Get the MongoDB collection (sync)"""
        db = get_db().get_sync_db()
        if db is None:
            raise RuntimeError("MongoDB not configured")
        return db[self.collection_name]
    
    async def _get_async_collection(self):
        """Get the MongoDB collection (async)"""
        db = get_db().get_async_db()
        if db is None:
            raise RuntimeError("MongoDB not configured")
        return db[self.collection_name]
    
    def insert_one(self, document: dict) -> str:
        """Insert a single document"""
        document["created_at"] = datetime.utcnow()
        result = self._get_collection().insert_one(document)
        return str(result.inserted_id)
    
    def insert_many(self, documents: list[dict]) -> list[str]:
        """Insert multiple documents"""
        now = datetime.utcnow()
        for doc in documents:
            doc["created_at"] = now
        result = self._get_collection().insert_many(documents)
        return [str(id) for id in result.inserted_ids]
    
    def find_one(self, query: dict) -> Optional[dict]:
        """Find a single document"""
        return self._get_collection().find_one(query)
    
    def find_many(self, query: dict, limit: int = 100) -> list[dict]:
        """Find multiple documents"""
        return list(self._get_collection().find(query).limit(limit))
    
    async def async_insert_one(self, document: dict) -> str:
        """Insert a single document (async)"""
        document["created_at"] = datetime.utcnow()
        collection = await self._get_async_collection()
        result = await collection.insert_one(document)
        return str(result.inserted_id)
    
    async def async_insert_many(self, documents: list[dict]) -> list[str]:
        """Insert multiple documents (async)"""
        now = datetime.utcnow()
        for doc in documents:
            doc["created_at"] = now
        collection = await self._get_async_collection()
        result = await collection.insert_many(documents)
        return [str(id) for id in result.inserted_ids]


class TelemetryRepository(BaseRepository):
    """Repository for telemetry data"""
    
    def __init__(self):
        super().__init__("telemetry")
    
    def insert_telemetry_point(self, point: dict) -> str:
        """Insert a single telemetry point"""
        return self.insert_one(point)
    
    def insert_telemetry_batch(self, points: list[dict]) -> list[str]:
        """Insert a batch of telemetry points"""
        return self.insert_many(points)
    
    def find_by_tag(self, tag_id: str, limit: int = 1000) -> list[dict]:
        """Find telemetry by tag ID"""
        return self.find_many({"tag_id": tag_id}, limit=limit)
    
    def find_by_time_range(
        self, 
        start_time: datetime, 
        end_time: datetime,
        tag_id: Optional[str] = None,
        limit: int = 10000
    ) -> list[dict]:
        """Find telemetry within a time range"""
        query = {
            "timestamp": {
                "$gte": start_time,
                "$lte": end_time
            }
        }
        if tag_id:
            query["tag_id"] = tag_id
        
        return list(
            self._get_collection()
            .find(query)
            .sort("timestamp", 1)
            .limit(limit)
        )
    
    def create_indexes(self):
        """Create indexes for optimal query performance"""
        collection = self._get_collection()
        collection.create_index([("tag_id", 1), ("timestamp", -1)])
        collection.create_index([("timestamp", -1)])
        collection.create_index([("scenario_id", 1)])


class AuditRepository(BaseRepository):
    """Repository for audit events"""
    
    def __init__(self):
        super().__init__("audit_events")
    
    def insert_audit_event(self, event: dict) -> str:
        """Insert an audit event"""
        return self.insert_one(event)
    
    def find_by_chain_id(self, chain_id: str) -> list[dict]:
        """Find all events in a chain"""
        return list(
            self._get_collection()
            .find({"chain_id": chain_id})
            .sort("timestamp", 1)
        )
    
    def find_latest_chain(self) -> Optional[dict]:
        """Find the most recent chain"""
        return self._get_collection().find_one(
            {},
            sort=[("timestamp", -1)]
        )
    
    def create_indexes(self):
        """Create indexes"""
        collection = self._get_collection()
        collection.create_index([("chain_id", 1), ("timestamp", 1)])
        collection.create_index([("event_id", 1)], unique=True)
        collection.create_index([("current_hash", 1)])


class IncidentRepository(BaseRepository):
    """Repository for incidents"""
    
    def __init__(self):
        super().__init__("incidents")
    
    def create_incident(self, incident: dict) -> str:
        """Create a new incident"""
        return self.insert_one(incident)
    
    def find_by_id(self, incident_id: str) -> Optional[dict]:
        """Find incident by ID"""
        return self.find_one({"incident_id": incident_id})
    
    def find_active(self) -> list[dict]:
        """Find all active incidents"""
        return self.find_many({"status": "active"})
    
    def update_status(self, incident_id: str, status: str) -> bool:
        """Update incident status"""
        result = self._get_collection().update_one(
            {"incident_id": incident_id},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0


class SimulationRepository(BaseRepository):
    """Repository for simulation runs and scenarios"""
    
    def __init__(self):
        super().__init__("simulations")
    
    def create_simulation_run(self, run: dict) -> str:
        """Create a new simulation run record"""
        return self.insert_one(run)
    
    def find_by_scenario(self, scenario_id: str) -> list[dict]:
        """Find all runs of a scenario"""
        return self.find_many({"scenario_id": scenario_id})
    
    def get_latest_run(self, scenario_id: str) -> Optional[dict]:
        """Get the most recent run of a scenario"""
        return self._get_collection().find_one(
            {"scenario_id": scenario_id},
            sort=[("created_at", -1)]
        )
