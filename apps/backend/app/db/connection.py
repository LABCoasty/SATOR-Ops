"""
MongoDB Atlas Connection Module

Handles connection to MongoDB Atlas and provides database access.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient
from pymongo.database import Database
from typing import Optional
import logging

from config import config

logger = logging.getLogger(__name__)


class MongoDBConnection:
    """
    MongoDB Atlas connection manager.
    
    Provides both sync (pymongo) and async (motor) clients.
    """
    
    _instance: Optional["MongoDBConnection"] = None
    _sync_client: Optional[MongoClient] = None
    _async_client: Optional[AsyncIOMotorClient] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self._uri = config.mongodb_uri
        self._database_name = config.mongodb_database
        self._enabled = config.enable_mongodb and self._uri is not None
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    @property
    def sync_client(self) -> Optional[MongoClient]:
        """Get synchronous MongoDB client"""
        if not self._enabled:
            return None
        
        if self._sync_client is None:
            self._sync_client = MongoClient(self._uri)
            logger.info(f"Connected to MongoDB Atlas (sync): {self._database_name}")
        
        return self._sync_client
    
    @property
    def async_client(self) -> Optional[AsyncIOMotorClient]:
        """Get asynchronous MongoDB client"""
        if not self._enabled:
            return None
        
        if self._async_client is None:
            self._async_client = AsyncIOMotorClient(self._uri)
            logger.info(f"Connected to MongoDB Atlas (async): {self._database_name}")
        
        return self._async_client
    
    def get_sync_db(self) -> Optional[Database]:
        """Get synchronous database instance"""
        if self.sync_client is None:
            return None
        return self.sync_client[self._database_name]
    
    def get_async_db(self) -> Optional[AsyncIOMotorDatabase]:
        """Get asynchronous database instance"""
        if self.async_client is None:
            return None
        return self.async_client[self._database_name]
    
    def close(self):
        """Close all connections"""
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None
        if self._async_client:
            self._async_client.close()
            self._async_client = None
        logger.info("MongoDB connections closed")
    
    async def health_check(self) -> dict:
        """Check MongoDB connection health"""
        if not self._enabled:
            return {"status": "disabled", "message": "MongoDB not configured"}
        
        try:
            db = self.get_async_db()
            if db is None:
                return {"status": "error", "message": "Failed to get database"}
            
            # Ping the database
            await db.command("ping")
            
            # Get collection stats
            collections = await db.list_collection_names()
            
            return {
                "status": "healthy",
                "database": self._database_name,
                "collections": collections,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}


# Global connection instance
_connection: Optional[MongoDBConnection] = None


def get_db() -> MongoDBConnection:
    """Get the global MongoDB connection"""
    global _connection
    if _connection is None:
        _connection = MongoDBConnection()
    return _connection
