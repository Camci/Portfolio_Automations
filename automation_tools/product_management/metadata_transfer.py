import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm  # For progress tracking

# -------------------------------------
# Configuration
# -------------------------------------
# Shopify credentials (replace with your own)
STORE_URL = "your-store.myshopify.com"
ADMIN_API_TOKEN = "your_admin_api_token"

# Path to your CSV file
INPUT_CSV_FILE = "products_export.csv"

# Thread pool concurrency
MAX_WORKERS = 5

# Enable debug logs
DEBUG = True

# -------------------------------------
# GraphQL Query Function
# -------------------------------------
def get_variant_metafield_by_sku(sku, namespace="custom", key="weight"):
    """
    Query the Shopify Admin GraphQL API for a specific metafield value of a variant.
    
    Args:
        sku (str): SKU of the variant to query
        namespace (str): Metafield namespace
        key (str): Metafield key
        
    Returns:
        str: Metafield value or None if not found/error
    """
    if not sku:
        return None
    
    url = f"https://{STORE_URL}/admin/api/2023-07/graphql.json"
    headers = {
        "X-Shopify-Access-Token": ADMIN_API_TOKEN,
        "Content-Type": "application/json",
    }

    query = """
    query($sku: String!, $namespace: String!, $key: String!) {
      productVariants(first: 1, query: $sku) {
        edges {
          node {
            metafield(namespace: $namespace, key: $key) {
              value
            }
          }
        }
      }
    }
    """

    payload = {
        "query": query,
        "variables": {"sku": sku, "namespace": namespace, "key": key}
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Debug output for the query and response
        if DEBUG:
            print(f"SKU={sku} Response: {data}")

        # Navigate to the metafield
        edges = data.get("data", {}).get("productVariants", {}).get("edges", [])
        if edges:
            metafield = edges[0]["node"].get("metafield", {})
            if metafield:
                return metafield.get("value")
    except requests.exceptions.RequestException as e:
        print(f"Request error for SKU={sku}: {e}")

    return None

# -------------------------------------
# Main Script
# -------------------------------------
def main():
    """
    Main function to process CSV file and add metafield values.
    
    The process:
    1. Read the CSV file
    2. For each unique SKU, query Shopify for the metafield value
    3. Update the CSV with the metafield values
    4. Save the updated CSV
    """
    print(f"Reading CSV file: {INPUT_CSV_FILE}")
    
    # 1. Read the CSV file into a DataFrame
    df = pd.read_csv(INPUT_CSV_FILE)

    # 2. Add the new column for metafield data (initially None)
    metafield_column = "Variant Weight"
    df[metafield_column] = None

    # 3. Get unique SKUs to avoid querying duplicates
    skus = df["Variant SKU"].dropna().unique().tolist()
    print(f"Found {len(skus)} unique SKUs to process")

    sku_metafield_map = {}

    # 4. Submit parallel tasks with progress tracking
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(get_variant_metafield_by_sku, sku): sku for sku in skus}

        with tqdm(total=len(futures), desc=f"Fetching {metafield_column}", unit="SKU") as pbar:
            for future in as_completed(futures):
                sku = futures[future]
                try:
                    metafield_value = future.result()
                    sku_metafield_map[sku] = metafield_value

                    # Debug output for mapping
                    if DEBUG:
                        print(f"SKU={sku} -> {metafield_column}={metafield_value}")
                except Exception as e:
                    print(f"Error processing SKU={sku}: {e}")
                finally:
                    pbar.update(1)

    # 5. Map the retrieved metafield values back to the DataFrame rows
    df[metafield_column] = df["Variant SKU"].map(lambda s: sku_metafield_map.get(s, None))

    # Debug output for DataFrame
    if DEBUG:
        print(f"Updated DataFrame:\n{df.head()}")

    # 6. Save the updated CSV
    output_file = f"updated_{INPUT_CSV_FILE}"
    df.to_csv(output_file, index=False)
    print(f"Updated CSV saved to {output_file} with new '{metafield_column}' column.")
    
    # 7. Print summary statistics
    total_updated = df[metafield_column].notnull().sum()
    print(f"Summary: {total_updated} of {len(df)} rows updated with {metafield_column} values.")

if __name__ == "__main__":
    main() 