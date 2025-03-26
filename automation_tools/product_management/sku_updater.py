import requests
import json
import os

# ----------------------------------------------------------------
# 1) Shopify credentials (replace with your own)
# ----------------------------------------------------------------
SHOPIFY_ACCESS_TOKEN = "your_shopify_access_token"
SHOPIFY_STORE_NAME = "your-store-name"
SHOPIFY_API_VERSION = "2023-10"

# ----------------------------------------------------------------
# 2) Cache Setup
# ----------------------------------------------------------------
CACHE_FILE = "products.json"  # Local file to cache product data

def save_to_cache(data):
    """Save product data to a local JSON file."""
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_from_cache():
    """Load product data from a local JSON file."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return None

# ----------------------------------------------------------------
# 3) GraphQL Query to Fetch Products
# ----------------------------------------------------------------
def fetch_products_graphql():
    """Fetch all products with pagination using GraphQL."""
    url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/{SHOPIFY_API_VERSION}/graphql.json"
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN
    }
    query = """
    query ($cursor: String) {
      products(first: 250, after: $cursor, query: "title:*Example QUERY*") {
        pageInfo {
          hasNextPage
        }
        edges {
          cursor
          node {
            id
            title
            variants(first: 250) {
              edges {
                node {
                  id
                  title
                  sku
                  selectedOptions {
                    name
                    value
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    products = []
    variables = {}
    cursor = None

    while True:
        if cursor:
            variables["cursor"] = cursor
        payload = {"query": query, "variables": variables}
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()

        if 'errors' in data:
            print(f"Error: {data['errors']}")
            break

        edges = data['data']['products']['edges']
        for edge in edges:
            products.append(edge['node'])

        has_next_page = data['data']['products']['pageInfo']['hasNextPage']
        if has_next_page:
            cursor = edges[-1]['cursor']
        else:
            break

    save_to_cache(products)
    return products

# ----------------------------------------------------------------
# 4) SKU Logic
# ----------------------------------------------------------------
def generate_sku(title, option1, option2, option3):
    """
    Generate SKU based on product title and variant options.
    
    Args:
        title (str): Product title
        option1 (str): First variant option (e.g. size)
        option2 (str): Second variant option (e.g. color)
        option3 (str): Third variant option (e.g. material)
        
    Returns:
        str: Generated SKU following the pattern PREFIX-OPTION1-OPTION2OPTION3[-B]
    """
    # Map of product titles to SKU prefixes
    prefix_map = {
        "Test Product 1": "T1-PRDCT",
    }
    
    # Remove the last word from the title (usually a size indicator)
    title_modified = " ".join(title.split(" ")[:-1])
    
    # Get the prefix from the map, or raise an error if not found
    prefix = prefix_map.get(title_modified, "UNKNOWN")
    if prefix == "UNKNOWN":
        raise ValueError(f"Unknown product title: {title_modified}")

    # Add a -B suffix for black edition products
    if 'black' in title_modified.lower():
        return f"{prefix}-{option1}-{option2}{option3}-B"
    else:
        return f"{prefix}-{option1}-{option2}{option3}"

# ----------------------------------------------------------------
# 5) Update Function
# ----------------------------------------------------------------
def update_product(variant_id, sku_new):
    """
    Update only the SKU of a specific variant using GraphQL.
    
    Args:
        variant_id (str): ID of the variant to update
        sku_new (str): New SKU to assign
        
    Returns:
        bool: True if update was successful, False otherwise
    """
    url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/{SHOPIFY_API_VERSION}/graphql.json"
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN
    }

    mutation = """
    mutation updateVariant($input: ProductVariantInput!) {
      productVariantUpdate(input: $input) {
        productVariant {
          id
          sku
        }
        userErrors {
          field
          message
        }
      }
    }
    """

    variables = {
        "input": {
            "id": variant_id,
            "sku": sku_new
        }
    }

    payload = {"query": mutation, "variables": variables}
    response = requests.post(url, headers=headers, json=payload)
    data = response.json()

    if 'errors' in data:
        print(f"Error: {data['errors']}")
        return False
    elif data['data']['productVariantUpdate']['userErrors']:
        print(f"User Errors: {data['data']['productVariantUpdate']['userErrors']}")
        return False
    else:
        print(f"Success: Updated variant {variant_id} with SKU {sku_new}")
        return True

# ----------------------------------------------------------------
# 6) Main Logic
# ----------------------------------------------------------------
def main():
    """
    Main function to orchestrate the SKU update process.
    
    1. Loads products from cache if available, otherwise fetches from Shopify
    2. For each product, processes all its variants:
        - Extracts option values
        - Generates a new SKU based on the product title and option values
        - Updates the SKU in Shopify if it's different from the current one
    """
    # Try to load products from cache first
    all_products = load_from_cache()
    if not all_products:
        print("Fetching products via GraphQL API...")
        all_products = fetch_products_graphql()
    else:
        print("Loaded products from cache.")

    # Process each product
    update_count = 0
    error_count = 0
    
    for p in all_products:
        title = p.get("title", "")
        # Skip black edition products in this run (can be modified based on needs)
        if "black" not in title.lower():
            product_id = p["id"]
            print(f"Processing product: {title} ({product_id})")
            
            variants = p.get("variants", {}).get("edges", [])
            for v in variants:
                variant = v['node']
                variant_id = variant['id']
                
                # Extract option values
                options = variant['selectedOptions']
                # Make sure we have 3 options, as expected by our SKU format
                if len(options) < 3:
                    print(f"  Skipping variant {variant_id} - insufficient options")
                    continue
                    
                option1 = options[0]['value']
                option2 = options[1]['value']
                option3 = options[2]['value']

                try:
                    # Generate the new SKU
                    sku_new = generate_sku(title, option1, option2, option3)
                    
                    # If the SKU has changed, update it
                    current_sku = variant.get('sku', '')
                    if current_sku != sku_new:
                        print(f"  Updating variant {variant_id}: {current_sku} → {sku_new}")
                        
                        # Uncomment this line to actually update in Shopify
                        # success = update_product(variant_id, sku_new)
                        success = True  # For demo purposes
                        
                        if success:
                            update_count += 1
                        else:
                            error_count += 1
                except ValueError as e:
                    print(f"  Error: {e}")
                    error_count += 1

    print(f"Processing completed. Updated {update_count} SKUs with {error_count} errors.") 
