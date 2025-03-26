import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

# Shopify credentials and settings (replace with your own)
private_app_password = 'your_private_app_password' 
shop_url = "your-store.myshopify.com"
api_version = '2023-04'
graphql_url = f"https://{shop_url}/admin/api/{api_version}/graphql.json"

headers = {
    "Content-Type": "application/json",
    "X-Shopify-Access-Token": private_app_password
}


def generate_all_karat_weights_from_10k(sku_weight_dict_10k):
    """
    Generates estimated weights for 14K, 18K, 21K, and 22K gold in YG, RG, and WG,
    starting from a dictionary of 10KYG weights.
    
    Args:
        sku_weight_dict_10k: Dictionary mapping 10K gold SKUs to their weights
        
    Returns:
        Dictionary mapping all variant SKUs to their estimated weights
    """
    all_weights = {}
    karat_14k_multiplier = 1 / 0.89
    percentage_18k_increase = 0.18
    percentage_21k_increase = 0.28
    percentage_22k_increase = 0.30
    metal_colors = ['KYG', 'KRG', 'KWG']

    for sku_10k, weight_10k in sku_weight_dict_10k.items():
        base_sku = "-".join(sku_10k.split('-')[:-1])

        # Calculate 14K weight
        weight_14k_est = round(weight_10k * karat_14k_multiplier, 2)
        for color in metal_colors:
            sku_14k = f"{base_sku}-14{color}"
            all_weights[sku_14k] = weight_14k_est

        # Calculate 18K weight
        weight_18k_est = round(weight_14k_est * (1 + percentage_18k_increase), 2)
        for color in metal_colors:
            sku_18k = f"{base_sku}-18{color}"
            all_weights[sku_18k] = weight_18k_est

        # Calculate 21K weight
        weight_21k_est = round(weight_14k_est * (1 + percentage_21k_increase), 2)
        for color in metal_colors:
            sku_21k = f"{base_sku}-21{color}"
            all_weights[sku_21k] = weight_21k_est

        # Calculate 22K weight
        weight_22k_est = round(weight_14k_est * (1 + percentage_22k_increase), 2)
        for color in metal_colors:
            sku_22k = f"{base_sku}-22{color}"
            all_weights[sku_22k] = weight_22k_est

        # Include the original 10K weight
        all_weights[sku_10k] = weight_10k
    return all_weights


