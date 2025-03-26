# Shopify-Grist Integration System

This project provides a bidirectional synchronization system between Shopify e-commerce platform and Grist databases, enabling seamless data flow for inventory, customers, and orders.

## Features

- **Customer Synchronization**: Automatically creates or updates customer records in Grist when orders are placed in Shopify
- **Order Data Management**: Syncs complete order details including tax information, shipping addresses, and payment status
- **Smart Duplicate Prevention**: Checks for existing records before creating new ones to avoid data duplication
- **ZIP Code Standardization**: Processes shipping ZIP codes for consistency in analytics and reporting

## Files

- `shopify_to_grist.py` - Core integration script for syncing Shopify orders and customers to Grist
- `shopify_grist_CustomerPhoenFF.py` - Enhanced customer data synchronization with phone number validation
- `Shop_Grist_OrderCheck_Payment.py` - Payment verification and processing
- `Shop_Grist_OrderCheck_Refund_Return.py` - Refund and return handling

## Requirements

```
shopify==13.0.0
grist-api==0.5.0
requests==2.28.1
```

## Setup

1. Create a Private App in your Shopify admin
2. Set up a Grist API key and document access
3. Configure the credentials in the scripts
4. Run the appropriate script based on your synchronization needs

## Usage

Basic usage:

```python
python shopify_to_grist.py
```

This will:
1. Fetch new orders from Shopify using GraphQL API
2. Check if customers already exist in Grist
3. Add new customers to Grist if needed
4. Add new orders to Grist with all relevant details
5. Report on the results

## Notes

- The scripts use pagination to handle large volumes of orders
- Rate limiting is implemented to avoid API throttling
- Error handling ensures the process continues even if individual records fail 