import argparse
import sys
import os.path
import json
import datetime
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import google.oauth2.credentials
from google.oauth2.credentials import Credentials
from grist_api import GristDocAPI

# Configuration settings (replace with your own)
customer_id = "your_customer_id" 
CREDENTIALS_PATH = 'credentials/google-ads-credentials.json'
CLIENT_SECRET_PATH = 'credentials/client_secret.json'
SCOPES = ['https://www.googleapis.com/auth/adwords']

# Performance Max campaign IDs
performance_necklace_id = 'your_necklace_campaign_id'
performance_bracelet_id = 'your_bracelet_campaign_id'

# Date settings
end_date = datetime.datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
grist_date = datetime.datetime.now().strftime("%b - %Y")

# Revenue tracking
total_month = 0

# Grist database connection
SERVER = "https://your-grist-server.example.com"
DOC_ID = 'your_doc_id'
api_key = "your_api_key"
api = GristDocAPI(DOC_ID, server=SERVER, api_key=api_key)

# Data storage
campaign_data = {}
ad_group_data = {}
search_query_data = {}

# Fetch existing data from Grist
order_source_data = api.fetch_table("Order_Source")
google_ads_data = api.fetch_table("Google_AD")
google_ad_query_data = api.fetch_table("Google_AD_Query")
google_ad_campaign_data = api.fetch_table("Google_Campaign")

# Get current month revenue from Grist
month_rev_grist = 0
for data in order_source_data:
    if data.Month == str(grist_date):
        month_rev_grist = data.Google_Revenue

# Process existing Google Ads campaign data
google_ad_campaign = {}
for entry in google_ad_campaign_data:
    if entry.Month_Clean == str(grist_date):
        google_ad_campaign[entry.campaign_id] = {
            "id": entry.id,
        }    

# Process existing Google Ads ad group data
google_ads = {}
for entry in google_ads_data:
    if entry.Month_Clean == str(grist_date):
        google_ads[entry.Ad_Group_ID] = {
            "Ad_Group_Name": entry.Ad_Group_Name,
            "Campaign Name": entry.Campaign_Name,
            "id": entry.id,
        }    

# Process existing Google Ads query data
google_ads_query = {}
for entry in google_ad_query_data:
    google_ads_query[entry.Keyword_ID] = {
        "Search_Query": entry.Search_Query,
        "id": entry.id,
    }


def load_credentials():
    """
    Load OAuth2 credentials for Google Ads API.
    
    Returns:
        Credentials: OAuth2 credentials for Google Ads API
    """
    # Check if cached credentials exist
    if os.path.exists(CREDENTIALS_PATH):
        # Load cached credentials
        with open(CREDENTIALS_PATH, 'r') as f:
            credentials_data = json.load(f)
            credentials = Credentials(
                token=credentials_data['token'],
                refresh_token=credentials_data['refresh_token'],
                token_uri=credentials_data['token_uri'],
                client_id=credentials_data['client_id'],
                client_secret=credentials_data['client_secret'],
                scopes=credentials_data['scopes'],
            )
            # Refresh credentials if expired
            credentials.refresh(Request())
            with open(CREDENTIALS_PATH, 'w') as f:
                credentials_data['token'] = credentials.token
                json.dump(credentials_data, f)
            return credentials
    else:
        # Initialize the flow using the defined scopes
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, scopes=SCOPES)
        # Run the OAuth2 flow and obtain credentials
        credentials = flow.run_local_server()
        # Save obtained credentials to cache
        with open(CREDENTIALS_PATH, 'w') as f:
            credentials_data = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes
            }
            json.dump(credentials_data, f)
        return credentials