def estimate_weights_for_new_lengths(all_estimated_weights, new_lengths_inches):
    """
    Estimates weights for new lengths based on specific guidelines provided, and formats SKUs.

    Args:
        all_estimated_weights (dict): Dictionary of SKUs and their estimated weights.
        new_lengths_inches (list): List of new lengths in inches (e.g., ['8.0\'\'', '8.5\'\'] ).

    Returns:
        dict: Updated dictionary with weights estimated for new lengths, or None if error.
    """
    updated_weights = all_estimated_weights.copy()

    # Weight difference guidelines for different chain dimensions and lengths
    length_weight_diffs = {
        "3mm": {
            "8.0''": 0.3,  # heavier than 7.5''
            "8.5''": 0.62, # heavier than 7.5''
            "24''": 0.8,   # heavier than 22''
            "26''": 1.7,   # heavier than 22''
            "28''": 2.5,   # heavier than 22''
            "30''": 3.4    # heavier than 22''
        },
        "4mm": {
            "8.0''": 0.3,
            "8.5''": 0.62,
            "24''": 1.2,
            "26''": 2.5,
            "28''": 3.7,
            "30''": 4.9
        },
        "5mm": {
            "8.0''": 0.5,
            "8.5''": 1,
            "24''": 2,
            "26''": 4,
            "28''": 6.1,
            "30''": 8.2
        }
    }

    # Group SKUs by base SKU (excluding length)
    grouped_by_base_sku = {}
    for sku, weight in all_estimated_weights.items():
        parts = sku.split('-')
        mm_dimension = parts[3]  # e.g., "3mm", "4mm", "5mm"
        length_part = parts[2]   # e.g., "7.0''", "7.5''", "16''", "22''"
        base_sku = "-".join([parts[0], parts[1], parts[3], parts[4]])  # SKU without length, keep mm and karat

        if base_sku not in grouped_by_base_sku:
            grouped_by_base_sku[base_sku] = {}
        grouped_by_base_sku[base_sku][length_part] = weight

    # Calculate new weights for each base SKU and new length
    for base_sku_with_length, length_weights in grouped_by_base_sku.items():
        parts = base_sku_with_length.split('-')
        mm_dimension = parts[2]  # mm dimension from base_sku (which now excludes length)

        if mm_dimension not in length_weight_diffs:
            print(f"Warning: No weight differences defined for mm dimension: {mm_dimension}. Skipping base_sku group: {base_sku_with_length}")
            continue

        for new_length_inch in new_lengths_inches:
            if new_length_inch in length_weight_diffs[mm_dimension]:
                weight_difference = length_weight_diffs[mm_dimension][new_length_inch]
                reference_weight = 0

                # Determine reference length
                if new_length_inch in ["8.0''", "8.5''"]:
                    reference_length = "7.5''"
                elif new_length_inch in ["24''", "26''", "28''", "30''"]:
                    reference_length = "22''"
                else:
                    print(f"Warning: No reference length defined for new length: {new_length_inch}. Skipping.")
                    continue

                # Construct reference SKU
                reference_sku_parts = base_sku_with_length.split('-')
                reference_sku = "-".join([
                    reference_sku_parts[0],
                    reference_sku_parts[1], 
                    reference_length, 
                    reference_sku_parts[2], 
                    reference_sku_parts[3]
                ])

                # Calculate estimated weight if reference SKU exists
                if reference_sku in all_estimated_weights:
                    reference_weight = all_estimated_weights[reference_sku]
                    estimated_weight = round(reference_weight + weight_difference, 2)

                    # Construct new SKU
                    base_parts = base_sku_with_length.split('-')
                    mm_dimension_for_sku = base_parts[2]
                    karat_metal = base_parts[3]

                    new_sku = "-".join([
                        base_parts[0], 
                        base_parts[1], 
                        new_length_inch, 
                        mm_dimension_for_sku, 
                        karat_metal
                    ])
                    updated_weights[new_sku] = estimated_weight
                else:
                    print(f"Warning: Reference SKU {reference_sku} not found. Cannot estimate weight for {new_length_inch}")
            else:
                print(f"Warning: No weight difference defined for length {new_length_inch} and mm dimension {mm_dimension}. Skipping.")
                continue

    return updated_weights


