"""
Database utilities for Pharmaceutical Supply Chain Agentic AI

This module provides database connection and query utilities.
"""

from pymongo import MongoClient
from pymongo.database import Database
from typing import Optional, List, Dict, Any
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """MongoDB connection manager"""

    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None

    def connect(self, uri: str = "mongodb://localhost:27017", db_name: str = "pharma_supply_chain") -> Database:
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(uri)
            self.db = self.client[db_name]

            # Test connection
            self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {db_name}")
            return self.db

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    def get_database(self) -> Database:
        """Get database instance"""
        if self.db is None:
            uri = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
            db_name = os.getenv("DATABASE_NAME", "pharma_supply_chain")
            self.connect(uri, db_name)
        return self.db

# Global database connection instance
db_connection = DatabaseConnection()

def get_database() -> Database:
    """Get database instance (convenience function)"""
    return db_connection.get_database()

def connect_to_mongo() -> Database:
    """Connect to MongoDB (alias for get_database)"""
    return get_database()

class DataAccess:
    """Data access layer for querying sales and inventory data"""

    def __init__(self):
        self.db = get_database()

    def get_sales_history(self, drug_id: str, branch_id: Optional[str] = None,
                         days: int = 365) -> List[Dict[str, Any]]:
        """Get sales history for a drug"""
        try:
            # Build query (normalized to drug_id only for index usage)
            query = {
                "drug_id": drug_id.lower()
            }

            if branch_id:
                query["branch_id"] = branch_id

            # Limit to recent window to avoid full collection scans
            start_date = datetime.utcnow() - timedelta(days=days)
            query["date"] = {"$gte": start_date}

            # Aggregate per day to shrink payload while keeping signal
            pipeline = [
                {"$match": query},
                {
                    "$group": {
                        "_id": "$date",
                        "quantity": {"$sum": "$quantity"},
                        "drug_id": {"$first": "$drug_id"},
                        "drug_name": {"$first": "$drug_name"},
                        "branch_id": {"$first": "$branch_id"}
                    }
                },
                {"$sort": {"_id": -1}},  # latest dates first
                {"$limit": days},  # one record per day max
                {"$sort": {"_id": 1}},  # keep chronological order
            ]

            aggregated = list(self.db.sales_history.aggregate(pipeline, allowDiskUse=True))

            sales_data = [
                {
                    "drug_id": doc.get("drug_id", drug_id.lower()),
                    "drug_name": doc.get("drug_name", drug_id),
                    "branch_id": doc.get("branch_id", branch_id or "UNKNOWN"),
                    "quantity": doc.get("quantity", 0),
                    "date": doc["_id"]
                }
                for doc in aggregated
            ]

            # Defensive fallback: if aggregation returns nothing, fetch a small sample directly
            if not sales_data:
                cursor = (
                    self.db.sales_history
                    .find(query, {"drug_id": 1, "drug_name": 1, "branch_id": 1, "quantity": 1, "date": 1})
                    .sort("date", 1)
                    .limit(days)
                )
                sales_data = list(cursor)

            logger.info(
                f"Retrieved {len(sales_data)} aggregated sales records for drug {drug_id} "
                f"(last {days} days)"
            )
            return sales_data

        except Exception as e:
            logger.error(f"Error retrieving sales history: {e}")
            return []

    def get_inventory_status(self, drug_id: str, branch_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get current inventory status for a drug"""
        try:
            query = {"drug_id": drug_id}
            if branch_id:
                query["branch_id"] = branch_id

            inventory_data = list(self.db.inventory.find(query))
            logger.info(f"Retrieved {len(inventory_data)} inventory records for drug {drug_id}")
            return inventory_data

        except Exception as e:
            logger.error(f"Error retrieving inventory status: {e}")
            return []

    def get_all_drugs(self) -> List[Dict[str, Any]]:
        """Get all drugs information"""
        try:
            drugs = list(self.db.drugs.find({}))
            logger.info(f"Retrieved {len(drugs)} drug records")
            return drugs

        except Exception as e:
            logger.error(f"Error retrieving drugs: {e}")
            return []

    def get_drug_info(self, drug_id: str) -> Optional[Dict[str, Any]]:
        """Get information for a specific drug"""
        try:
            drug = self.db.drugs.find_one({"id": drug_id})
            return drug

        except Exception as e:
            logger.error(f"Error retrieving drug info for {drug_id}: {e}")
            return None

# Global data access instance
data_access = DataAccess()

def get_sales_data(drug_id: str, branch_id: Optional[str] = None, days: int = 365) -> List[Dict[str, Any]]:
    """Convenience function to get sales data (direct DB query to avoid heavy loads)"""
    try:
        db = get_database()
        match_stage: Dict[str, Any] = {
            "drug_id": drug_id.lower()
        }
        if branch_id:
            match_stage["branch_id"] = branch_id

        # Limit to the most recent window of data to keep queries fast
        start_date = datetime.utcnow() - timedelta(days=days)
        match_stage["date"] = {"$gte": start_date}

        pipeline = [
            {"$match": match_stage},
            {
                "$group": {
                    "_id": "$date",
                    "quantity": {"$sum": "$quantity"},
                    "drug_id": {"$first": "$drug_id"},
                    "drug_name": {"$first": "$drug_name"},
                    "branch_id": {"$first": "$branch_id"}
                }
            },
            {"$sort": {"_id": -1}},
            {"$limit": days},
            {"$sort": {"_id": 1}}
        ]

        aggregated = list(db.sales_history.aggregate(pipeline, allowDiskUse=True))
        logger.info(f"Aggregated sales rows for {drug_id}: {len(aggregated)}")

        sales_data = [
            {
                "drug_id": doc.get("drug_id", drug_id.lower()),
                "drug_name": doc.get("drug_name", drug_id),
                "branch_id": doc.get("branch_id", branch_id or "UNKNOWN"),
                "quantity": doc.get("quantity", 0),
                "date": doc["_id"]
            }
            for doc in aggregated
        ]

        # Fallback to a capped direct query if aggregation unexpectedly returns empty
        if not sales_data:
            cursor = (
                db.sales_history
                .find(match_stage, {"drug_id": 1, "drug_name": 1, "branch_id": 1, "quantity": 1, "date": 1})
                .sort("date", 1)
                .limit(days)
            )
            sales_data = list(cursor)
            logger.info(f"Fallback sales rows for {drug_id}: {len(sales_data)}")

        logger.info(f"Retrieved {len(sales_data)} sales records for drug {drug_id}")
        return sales_data
    except Exception as e:
        logger.error(f"Error retrieving sales data: {e}")
        return []

def get_inventory_data(drug_id: str, branch_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Convenience function to get inventory data"""
    return data_access.get_inventory_status(drug_id, branch_id)
