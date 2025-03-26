from datetime import datetime, timedelta
import pytz
import requests
from requests.structures import CaseInsensitiveDict
import json
from grist_api import GristDocAPI


# Grist API configuration (replace with your own credentials)
SERVER = "https://your-grist-server.example.com"
DOC_ID = "your_document_id"
api_key = "your_api_key"

# Initialize Grist API client
api = GristDocAPI(DOC_ID, server=SERVER, api_key=api_key)

# Table and column configuration
table_name = 'Gold_Spot_Prices'
column_gold = 'Gold_Spot_Price'
column_time = 'Date'

# Fetch current gold price data from Grist
gold_table = api.fetch_table(table_name)

# Set date range for historical data
end_date = datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

# Metals API configuration (replace with your own API key)
metals_api_key = "your_metals_api_key"
url_time_series = f"https://api.metals.dev/v1/timeseries?api_key={metals_api_key}&start_date={start_date}&end_date={end_date}"
url_spot = f"https://api.metals.dev/v1/metal/spot?api_key={metals_api_key}&metal=gold&currency=USD"

# Set request headers
headers = CaseInsensitiveDict()
headers["Accept"] = "application/json"


def update_historical_prices():
    """
    Update historical gold prices in Grist database.
    Fetches time series data and adds any missing dates.
    """
    try:
        # Fetch historical gold price data
        resp = requests.get(url_time_series, headers=headers)
        resp.raise_for_status()  # Raise exception for HTTP errors
        response_data = resp.json()
        
        print(f"Retrieved historical gold prices from {start_date} to {end_date}")
        
        # Track how many records were added
        records_added = 0
        
        # Iterate over the dates in the response
        for date, data in response_data['rates'].items():
            # Extract the gold price for the day
            gold_spot_price = data['metals']['gold']
            
            # Check if the date is not already in the Grist table
            if not any(entry.Date == date for entry in gold_table):
                # Insert the data into the Grist table
                api.add_records(table_name, [{
                    "Date": date,
                    "Gold_Spot_Price": gold_spot_price
                }])
                records_added += 1
                print(f"Added gold price for {date}: ${gold_spot_price}")
                
        print(f"Added {records_added} new gold price records to Grist")
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching historical gold prices: {e}")
        
        
def get_current_spot_price():
    """
    Get the current spot price of gold from the Metals API.
    
    Returns:
        float: Current gold spot price
    """
    try:
        resp = requests.get(url_spot, headers=headers)
        resp.raise_for_status()
        spot_data = resp.json()
        
        # Extract the current gold price
        current_price = spot_data['rates']['gold']
        print(f"Current gold spot price: ${current_price}")
        return current_price
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching current gold spot price: {e}")
        return None


def update_product_prices(current_gold_price, base_gold_price=1800.0, update_threshold_percent=2.0):
    """
    Update product prices based on gold price changes.
    
    Args:
        current_gold_price (float): Current gold price
        base_gold_price (float): Reference gold price for calculations
        update_threshold_percent (float): Minimum percent change to trigger updates
    """
    # Calculate price change percentage
    price_change_percent = ((current_gold_price - base_gold_price) / base_gold_price) * 100
    
    # Only update prices if change exceeds threshold
    if abs(price_change_percent) >= update_threshold_percent:
        print(f"Gold price change of {price_change_percent:.2f}% exceeds threshold, updating product prices")
        
        # Here you would add logic to update product prices in your e-commerce platform
        # Example: Fetch products, calculate new prices, update via API
        
        # For demonstration purposes:
        print(f"Would update prices by factor of {current_gold_price/base_gold_price:.4f}")
    else:
        print(f"Gold price change of {price_change_percent:.2f}% does not exceed threshold, no updates needed")


def main():
    """Main function to run the gold price update process."""
    print("Starting gold price update process...")
    
    # Update historical prices in Grist
    update_historical_prices()
    
    # Get current spot price
    current_price = get_current_spot_price()
    
    if current_price:
        # Get the latest base price from Grist (e.g., from 30 days ago)
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        base_prices = [entry for entry in gold_table if entry.Date <= thirty_days_ago]
        
        if base_prices:
            # Use the most recent base price available
            base_prices.sort(key=lambda x: x.Date, reverse=True)
            base_price = base_prices[0].Gold_Spot_Price
            print(f"Using base gold price from {base_prices[0].Date}: ${base_price}")
            
            # Update product prices based on gold price changes
            update_product_prices(current_price, base_price)
        else:
            print("No base price available for comparison")
    
    print("Gold price update process completed")


if __name__ == "__main__":
    main() 