def graphql_request(query, variables=None):
    """
    Makes a GraphQL request to the Shopify API.
    
    Args:
        query (str): The GraphQL query
        variables (dict, optional): Variables for the query
        
    Returns:
        dict: The response data
    """
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
        
    try:
        response = requests.post(graphql_url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making GraphQL request: {e}")
        return None


def retrieve_products():
    """
    Retrieves products and their variants from Shopify using GraphQL pagination.
    
    Returns:
        list: List of variant data including ID, SKU, and current weight
    """
    products = []
    has_next_page = True
    cursor = None
    
    while has_next_page:
        # GraphQL query to fetch products with variants
        query = """
        {
          products(first: 50%s) {
            pageInfo {
              hasNextPage
              endCursor
            }
            edges {
              node {
                id
                title
                variants(first: 100) {
                  edges {
                    node {
                      id
                      sku
                      weight
                      weightUnit
                    }
                  }
                }
              }
            }
          }
        }
        """ % (f', after: "{cursor}"' if cursor else '')
        
        response = graphql_request(query)
        if not response or "errors" in response:
            print("Error retrieving products:", response.get("errors", "Unknown error"))
            return []
            
        product_edges = response.get("data", {}).get("products", {}).get("edges", [])
        for product_edge in product_edges:
            products.append(product_edge["node"])
            
        page_info = response.get("data", {}).get("products", {}).get("pageInfo", {})
        has_next_page = page_info.get("hasNextPage", False)
        cursor = page_info.get("endCursor", None)
        
        # Respect API rate limits
        time.sleep(1)
        
    # Extract variant data
    variants = []
    for product in products:
        for variant_edge in product.get("variants", {}).get("edges", []):
            variant = variant_edge["node"]
            if variant.get("sku"):  # Only include variants with SKUs
                variants.append({
                    "id": variant["id"],
                    "sku": variant["sku"],
                    "weight": variant.get("weight"),
                    "weightUnit": variant.get("weightUnit")
                })
                
    return variants


def update_variant_weight(variant_id, weight):
    """
    Updates the weight of a variant using the Shopify GraphQL API.
    
    Args:
        variant_id (str): The ID of the variant
        weight (float): The new weight value
        
    Returns:
        bool: True if update was successful, False otherwise
    """
    mutation = """
    mutation productVariantUpdate($input: ProductVariantInput!) {
      productVariantUpdate(input: $input) {
        productVariant {
          id
          weight
          weightUnit
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
            "weight": weight,
            "weightUnit": "GRAMS"
        }
    }
    
    response = graphql_request(mutation, variables)
    if not response or "errors" in response:
        print(f"Error updating variant {variant_id}:", response.get("errors", "Unknown error"))
        return False
        
    user_errors = response.get("data", {}).get("productVariantUpdate", {}).get("userErrors", [])
    if user_errors:
        print(f"Error updating variant {variant_id}:", user_errors)
        return False
        
    return True


def main():
    """
    Main function to run the weight update process.
    
    1. Retrieves product variants from Shopify
    2. Identifies 10K gold variants with weights
    3. Calculates weights for all other variants
    4. Updates weights in Shopify
    """
    print("Starting weight update process...")
    
    # Retrieve all variants
    print("Retrieving product variants...")
    variants = retrieve_products()
    if not variants:
        print("No variants found or error retrieving variants.")
        return
    print(f"Retrieved {len(variants)} variants.")
    
    # Extract 10K gold variants with weights
    sku_weight_dict_10k = {}
    for variant in variants:
        sku = variant.get("sku", "")
        if sku and sku.endswith("-10KYG") and variant.get("weight"):
            sku_weight_dict_10k[sku] = float(variant.get("weight"))
    
    if not sku_weight_dict_10k:
        print("No 10K yellow gold variants with weights found.")
        return
    print(f"Found {len(sku_weight_dict_10k)} 10K yellow gold variants with weights.")
    
    # Generate weights for all karat variations
    print("Calculating weights for all karat variations...")
    all_estimated_weights = generate_all_karat_weights_from_10k(sku_weight_dict_10k)
    print(f"Generated weights for {len(all_estimated_weights)} variants.")
    
    # Add weights for new length variations
    print("Calculating weights for additional lengths...")
    new_lengths_inches = ["8.0''", "8.5''", "24''", "26''", "28''", "30''"]
    all_estimated_weights = estimate_weights_for_new_lengths(all_estimated_weights, new_lengths_inches)
    print(f"Final weight dictionary contains {len(all_estimated_weights)} variants.")
    
    # Create SKU to variant ID mapping
    sku_to_variant_id = {variant.get("sku"): variant.get("id") for variant in variants if variant.get("sku")}
    
    # Update variant weights in Shopify
    print("Updating variant weights in Shopify...")
    success_count = 0
    error_count = 0
    
    # Use ThreadPoolExecutor for parallel updates with rate limiting
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {}
        for sku, weight in all_estimated_weights.items():
            if sku in sku_to_variant_id:
                variant_id = sku_to_variant_id[sku]
                # Submit update task to executor
                future = executor.submit(update_variant_weight, variant_id, weight)
                futures[future] = sku
                # Sleep briefly to avoid rate limiting
                time.sleep(0.2)
            else:
                print(f"Warning: SKU {sku} not found in store variants. Skipping update.")
        
        # Process results as they complete
        for future in as_completed(futures):
            sku = futures[future]
            try:
                success = future.result()
                if success:
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                print(f"Error updating {sku}: {e}")
                error_count += 1
    
    print(f"Weight update process completed.")
    print(f"Successfully updated {success_count} variants.")
    print(f"Failed to update {error_count} variants.")


if __name__ == "__main__":
    main() 