def fetch_campaign_data(googleads_client, customer_id, start_date, end_date, total_month=0):
    """
    Fetch campaign performance data from Google Ads API.
    
    Args:
        googleads_client: Google Ads API client
        customer_id: Google Ads customer ID
        start_date: Start date for data range (YYYY-MM-DD)
        end_date: End date for data range (YYYY-MM-DD)
        total_month: Running total of monthly conversion value
        
    Returns:
        tuple: (campaign_data dictionary, updated total_month value)
    """
    ga_service = googleads_client.get_service("GoogleAdsService")
    query = f"""
        SELECT
            campaign.id,
            campaign.name,
            metrics.clicks,
            metrics.impressions,
            metrics.ctr,
            metrics.cost_micros,
            metrics.conversions,
            metrics.conversions_value,
            metrics.search_impression_share,
            metrics.search_budget_lost_impression_share,
            metrics.average_cpc,
            metrics.average_cpm
        FROM campaign
        WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY campaign.id"""
    
    try:
        stream = ga_service.search_stream(customer_id=customer_id, query=query)
        for batch in stream:
            for row in batch.results:
                if row.metrics.cost_micros != 0:
                    # Handle Performance Max campaigns separately
                    if str(row.campaign.id) == performance_necklace_id:
                        campaign_data[str(row.campaign.id)] = {
                            "Ad_Group_Name": '(Performance Max Necklace)',
                            "Campaign_Name": row.campaign.name,
                            "Search_Impression_Share": row.metrics.search_impression_share,
                            "Search_Last_IS_budget_": row.metrics.search_budget_lost_impression_share,
                            "Clicks": row.metrics.clicks,
                            "Impressions": row.metrics.impressions,
                            "Conversions": row.metrics.conversions,
                            "Revenue": row.metrics.conversions_value,
                            "Spend": row.metrics.cost_micros/1000000,
                            "CPC2": row.metrics.average_cpc/1000000,
                            "CPM2": row.metrics.average_cpm/1000000,
                            "CTR2": row.metrics.ctr/1000000,
                        }
                    elif str(row.campaign.id) == performance_bracelet_id:
                        campaign_data[str(row.campaign.id)] = {
                            "Ad_Group_Name": '(Performance Max Bracelet)',
                            "Campaign_Name": row.campaign.name,
                            "Search_Impression_Share": row.metrics.search_impression_share,
                            "Clicks": row.metrics.clicks,
                            "Impressions": row.metrics.impressions,
                            "Conversions": row.metrics.conversions,
                            "Spend": row.metrics.cost_micros/1000000,
                            "Revenue": row.metrics.conversions_value,
                            "Search_Last_IS_budget_": row.metrics.search_budget_lost_impression_share,
                            "CPC2": row.metrics.average_cpc/1000000,
                            "CPM2": row.metrics.average_cpm/1000000,
                            "CTR2": row.metrics.ctr/1000000,
                        }
                    else:
                        campaign_data[str(row.campaign.id)] = {
                            "Campaign_Name": row.campaign.name,
                            "Search_Impression_Share": row.metrics.search_impression_share,
                            "Search_Last_IS_budget_": row.metrics.search_budget_lost_impression_share,
                            "CPC2": row.metrics.average_cpc/1000000,
                            "CPM2": row.metrics.average_cpm/1000000,
                            "CTR2": row.metrics.ctr/1000000,
                        }
                    total_month += row.metrics.conversions_value                                               
                else:
                    continue
        return campaign_data, total_month
                
    except GoogleAdsException as ex:
        print(f"Request failed with status {ex.error.code().name} and includes the following errors:")
        for error in ex.failure.errors:
            print(f"\tError with message: {error.message}")
            if error.location:
                for field_path_element in error.location.field_path_elements:
                    print(f"\t\tOn field: {field_path_element.field_name}")
        sys.exit(1)


