#!/usr/bin/env python3
"""
Dynamic Pricing System

An algorithmic pricing system that automatically adjusts product prices based on market
conditions, competitor pricing, inventory levels, and demand patterns.
"""

import os
import sys
import json
import logging
import argparse
import schedule
import time
import yaml
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dynamic_pricing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("dynamic-pricing")

# Configuration paths
CONFIG_FILE = "config.yaml"
CREDENTIALS_FILE = "credentials.json"
SOURCES_FILE = "sources.json"
RULES_FILE = "rules.json"
CACHE_DIR = ".cache"

class ShopifyConnector:
    """Handles interactions with the Shopify API for product and pricing data."""
    
    def __init__(self, credentials_path):
        """
        Initialize the Shopify connector with API credentials.
        
        Args:
            credentials_path (str): Path to the credentials JSON file
        """
        self.credentials = self._load_credentials(credentials_path)
        self.store_url = self.credentials.get("store_url")
        self.access_token = self.credentials.get("access_token")
        self.api_version = self.credentials.get("api_version", "2023-07")
        
        # Set up API headers
        self.headers = {
            'X-Shopify-Access-Token': self.access_token,
            'Content-Type': 'application/json'
        }
    
    def _load_credentials(self, credentials_path):
        """Load API credentials from JSON file."""
        try:
            with open(credentials_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            sys.exit(1)
    
    def get_products(self, collection_id=None, product_type=None, limit=250):
        """
        Fetch products from Shopify, optionally filtered by collection or type.
        
        Args:
            collection_id (str, optional): Filter by collection ID
            product_type (str, optional): Filter by product type
            limit (int, optional): Maximum number of products to fetch
            
        Returns:
            list: List of product data dictionaries
        """
        url = f"https://{self.store_url}/admin/api/{self.api_version}/products.json?limit={limit}"
        
        # Add collection filter if provided
        if collection_id:
            url += f"&collection_id={collection_id}"
        
        # Add product type filter if provided
        if product_type:
            url += f"&product_type={product_type}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            products = response.json().get('products', [])
            logger.info(f"Fetched {len(products)} products from Shopify")
            return products
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch products: {e}")
            return []
    
    def get_inventory_levels(self, inventory_item_ids):
        """
        Fetch inventory levels for specific inventory item IDs.
        
        Args:
            inventory_item_ids (list): List of inventory item IDs
            
        Returns:
            dict: Dictionary mapping inventory item IDs to inventory levels
        """
        if not inventory_item_ids:
            return {}
        
        # Convert list to comma-separated string
        ids_str = ','.join(inventory_item_ids)
        
        url = f"https://{self.store_url}/admin/api/{self.api_version}/inventory_levels.json?inventory_item_ids={ids_str}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            inventory_levels = response.json().get('inventory_levels', [])
            
            # Create a mapping from inventory item ID to available quantity
            inventory_map = {
                level.get('inventory_item_id'): level.get('available') 
                for level in inventory_levels
            }
            
            return inventory_map
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch inventory levels: {e}")
            return {}
    
    def update_product_price(self, product_id, variant_id, new_price):
        """
        Update the price of a specific product variant.
        
        Args:
            product_id (str): Product ID
            variant_id (str): Variant ID
            new_price (float): New price to set
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        url = f"https://{self.store_url}/admin/api/{self.api_version}/variants/{variant_id}.json"
        
        payload = {
            'variant': {
                'id': variant_id,
                'price': str(new_price)
            }
        }
        
        try:
            response = requests.put(url, headers=self.headers, json=payload)
            response.raise_for_status()
            logger.info(f"Updated price for variant {variant_id} to {new_price}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update price for variant {variant_id}: {e}")
            return False


class CompetitorMonitor:
    """Monitors competitor pricing from various sources."""
    
    def __init__(self, sources_path):
        """
        Initialize the competitor monitor.
        
        Args:
            sources_path (str): Path to the sources JSON file
        """
        self.sources = self._load_sources(sources_path)
    
    def _load_sources(self, sources_path):
        """Load competitor data sources from JSON file."""
        try:
            with open(sources_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load sources: {e}")
            return {}
    
    def get_competitor_prices(self, product_id, product_type=None):
        """
        Fetch competitor prices for a specific product or product type.
        
        Args:
            product_id (str): Product ID to match with competitor products
            product_type (str, optional): Product type for broader matching
            
        Returns:
            list: List of competitor price data for similar products
        """
        # In a real implementation, this would call API endpoints or scrape websites
        # For this example, we'll return mock data from the sources file
        
        competitor_prices = []
        
        # Check if we have specific mappings for this product
        product_mappings = self.sources.get('product_mappings', {})
        if product_id in product_mappings:
            # Direct product mapping exists
            for competitor, competitor_product in product_mappings[product_id].items():
                if 'price' in competitor_product:
                    competitor_prices.append({
                        'competitor': competitor,
                        'product_id': competitor_product.get('id'),
                        'product_name': competitor_product.get('name'),
                        'price': competitor_product.get('price'),
                        'url': competitor_product.get('url'),
                        'last_updated': competitor_product.get('last_updated')
                    })
        
        # If no direct mappings or we want broader results, check product type
        if not competitor_prices and product_type:
            type_mappings = self.sources.get('type_mappings', {})
            if product_type in type_mappings:
                for competitor, products in type_mappings[product_type].items():
                    for product in products:
                        competitor_prices.append({
                            'competitor': competitor,
                            'product_id': product.get('id'),
                            'product_name': product.get('name'),
                            'price': product.get('price'),
                            'url': product.get('url'),
                            'last_updated': product.get('last_updated')
                        })
        
        logger.info(f"Found {len(competitor_prices)} competitor prices for product {product_id}")
        return competitor_prices


class PricingEngine:
    """Core engine for price calculation and rule application."""
    
    def __init__(self, rules_path):
        """
        Initialize the pricing engine.
        
        Args:
            rules_path (str): Path to the pricing rules JSON file
        """
        self.rules = self._load_rules(rules_path)
    
    def _load_rules(self, rules_path):
        """Load pricing rules from JSON file."""
        try:
            with open(rules_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load rules: {e}")
            return {}
    
    def get_applicable_rules(self, product):
        """
        Determine which rules apply to a given product.
        
        Args:
            product (dict): Product data
            
        Returns:
            list: List of applicable rules sorted by priority
        """
        applicable_rules = []
        
        for rule in self.rules.get('rules', []):
            # Check rule conditions
            conditions = rule.get('conditions', [])
            conditions_met = True
            
            for condition in conditions:
                field = condition.get('field')
                operator = condition.get('operator')
                value = condition.get('value')
                
                # Extract field value from product data
                if field == 'product_type':
                    field_value = product.get('product_type')
                elif field == 'vendor':
                    field_value = product.get('vendor')
                elif field == 'tags':
                    field_value = product.get('tags', [])
                elif field == 'collection_id':
                    # Not directly available in product data, would need separate lookup
                    field_value = None
                else:
                    # Unknown field
                    field_value = None
                
                # Apply condition check
                if not self._check_condition(field_value, operator, value):
                    conditions_met = False
                    break
            
            if conditions_met:
                applicable_rules.append(rule)
        
        # Sort by priority (lower number = higher priority)
        applicable_rules.sort(key=lambda r: r.get('priority', 999))
        
        return applicable_rules
    
    def _check_condition(self, field_value, operator, value):
        """
        Check if a condition is satisfied.
        
        Args:
            field_value: The value extracted from the product
            operator (str): The comparison operator
            value: The value to compare against
            
        Returns:
            bool: True if condition is satisfied, False otherwise
        """
        if field_value is None:
            return False
        
        if operator == 'equals':
            return field_value == value
        elif operator == 'not_equals':
            return field_value != value
        elif operator == 'contains':
            if isinstance(field_value, list):
                return value in field_value
            return value in str(field_value)
        elif operator == 'not_contains':
            if isinstance(field_value, list):
                return value not in field_value
            return value not in str(field_value)
        elif operator == 'greater_than':
            return float(field_value) > float(value)
        elif operator == 'less_than':
            return float(field_value) < float(value)
        
        return False
    
    def calculate_new_price(self, product, variant, inventory_level, competitor_prices):
        """
        Calculate a new price for a product variant based on rules, inventory, and competition.
        
        Args:
            product (dict): Product data
            variant (dict): Variant data
            inventory_level (int): Current inventory level
            competitor_prices (list): Competitor price data
            
        Returns:
            float: Calculated new price
        """
        # Get current price
        current_price = float(variant.get('price', 0))
        
        # Start with current price as base
        new_price = current_price
        price_changed = False
        
        # Get applicable rules
        applicable_rules = self.get_applicable_rules(product)
        
        if not applicable_rules:
            logger.info(f"No pricing rules apply to product {product.get('id')}")
            return current_price
        
        # Apply each applicable rule in priority order
        for rule in applicable_rules:
            action = rule.get('action', {})
            action_type = action.get('type')
            
            # Apply different pricing strategies based on action type
            if action_type == 'fixed_price':
                new_price = float(action.get('value', new_price))
                price_changed = True
            
            elif action_type == 'percentage_adjustment':
                percentage = float(action.get('value', 0))
                new_price = new_price * (1 + percentage/100)
                price_changed = True
            
            elif action_type == 'fixed_adjustment':
                amount = float(action.get('value', 0))
                new_price = new_price + amount
                price_changed = True
            
            elif action_type == 'match_competitor':
                # Find the competitor to match
                competitor_to_match = action.get('competitor')
                offset_percentage = float(action.get('offset_percentage', 0))
                
                # Get the competitor's price
                for comp_price in competitor_prices:
                    if comp_price.get('competitor') == competitor_to_match:
                        competitor_price = float(comp_price.get('price', 0))
                        new_price = competitor_price * (1 + offset_percentage/100)
                        price_changed = True
                        break
            
            elif action_type == 'inventory_based':
                # Adjust price based on inventory level
                threshold = int(action.get('threshold', 0))
                low_adjustment = float(action.get('low_adjustment', 0))
                high_adjustment = float(action.get('high_adjustment', 0))
                
                if inventory_level <= threshold:
                    # Low inventory, potentially increase price
                    new_price = current_price * (1 + low_adjustment/100)
                else:
                    # High inventory, potentially decrease price
                    new_price = current_price * (1 + high_adjustment/100)
                
                price_changed = True
        
        # Apply safe guards to prevent extreme price changes
        if price_changed:
            # Get price limits from rules
            min_price = float(self.rules.get('global_settings', {}).get('min_price', 0))
            max_price = float(self.rules.get('global_settings', {}).get('max_price', 9999999))
            max_change_percent = float(self.rules.get('global_settings', {}).get('max_change_percent', 20))
            
            # Ensure price is within allowed range
            new_price = max(min_price, new_price)
            new_price = min(max_price, new_price)
            
            # Ensure price change is not too extreme
            max_allowed_change = current_price * (max_change_percent / 100)
            if abs(new_price - current_price) > max_allowed_change:
                if new_price > current_price:
                    new_price = current_price + max_allowed_change
                else:
                    new_price = current_price - max_allowed_change
            
            # Round to 2 decimal places
            new_price = round(new_price, 2)
        
        return new_price


def load_config():
    """
    Load configuration from YAML file.
    
    Returns:
        dict: Configuration settings
    """
    try:
        with open(CONFIG_FILE, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}


def run_pricing_update(shopify, monitor, engine):
    """
    Execute a pricing update run.
    
    Args:
        shopify (ShopifyConnector): Shopify API connector
        monitor (CompetitorMonitor): Competitor price monitor
        engine (PricingEngine): Pricing rules engine
        
    Returns:
        dict: Update statistics
    """
    logger.info("Starting pricing update run")
    
    # Get products from Shopify
    products = shopify.get_products()
    
    if not products:
        logger.warning("No products found to update")
        return {"products_processed": 0, "variants_updated": 0}
    
    stats = {
        "products_processed": 0,
        "variants_updated": 0,
        "price_increases": 0,
        "price_decreases": 0,
        "no_change": 0
    }
    
    # Process each product
    for product in products:
        product_id = product.get('id')
        product_type = product.get('product_type')
        
        # Get competitor prices
        competitor_prices = monitor.get_competitor_prices(product_id, product_type)
        
        # Get inventory item IDs for all variants
        inventory_item_ids = [
            variant.get('inventory_item_id') 
            for variant in product.get('variants', [])
            if variant.get('inventory_item_id')
        ]
        
        # Get inventory levels
        inventory_levels = shopify.get_inventory_levels(inventory_item_ids)
        
        # Process each variant
        for variant in product.get('variants', []):
            variant_id = variant.get('id')
            inventory_item_id = variant.get('inventory_item_id')
            current_price = float(variant.get('price', 0))
            
            # Get inventory level
            inventory_level = inventory_levels.get(inventory_item_id, 0)
            
            # Calculate new price
            new_price = engine.calculate_new_price(product, variant, inventory_level, competitor_prices)
            
            # Update price if changed
            if abs(new_price - current_price) >= 0.01:
                if shopify.update_product_price(product_id, variant_id, new_price):
                    stats["variants_updated"] += 1
                    
                    if new_price > current_price:
                        stats["price_increases"] += 1
                    else:
                        stats["price_decreases"] += 1
            else:
                stats["no_change"] += 1
        
        stats["products_processed"] += 1
    
    logger.info(f"Pricing update run completed: {stats}")
    return stats


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Dynamic Pricing System')
    parser.add_argument('--mode', choices=['once', 'daemon'], default='once',
                      help='Operation mode: run once or as a background daemon')
    parser.add_argument('--interval', type=int, default=60,
                      help='Update interval in minutes (for daemon mode)')
    parser.add_argument('--collection', type=str,
                      help='Process only products in a specific collection')
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # Initialize components
    shopify = ShopifyConnector(CREDENTIALS_FILE)
    monitor = CompetitorMonitor(SOURCES_FILE)
    engine = PricingEngine(RULES_FILE)
    
    if args.mode == 'once':
        logger.info("Running in single-run mode")
        run_pricing_update(shopify, monitor, engine)
    else:
        logger.info(f"Running in daemon mode with {args.interval} minute intervals")
        
        # Run immediately
        run_pricing_update(shopify, monitor, engine)
        
        # Schedule regular updates
        schedule.every(args.interval).minutes.do(
            run_pricing_update, shopify=shopify, monitor=monitor, engine=engine
        )
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(1)


if __name__ == "__main__":
    main() 