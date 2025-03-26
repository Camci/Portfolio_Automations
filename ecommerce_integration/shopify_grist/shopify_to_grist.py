import logging
import os
import json
import requests
import time
from datetime import datetime
from grist_api import GristDocAPI
import shopify


# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Configuration - replace with your own credentials
SERVER = "https://your-grist-server.example.com"
grist_api = "your_grist_api_key"
DOC_ID = "your_document_id"
private_app_password = "your_shopify_private_app_password"
shop_url = "your-store.myshopify.com"
api_version = '2023-04'

all_orders = []
start_time = datetime.now()

api = GristDocAPI(DOC_ID, server=SERVER, api_key=grist_api)

customer_Table = "Customers"
order_Table = "Orders"

grist_data_customer = api.fetch_table(customer_Table)
grist_data_order = api.fetch_table(order_Table)


def shopify_client():
    """
    Initialize and return a Shopify GraphQL client
    """
    api_session = shopify.Session(shop_url, api_version, private_app_password)
    time.sleep(2)
    shopify.ShopifyResource.activate_session(api_session)
    time.sleep(2)
    client = shopify.GraphQL()
    return client


# Example cursor - you would use your own when running the script
order_cursor = "example_cursor_value"


def graphQL(cursor, all_orders):
    """
    Execute a GraphQL query to fetch orders from Shopify
    
    Args:
        cursor: Pagination cursor
        all_orders: List to append orders to
        
    Returns:
        Next cursor if more pages exist, None otherwise
    """
    query = """
    {
      orders(after: "%s", first: 248) {
        pageInfo {
          endCursor
          hasNextPage
        }
        edges {
          cursor
          node {
            createdAt
            id
            name
            customer {
              firstName
              lastName
            }
            taxLines {
              rate
            }
            shippingAddress {
              zip
            }
          }
        }
      }
    }
    """ % (cursor)
    time.sleep(2)
    client = shopify_client()
    try:
        time.sleep(5)
        response = json.loads(client.execute(query))
        time.sleep(5)
        # Extract orders from the response
        
        orders = response.get("data", {}).get("orders", {}).get("edges", [])

        time.sleep(5)

        # Add the orders to the list
        all_orders.extend(orders)
        time.sleep(5)
        
        # Check if there are more pages
        page_info = response.get("data", {}).get("orders", {}).get("pageInfo", {})
        logging.debug("Page info: %s", page_info)
        if page_info.get("hasNextPage"):
            next_cursor = page_info.get("endCursor")
            return next_cursor
        else:
            return None
    except Exception as e:
        logging.error("An error occurred during GraphQL request: %s", str(e))
        return None


# Initial call
next_cursor = graphQL(order_cursor, all_orders)


# Fetch all pages
while next_cursor:
    time.sleep(2)
    next_cursor = graphQL(next_cursor, all_orders)


def grist():
    """
    Prepare data structures from Grist tables
    
    Returns:
        Tuple of (customer list, order list) from Grist
    """
    nested_list_customer = []
    nested_dict_orders = []
    
    def customer_nested(data_customer):
        """Process customer data for comparison"""
        for i in range(len(data_customer)):
            lower = data_customer[i].Name.lower()
            nested_list_customer.append(lower.replace(" ", ""))

        return nested_list_customer

    def order_customer_grist(data_order):
        """Extract order numbers from order data"""
        for i in range(0, len(data_order)):
            order_number = data_order[i].Order_
            nested_dict_orders.append(order_number)
        return nested_dict_orders

    a = customer_nested(grist_data_customer)
    b = order_customer_grist(grist_data_order)

    return a, b

def remove_zip_suffix(zip_code):
    """
    Remove suffix from ZIP code (e.g., 12345-6789 -> 12345)
    
    Args:
        zip_code: ZIP code string
        
    Returns:
        ZIP code without suffix
    """
    if zip_code is not None:
        if '-' in zip_code:
            parts = zip_code.split('-')
            zip_without_suffix = parts[0]
            return zip_without_suffix
        else:
            return zip_code
    return ""

# Get existing data from Grist
grist_customerList, grist_orderCustomerDict = grist()


# Process orders and update Grist
for i in range(0, len(all_orders)):
    # Extract order number (remove leading # character)
    orderNumber = int(all_orders[i]['node']['name'].lstrip('#'))
    
    # Format date
    date_object = datetime.strptime(all_orders[i]['node']['createdAt'], "%Y-%m-%dT%H:%M:%SZ")
    orderDate = date_object.strftime("%m-%d-%Y")
    
    # Calculate total tax rate
    total_tax_rate = 0.0
    tax_lines = all_orders[i].get("node", {}).get("taxLines", [])
    
    # Get shipping address ZIP code
    shipping_address = all_orders[i].get("node", {}).get("shippingAddress", {})
    zip_code = remove_zip_suffix(shipping_address.get("zip", ""))
    
    for tax_line in tax_lines:
        tax_rate = tax_line.get("rate", 0.0)
        total_tax_rate += tax_rate
    
    # Handle customer name, with fallbacks for missing data
    if all_orders[i]['node']['customer']['firstName'] is not None:
        first_name = all_orders[i]['node']['customer']['firstName'].strip()
    else:
        first_name = " "
        
    if all_orders[i]['node']['customer']['lastName'] is not None:  
        last_name = all_orders[i]['node']['customer']['lastName'].strip()
    else:
        last_name = " "

    # Format customer name
    customerName_space = f"{first_name} {last_name}"
    customerName_space = customerName_space.title()
    customerName_space_l = customerName_space.replace(" ", "")

    # Add customer if doesn't exist
    if customerName_space_l.lower() not in grist_customerList:
        api.add_records(customer_Table, [{'Name': customerName_space}])
        grist_customerList.append(customerName_space_l.lower())
      
        # Add order if it doesn't exist
        if orderNumber not in grist_orderCustomerDict:
            if total_tax_rate != 0.0:
                api.add_records("Orders", [{"Order_": orderNumber, 
                                           "Customer_Name": customerName_space, 
                                           "Date": orderDate, 
                                           "Tax_": total_tax_rate, 
                                           "Tax": True, 
                                           "Zip_Code2": zip_code}])
            else:
                api.add_records("Orders", [{"Order_": orderNumber, 
                                           "Customer_Name": customerName_space, 
                                           "Date": orderDate, 
                                           "Zip_Code2": zip_code}])
    else:
        # Customer exists but order might not
        if orderNumber not in grist_orderCustomerDict:
            if total_tax_rate != 0.0:
                api.add_records("Orders", [{"Order_": orderNumber, 
                                           "Customer_Name": customerName_space, 
                                           "Date": orderDate, 
                                           "Tax_": total_tax_rate, 
                                           "Tax": True, 
                                           "Zip_Code2": zip_code}])
            else:
                api.add_records("Orders", [{"Order_": orderNumber, 
                                           "Customer_Name": customerName_space, 
                                           "Date": orderDate, 
                                           "Zip_Code2": zip_code}])
         

# Clean up session and report completion
end_time = datetime.now()
shopify.ShopifyResource.clear_session()
print("Sync completed successfully!", 'Duration: {}'.format(end_time - start_time)) 