def fetch_ad_group_data(googleads_client, customer_id, start_date, end_date):
    """
    Fetch ad group performance data from Google Ads API.
    
    Args:
        googleads_client: Google Ads API client
        customer_id: Google Ads customer ID
        start_date: Start date for data range (YYYY-MM-DD)
        end_date: End date for data range (YYYY-MM-DD)
        
    Returns:
        dict: Ad group performance data
    """
    ga_service = googleads_client.get_service("GoogleAdsService")
    query = f"""
        SELECT
            ad_group.id,
            ad_group.name,
            campaign.id,
            campaign.name,
            metrics.clicks,
            metrics.impressions,
            metrics.ctr,
            metrics.cost_micros,
            metrics.conversions,
            metrics.conversions_value,
            metrics.average_cpc
        FROM ad_group
        WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY ad_group.id"""
    
    try:
        stream = ga_service.search_stream(customer_id=customer_id, query=query)
        for batch in stream:
            for row in batch.results:
                if row.metrics.cost_micros != 0:
                    ad_group_data[str(row.ad_group.id)] = {
                        "Ad_Group_Name": row.ad_group.name,
                        "Campaign_Name": row.campaign.name,
                        "Campaign_ID": str(row.campaign.id),
                        "Clicks": row.metrics.clicks,
                        "Impressions": row.metrics.impressions,
                        "CTR": row.metrics.ctr,
                        "Cost": row.metrics.cost_micros/1000000,
                        "Conversions": row.metrics.conversions,
                        "Revenue": row.metrics.conversions_value,
                        "CPC": row.metrics.average_cpc/1000000,
                    }
                else:
                    continue
        return ad_group_data
                
    except GoogleAdsException as ex:
        print(f"Request failed with status {ex.error.code().name} and includes the following errors:")
        for error in ex.failure.errors:
            print(f"\tError with message: {error.message}")
            if error.location:
                for field_path_element in error.location.field_path_elements:
                    print(f"\t\tOn field: {field_path_element.field_name}")
        sys.exit(1)


def fetch_search_keyword_data(googleads_client, customer_id, start_date, end_date, month_rev_grist, total_month):
    """
    Fetch search query performance data from Google Ads API.
    
    Args:
        googleads_client: Google Ads API client
        customer_id: Google Ads customer ID
        start_date: Start date for data range (YYYY-MM-DD)
        end_date: End date for data range (YYYY-MM-DD)
        month_rev_grist: Current month revenue from Grist
        total_month: Total monthly conversion value
        
    Returns:
        dict: Search query performance data
    """
    ga_service = googleads_client.get_service("GoogleAdsService")
    query = f"""
        SELECT
            search_term_view.search_term,
            ad_group.id,
            ad_group.name,
            campaign.name,
            metrics.clicks,
            metrics.impressions,
            metrics.ctr,
            metrics.cost_micros,
            metrics.conversions,
            metrics.conversions_value,
            metrics.average_cpc
        FROM search_term_view
        WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY metrics.conversions_value DESC"""
    
    try:
        stream = ga_service.search_stream(customer_id=customer_id, query=query)
        for batch in stream:
            for row in batch.results:
                if row.metrics.cost_micros != 0:
                    search_query_data[row.search_term_view.search_term] = {
                        "Ad_Group_ID": str(row.ad_group.id),
                        "Ad_Group_Name": row.ad_group.name,
                        "Campaign_Name": row.campaign.name,
                        "Clicks": row.metrics.clicks,
                        "Impressions": row.metrics.impressions,
                        "CTR": row.metrics.ctr,
                        "Cost": row.metrics.cost_micros/1000000,
                        "Conversions": row.metrics.conversions,
                        "Revenue": row.metrics.conversions_value,
                        "CPC": row.metrics.average_cpc/1000000,
                    }
                else:
                    continue
        return search_query_data
                
    except GoogleAdsException as ex:
        print(f"Request failed with status {ex.error.code().name} and includes the following errors:")
        for error in ex.failure.errors:
            print(f"\tError with message: {error.message}")
            if error.location:
                for field_path_element in error.location.field_path_elements:
                    print(f"\t\tOn field: {field_path_element.field_name}")
        sys.exit(1)


