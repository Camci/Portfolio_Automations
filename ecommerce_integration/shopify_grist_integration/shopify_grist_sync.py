#!/usr/bin/env python3
"""
Shopify-Grist Synchronization System

This script provides bidirectional synchronization between Shopify e-commerce platform
and Grist spreadsheets, allowing for efficient inventory and order management.
"""

import os
import sys
import time
import json
import logging
import argparse
import yaml
import requests
import pandas as pd
import schedule
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("shopify-grist-sync")

# Configuration paths
CONFIG_FILE = "config.yaml"
MAPPING_FILE = "field_mappings.yaml"
CACHE_DIR = ".cache"

class SyncEngine:
    """Core synchronization engine that orchestrates data flow between systems."""
    
    def __init__(self, config):
        self.config = config
        self.shopify = ShopifyConnector(config['shopify'])
        self.grist = GristConnector(config['grist'])
        self.mappings = self._load_mappings()
        self.last_sync = self._get_last_sync_time()
        
        # Ensure cache directory exists
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)
    
    def _load_mappings(self):
        """Load field mappings from YAML file."""
        try:
            with open(MAPPING_FILE, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load mappings: {e}")
            sys.exit(1)
    
    def _get_last_sync_time(self):
        """Get the timestamp of the last successful synchronization."""
        timestamp_file = os.path.join(CACHE_DIR, "last_sync.txt")
        if os.path.exists(timestamp_file):
            with open(timestamp_file, 'r') as f:
                return f.read().strip()
        return None
    
    def _update_last_sync_time(self):
        """Update the timestamp of the last successful synchronization."""
        timestamp_file = os.path.join(CACHE_DIR, "last_sync.txt")
        with open(timestamp_file, 'w') as f:
            current_time = datetime.now().isoformat()
            f.write(current_time)
            return current_time
    
    def sync_products(self):
        """Synchronize product data between Shopify and Grist."""
        logger.info("Starting product synchronization...")
        
        # 1. Fetch data from both systems
        shopify_products = self.shopify.get_products(self.last_sync)
        grist_products = self.grist.get_products()
        
        # 2. Identify changes in both systems
        shopify_changes = self._identify_shopify_changes(shopify_products, grist_products)
        grist_changes = self._identify_grist_changes(grist_products, shopify_products)
        
        # 3. Resolve conflicts
        merged_changes = self._resolve_conflicts(shopify_changes, grist_changes)
        
        # 4. Apply changes to both systems
        shopify_updates = self._apply_to_shopify(merged_changes['to_shopify'])
        grist_updates = self._apply_to_grist(merged_changes['to_grist'])
        
        # 5. Update last sync time
        new_sync_time = self._update_last_sync_time()
        self.last_sync = new_sync_time
        
        logger.info(f"Product synchronization completed. Updated {len(shopify_updates)} Shopify records and {len(grist_updates)} Grist records.")
        
        return {
            'shopify_updates': shopify_updates,
            'grist_updates': grist_updates,
            'sync_time': new_sync_time
        }
    
    def _identify_shopify_changes(self, shopify_data, grist_data):
        """Identify changes in Shopify that need to be synced to Grist."""
        changes = []
        
        # Implementation depends on data structure
        # This is a placeholder for the real implementation
        
        logger.info(f"Identified {len(changes)} changes in Shopify")
        return changes
    
    def _identify_grist_changes(self, grist_data, shopify_data):
        """Identify changes in Grist that need to be synced to Shopify."""
        changes = []
        
        # Implementation depends on data structure
        # This is a placeholder for the real implementation
        
        logger.info(f"Identified {len(changes)} changes in Grist")
        return changes
    
    def _resolve_conflicts(self, shopify_changes, grist_changes):
        """Resolve conflicts between changes in both systems."""
        resolved = {
            'to_shopify': [],
            'to_grist': []
        }
        
        # Apply conflict resolution rules
        # This is a placeholder for the real implementation
        
        logger.info("Conflicts resolved")
        return resolved
    
    def _apply_to_shopify(self, changes):
        """Apply changes to Shopify."""
        results = []
        
        for change in changes:
            try:
                # Apply change to Shopify
                self.shopify.update_product(change)
                results.append({
                    'id': change.get('id'),
                    'status': 'success'
                })
            except Exception as e:
                logger.error(f"Failed to update Shopify: {e}")
                results.append({
                    'id': change.get('id'),
                    'status': 'error',
                    'message': str(e)
                })
        
        return results
    
    def _apply_to_grist(self, changes):
        """Apply changes to Grist."""
        results = []
        
        for change in changes:
            try:
                # Apply change to Grist
                self.grist.update_record(change)
                results.append({
                    'id': change.get('id'),
                    'status': 'success'
                })
            except Exception as e:
                logger.error(f"Failed to update Grist: {e}")
                results.append({
                    'id': change.get('id'),
                    'status': 'error',
                    'message': str(e)
                })
        
        return results


class ShopifyConnector:
    """Handles all interactions with the Shopify API."""
    
    def __init__(self, config):
        self.store_url = config['store_url']
        self.api_key = config['api_key']
        self.api_secret = config['api_secret']
        self.access_token = config['access_token']
        self.api_version = config.get('api_version', '2023-07')
        
        # Set up API headers
        self.headers = {
            'X-Shopify-Access-Token': self.access_token,
            'Content-Type': 'application/json'
        }
    
    def get_products(self, since_time=None):
        """Fetch products from Shopify, optionally filtered by update time."""
        url = f"https://{self.store_url}/admin/api/{self.api_version}/products.json"
        
        # Add updated_at filter if since_time is provided
        if since_time:
            url += f"?updated_at_min={since_time}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json().get('products', [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch products from Shopify: {e}")
            return []
    
    def update_product(self, product_data):
        """Update a product in Shopify."""
        product_id = product_data.get('id')
        if not product_id:
            logger.error("Cannot update product without ID")
            return False
        
        url = f"https://{self.store_url}/admin/api/{self.api_version}/products/{product_id}.json"
        
        try:
            response = requests.put(
                url, 
                headers=self.headers,
                json={'product': product_data}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update product {product_id} in Shopify: {e}")
            raise


class GristConnector:
    """Handles all interactions with the Grist API."""
    
    def __init__(self, config):
        self.api_key = config['api_key']
        self.doc_id = config['doc_id']
        self.workspace_id = config['workspace_id']
        self.base_url = "https://docs.getgrist.com/api"
        
        # Set up API headers
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def get_products(self):
        """Fetch product records from Grist."""
        url = f"{self.base_url}/docs/{self.doc_id}/tables/Products/records"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json().get('records', [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch records from Grist: {e}")
            return []
    
    def update_record(self, record_data):
        """Update a record in Grist."""
        record_id = record_data.get('id')
        if not record_id:
            logger.error("Cannot update record without ID")
            return False
        
        url = f"{self.base_url}/docs/{self.doc_id}/tables/Products/records"
        
        try:
            payload = {
                'records': [{
                    'id': record_id,
                    'fields': record_data.get('fields', {})
                }]
            }
            
            response = requests.patch(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update record {record_id} in Grist: {e}")
            raise


def load_config():
    """Load configuration from YAML file."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Shopify-Grist Synchronization')
    parser.add_argument('--mode', choices=['once', 'continuous'], default='once',
                      help='Sync mode: once (single run) or continuous (daemon)')
    parser.add_argument('--interval', type=int, default=15,
                      help='Sync interval in minutes for continuous mode')
    parser.add_argument('--fields', type=str,
                      help='Comma-separated list of fields to sync')
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # Create sync engine
    sync_engine = SyncEngine(config)
    
    # Execute sync based on mode
    if args.mode == 'once':
        logger.info("Running one-time synchronization")
        result = sync_engine.sync_products()
        logger.info(f"Sync completed at {result['sync_time']}")
    else:
        logger.info(f"Starting continuous synchronization every {args.interval} minutes")
        
        # Run sync immediately
        sync_engine.sync_products()
        
        # Schedule regular sync
        schedule.every(args.interval).minutes.do(sync_engine.sync_products)
        
        # Run the scheduler
        while True:
            schedule.run_pending()
            time.sleep(1)


if __name__ == "__main__":
    main() 