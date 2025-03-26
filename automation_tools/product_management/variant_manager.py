import requests
import json
import re

# Shopify API configuration (replace with your own credentials)
SHOPIFY_SHOP = 'your-store.myshopify.com'
API_VERSION = '2023-04'
ACCESS_TOKEN = 'your_access_token'

HEADERS = {
    "Content-Type": "application/json",
    "X-Shopify-Access-Token": ACCESS_TOKEN
}

def get_product(product_id):
    """
    Fetch a product using its ID.
    
    Args:
        product_id (str): Shopify product ID
        
    Returns:
        dict: Product data or None if error
    """
    url = f"https://{SHOPIFY_SHOP}/admin/api/{API_VERSION}/products/{product_id}.json"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json().get("product")
    else:
        print(f"Error fetching product {product_id}: {response.text}")
        return None

def update_product(product_id, payload):
    """
    Update a product by its ID using a PUT request.
    
    Args:
        product_id (str): Shopify product ID
        payload (dict): Data to update
        
    Returns:
        bool: True if successful, False otherwise
    """
    url = f"https://{SHOPIFY_SHOP}/admin/api/{API_VERSION}/products/{product_id}.json"
    response = requests.put(url, headers=HEADERS, data=json.dumps(payload))
    if response.status_code == 200:
        print(f"Product {product_id} updated successfully.")
        return True
    else:
        print(f"Failed to update product {product_id}: {response.text}")
        return False

def delete_variant(variant_id):
    """
    Delete a variant using its ID.
    
    Args:
        variant_id (str): Shopify variant ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    url = f"https://{SHOPIFY_SHOP}/admin/api/{API_VERSION}/variants/{variant_id}.json"
    response = requests.delete(url, headers=HEADERS)
    if response.status_code in [200, 204]:
        print(f"Deleted duplicate variant {variant_id}.")
        return True
    else:
        print(f"Failed to delete variant {variant_id}: {response.text}")
        return False

def process_product_options(product, allowed_options, remove_option=None):
    """
    Process product options and variants according to specifications.
    
    Args:
        product (dict): Product data
        allowed_options (dict): Dictionary mapping option names to allowed values
        remove_option (str, optional): Name of option to remove
        
    Returns:
        dict: Updated product payload ready for API update
    """
    new_variants = []
    seen = {}  # Track duplicates
    
    # Prepare new options structure
    original_options = product.get("options", [])
    option_positions = {opt["name"]: i for i, opt in enumerate(original_options)}
    
    # Create mapping from position to option name
    pos_to_name = {}
    for opt in original_options:
        pos_to_name[opt["position"]] = opt["name"]
    
    # Determine which options to keep
    if remove_option:
        kept_options = [opt for opt in original_options if opt["name"] != remove_option]
        remove_position = option_positions.get(remove_option)
    else:
        kept_options = original_options.copy()
        remove_position = None
    
    # Update option values to allowed values only
    for i, option in enumerate(kept_options):
        if option["name"] in allowed_options:
            kept_options[i]["values"] = allowed_options[option["name"]]
    
    # Reindex positions
    for i, option in enumerate(kept_options):
        kept_options[i]["position"] = i + 1
    
    # Process variants
    for variant in product.get("variants", []):
        # Create new variant with filtered options
        new_variant = variant.copy()
        
        # Apply option filtering and removal
        option_key = []
        for pos in range(1, len(original_options) + 1):
            option_name = pos_to_name.get(pos)
            option_value = variant.get(f"option{pos}")
            
            # If removing this option, skip it
            if remove_position and pos == remove_position:
                if f"option{pos}" in new_variant:
                    del new_variant[f"option{pos}"]
                continue
                
            # If restricting values for this option
            if option_name in allowed_options:
                if option_value not in allowed_options[option_name]:
                    # Replace with first allowed value
                    option_value = allowed_options[option_name][0]
                    
            # Add to the key for deduplication
            option_key.append(option_value)
            
            # Reposition options if removing one
            if remove_position and pos > remove_position:
                new_pos = pos - 1
                new_variant[f"option{new_pos}"] = option_value
                if f"option{pos}" in new_variant:
                    del new_variant[f"option{pos}"]
            else:
                new_variant[f"option{pos if not remove_position or pos < remove_position else pos-1}"] = option_value
                
        # Check for duplicates after option changes
        key_tuple = tuple(option_key)
        if key_tuple in seen:
            # This variant would be a duplicate after changes
            delete_variant(variant["id"])
        else:
            seen[key_tuple] = variant["id"]
            new_variants.append(new_variant)
    
    # Create update payload
    payload = {
        "product": {
            "id": product["id"],
            "options": kept_options,
            "variants": new_variants
        }
    }
    
    return payload

def main():
    """Main execution function."""
    # Example product IDs
    product_id_1 = "8778656252131"    # Product 1
    product_id_2 = "8778654613731"   # Product 2
    
    # Example 1: Restrict metals to White Gold options only
    product_1 = get_product(product_id_1)
    if product_1:
        print(f"Processing {product_1.get('title', 'Unknown Product')}...")
        
        # Define allowed options for product 1
        allowed_options = {
            "Metal": ["10K White Gold", "14K White Gold"]
        }
        
        # Process product without removing any options
        payload = process_product_options(product_1, allowed_options)
        update_product(product_1["id"], payload)
    
    # Example 2: Remove 'Width' option and restrict metals
    product_2 = get_product(product_id_2)
    if product_2:
        print(f"Processing {product_2.get('title', 'Unknown Product')}...")
        
        # Define allowed options for product 2
        allowed_options = {
            "Metal": ["14K White Gold"]
        }
        
        # Process product and remove the "Width" option
        payload = process_product_options(product_2, allowed_options, remove_option="Width")
        update_product(product_2["id"], payload)

if __name__ == '__main__':
    main() 