def process_campaign(campaign_data):
    """
    Process campaign data and update Grist database.
    
    Args:
        campaign_data: Dictionary of campaign performance data
    """
    for campaign_id, campaign in campaign_data.items():
        try:
            ctr_percent = campaign.get("CTR2", 0) * 100
            roas = campaign.get("Revenue", 0) / campaign.get("Spend", 1) if campaign.get("Spend", 0) > 0 else 0
            profit = campaign.get("Revenue", 0) - campaign.get("Spend", 0)
            
            # Update or add record in Grist
            if campaign_id in google_ad_campaign:
                api.update_records("Google_Campaign", [google_ad_campaign[campaign_id]["id"]], {
                    "Search_Impression_Share": campaign.get("Search_Impression_Share", 0),
                    "Revenue": campaign.get("Revenue", 0),
                    "Spend": campaign.get("Spend", 0),
                    "Profit": profit,
                    "ROAS": roas,
                    "Clicks": campaign.get("Clicks", 0),
                    "Impressions": campaign.get("Impressions", 0),
                    "CTR": ctr_percent,
                    "CPC": campaign.get("CPC2", 0),
                    "CPM": campaign.get("CPM2", 0),
                    "Conversions": campaign.get("Conversions", 0),
                    "Search_Last_IS_budget_": campaign.get("Search_Last_IS_budget_", 0)
                })
            else:
                api.add_records("Google_Campaign", [{
                    "Campaign_Name": campaign.get("Campaign_Name", ""),
                    "campaign_id": campaign_id,
                    "Month_Clean": str(grist_date),
                    "Search_Impression_Share": campaign.get("Search_Impression_Share", 0),
                    "Revenue": campaign.get("Revenue", 0),
                    "Spend": campaign.get("Spend", 0),
                    "Profit": profit,
                    "ROAS": roas,
                    "Clicks": campaign.get("Clicks", 0),
                    "Impressions": campaign.get("Impressions", 0),
                    "CTR": ctr_percent,
                    "CPC": campaign.get("CPC2", 0),
                    "CPM": campaign.get("CPM2", 0),
                    "Conversions": campaign.get("Conversions", 0),
                    "Search_Last_IS_budget_": campaign.get("Search_Last_IS_budget_", 0)
                }])
        except Exception as e:
            print(f"Error processing campaign {campaign_id}: {e}")


def process_ad_group(ad_group_data, total_month, month_rev_grist):
    """
    Process ad group data and update Grist database.
    
    Args:
        ad_group_data: Dictionary of ad group performance data
        total_month: Total monthly conversion value
        month_rev_grist: Current month revenue from Grist
    """
    for ad_group_id, ad_group in ad_group_data.items():
        try:
            # Calculate metrics
            ctr_percent = ad_group.get("CTR", 0) * 100
            roas = ad_group.get("Revenue", 0) / ad_group.get("Cost", 1) if ad_group.get("Cost", 0) > 0 else 0
            profit = ad_group.get("Revenue", 0) - ad_group.get("Cost", 0)
            
            # Calculate adjusted revenue
            revenue_adj = 0
            if total_month > 0:
                revenue_adj = (ad_group.get("Revenue", 0) / total_month) * month_rev_grist if month_rev_grist > 0 else 0
            
            # Adjusted metrics
            roas_adj = revenue_adj / ad_group.get("Cost", 1) if ad_group.get("Cost", 0) > 0 else 0
            profit_adj = revenue_adj - ad_group.get("Cost", 0)
            
            # Update or add record in Grist
            if ad_group_id in google_ads:
                api.update_records("Google_AD", [google_ads[ad_group_id]["id"]], {
                    "Revenue": ad_group.get("Revenue", 0),
                    "Cost": ad_group.get("Cost", 0),
                    "Profit": profit,
                    "ROAS": roas,
                    "Revenue_Adj": revenue_adj,
                    "ROAS_Adj": roas_adj,
                    "Profit_Adj": profit_adj,
                    "Clicks": ad_group.get("Clicks", 0),
                    "Impressions": ad_group.get("Impressions", 0),
                    "CTR": ctr_percent,
                    "CPC": ad_group.get("CPC", 0),
                    "Conversions": ad_group.get("Conversions", 0),
                })
            else:
                api.add_records("Google_AD", [{
                    "Ad_Group_Name": ad_group.get("Ad_Group_Name", ""),
                    "Campaign_Name": ad_group.get("Campaign_Name", ""),
                    "Ad_Group_ID": ad_group_id,
                    "Month_Clean": str(grist_date),
                    "Revenue": ad_group.get("Revenue", 0),
                    "Cost": ad_group.get("Cost", 0),
                    "Profit": profit,
                    "ROAS": roas,
                    "Revenue_Adj": revenue_adj,
                    "ROAS_Adj": roas_adj,
                    "Profit_Adj": profit_adj,
                    "Clicks": ad_group.get("Clicks", 0),
                    "Impressions": ad_group.get("Impressions", 0),
                    "CTR": ctr_percent,
                    "CPC": ad_group.get("CPC", 0),
                    "Conversions": ad_group.get("Conversions", 0),
                }])
        except Exception as e:
            print(f"Error processing ad group {ad_group_id}: {e}")


