#!/usr/bin/env python3
"""
Data Loading Script for Pharmaceutical Supply Chain POC

This script loads the downloaded datasets into MongoDB for the Agentic AI system.
"""

import os
import pandas as pd
import pymongo
from pymongo import MongoClient
from datetime import datetime, timedelta
import logging
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self, mongo_uri="mongodb://localhost:27017/", db_name="pharma_supply_chain"):
        """Initialize MongoDB connection"""
        try:
            self.client = MongoClient(mongo_uri)
            self.db = self.client[db_name]
            # Test connection
            self.client.admin.command('ping')
            logger.info("Connected to MongoDB successfully")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def load_medicines_dataset(self, file_path="data/medicines.csv"):
        """Load medicines dataset from CSV"""
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return

        try:
            logger.info("Loading medicines dataset...")
            df = pd.read_csv(file_path, encoding='utf-8')

            # Clean and prepare data
            df = df.dropna(subset=['med_name'])  # Remove rows without medicine name
            df = df.fillna("")  # Fill NaN values with empty strings

            # Convert to dictionary format
            medicines_data = []
            for _, row in df.iterrows():
                # Clean price - remove currency symbols and convert to float
                price_str = str(row.get('final_price', '0')).replace('₹', '').replace(',', '').strip()
                try:
                    price = float(price_str) if price_str and price_str != 'nan' else 0.0
                except ValueError:
                    price = 0.0

                medicine = {
                    "id": str(row.get('med_name', '')).lower().replace(' ', '_'),
                    "name": row.get('med_name', ''),
                    "generic_name": row.get('generic_name', ''),
                    "manufacturer": row.get('drug_manufacturer', ''),
                    "manufacturer_origin": row.get('drug_manufacturer_origin', ''),
                    "price": price,
                    "prescription_required": bool(row.get('prescription_required', False)),
                    "drug_content": row.get('drug_content', ''),
                    "disease_category": row.get('disease_name', ''),
                    "img_urls": row.get('img_urls', ''),
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                medicines_data.append(medicine)

            # Insert into MongoDB
            if medicines_data:
                self.db.drugs.insert_many(medicines_data)
                logger.info(f"Inserted {len(medicines_data)} medicines into drugs collection")

        except Exception as e:
            logger.error(f"Error loading medicines dataset: {e}")

    def load_supply_chain_dataset(self, file_path="data/Pharmaceutical Supply Chain Optimization.xlsx"):
        """Load pharmaceutical supply chain optimization dataset from Excel"""
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return

        try:
            logger.info("Loading supply chain optimization dataset...")
            df = pd.read_excel(file_path)

            # Create sample inventory data based on the optimization data
            inventory_data = []
            sales_history_data = []

            for _, row in df.iterrows():
                drug_name = row.get('Drug', '')
                demand_forecast = row.get('Demand_Forecast', 0)
                optimal_stock = row.get('Optimal_Stock_Level', 0)
                restocking_strategy = row.get('Restocking_Strategy', 'Monthly')

                # Create inventory record
                inventory_record = {
                    "drug_id": str(drug_name).lower().replace(' ', '_'),
                    "drug_name": drug_name,
                    "branch_id": "MAIN_BRANCH",  # Default branch
                    "current_stock": int(optimal_stock * 0.8),  # Assume 80% of optimal
                    "optimal_stock": int(optimal_stock),
                    "safe_stock": int(optimal_stock * 0.2),  # 20% safety stock
                    "demand_forecast": int(demand_forecast),
                    "restocking_strategy": restocking_strategy,
                    "last_updated": datetime.utcnow()
                }
                inventory_data.append(inventory_record)

                # Create sample sales history (last 30 days)
                # Create 100 days of historical data for each drug
                base_date = datetime.utcnow() - timedelta(days=100)
                for day in range(100):
                    current_date = base_date + timedelta(days=day)
                    # Add some randomness to sales
                    daily_variation = np.random.normal(0, 10)  # Normal distribution around base demand
                    daily_quantity = max(1, int(demand_forecast / 30) + daily_variation)

                    sales_record = {
                        "drug_id": str(drug_name).lower().replace(' ', '_'),
                        "drug_name": drug_name,
                        "branch_id": "MAIN_BRANCH",
                        "quantity": daily_quantity,
                        "date": current_date.replace(hour=0, minute=0, second=0, microsecond=0),
                        "unit_price": 10.0 + (day % 3),  # Sample price
                        "total_amount": daily_quantity * (10.0 + (day % 3))
                    }
                    sales_history_data.append(sales_record)

            # Insert into MongoDB
            if inventory_data:
                self.db.inventory.insert_many(inventory_data)
                logger.info(f"Inserted {len(inventory_data)} inventory records")

            if sales_history_data:
                self.db.sales_history.insert_many(sales_history_data)
                logger.info(f"Inserted {len(sales_history_data)} sales history records")

        except Exception as e:
            logger.error(f"Error loading supply chain dataset: {e}")

    def create_indexes(self):
        """Create necessary indexes for performance"""
        try:
            logger.info("Creating database indexes...")

            # Sales history indexes
            self.db.sales_history.create_index([("drug_id", 1), ("branch_id", 1), ("date", -1)])
            self.db.sales_history.create_index([("branch_id", 1), ("date", -1)])

            # Inventory indexes (non-unique for now)
            self.db.inventory.create_index([("drug_id", 1), ("branch_id", 1)])

            # Drugs indexes
            self.db.drugs.create_index([("id", 1)])
            self.db.drugs.create_index([("name", 1)])

            logger.info("Indexes created successfully")

        except Exception as e:
            logger.error(f"Error creating indexes: {e}")

    def clear_collections(self):
        """Clear existing data (use with caution)"""
        try:
            logger.warning("Clearing existing collections...")
            self.db.drugs.drop()
            self.db.inventory.drop()
            self.db.sales_history.drop()
            logger.info("Collections cleared")
        except Exception as e:
            logger.error(f"Error clearing collections: {e}")

    def get_stats(self):
        """Get database statistics"""
        try:
            stats = {
                "drugs": self.db.drugs.count_documents({}),
                "inventory": self.db.inventory.count_documents({}),
                "sales_history": self.db.sales_history.count_documents({})
            }
            logger.info(f"Database stats: {stats}")
            return stats
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}

def main():
    """Main function to run the data loading process"""
    loader = DataLoader()

    # Always clear existing data for fresh start
    logger.info("Clearing existing data...")
    loader.clear_collections()

    # Load datasets
    loader.load_medicines_dataset()
    loader.load_supply_chain_dataset()

    # Create indexes
    loader.create_indexes()

    # Show stats
    stats = loader.get_stats()

    logger.info("Data loading completed successfully!")
    logger.info(f"Total records loaded: {sum(stats.values())}")

if __name__ == "__main__":
    main()