def process_search_query(search_query_data, total_month, month_rev_grist):
    """
    Process search query data and update Grist database.
    
    Args:
        search_query_data: Dictionary of search query performance data
        total_month: Total monthly conversion value
        month_rev_grist: Current month revenue from Grist
    """
    for search_query, query_data in search_query_data.items():
        try:
            # Get the ad group name based on ad group ID
            ad_group_id = query_data.get("Ad_Group_ID", "")
            ad_group_name = query_data.get("Ad_Group_Name", "")
            
            # Calculate metrics
            ctr_percent = query_data.get("CTR", 0) * 100
            roas = query_data.get("Revenue", 0) / query_data.get("Cost", 1) if query_data.get("Cost", 0) > 0 else 0
            profit = query_data.get("Revenue", 0) - query_data.get("Cost", 0)
            
            # Calculate adjusted revenue
            revenue_adj = 0
            if total_month > 0:
                revenue_adj = (query_data.get("Revenue", 0) / total_month) * month_rev_grist if month_rev_grist > 0 else 0
            
            # Adjusted metrics
            roas_adj = revenue_adj / query_data.get("Cost", 1) if query_data.get("Cost", 0) > 0 else 0
            profit_adj = revenue_adj - query_data.get("Cost", 0)
            
            # Add record in Grist (always add new record for search queries)
            api.add_records("Google_AD_Query", [{
                "Search_Query": search_query,
                "Ad_Group_Name": ad_group_name,
                "Campaign_Name": query_data.get("Campaign_Name", ""),
                "Ad_Group_ID": ad_group_id,
                "Month_Clean": str(grist_date),
                "Revenue": query_data.get("Revenue", 0),
                "Cost": query_data.get("Cost", 0),
                "Profit": profit,
                "ROAS": roas,
                "Revenue_Adj": revenue_adj,
                "ROAS_Adj": roas_adj,
                "Profit_Adj": profit_adj,
                "Clicks": query_data.get("Clicks", 0),
                "Impressions": query_data.get("Impressions", 0),
                "CTR": ctr_percent,
                "CPC": query_data.get("CPC", 0),
                "Conversions": query_data.get("Conversions", 0),
            }])
        except Exception as e:
            print(f"Error processing search query {search_query}: {e}")


def main():
    """Main function to run the Google Ads analytics process."""
    print(f"Starting Google Ads analysis for period: {start_date} to {end_date}")
    print(f"Current month in Grist: {grist_date}")
    print(f"Current month revenue in Grist: ${month_rev_grist}")
    
    # Load credentials and initialize client
    credentials = load_credentials()
    googleads_client = GoogleAdsClient(credentials=credentials, developer_token='your_developer_token')
    
    # Fetch data from Google Ads API
    print("Fetching campaign data...")
    campaign_data, total_month = fetch_campaign_data(googleads_client, customer_id, start_date, end_date)
    print(f"Found {len(campaign_data)} campaigns")
    
    print("Fetching ad group data...")
    ad_group_data = fetch_ad_group_data(googleads_client, customer_id, start_date, end_date)
    print(f"Found {len(ad_group_data)} ad groups")
    
    print("Fetching search query data...")
    search_query_data = fetch_search_keyword_data(googleads_client, customer_id, start_date, end_date, month_rev_grist, total_month)
    print(f"Found {len(search_query_data)} search queries")
    
    # Process data and update Grist
    print("Processing campaign data and updating Grist...")
    process_campaign(campaign_data)
    
    print("Processing ad group data and updating Grist...")
    process_ad_group(ad_group_data, total_month, month_rev_grist)
    
    print("Processing search query data and updating Grist...")
    process_search_query(search_query_data, total_month, month_rev_grist)
    
    print("Google Ads analysis completed successfully!")
    print(f"Total conversion value from Google Ads: ${total_month}")
    print(f"Total revenue in Grist: ${month_rev_grist}")


if __name__ == "__main__":
    main() 