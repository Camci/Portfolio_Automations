# Google Ads Analytics System

This project provides a comprehensive solution for retrieving, analyzing, and storing Google Ads performance data. It integrates with Grist database for persistent storage and reconciliation with actual revenue figures.

## Features

- **Campaign Performance Analysis**: Tracks impressions, clicks, conversions, costs, and revenue at the campaign level
- **Ad Group Analysis**: Detailed metrics for each ad group with performance indicators
- **Search Query Tracking**: Monitors which search terms are driving traffic and conversions
- **Revenue Reconciliation**: Adjusts Google Ads reported conversions against actual tracked revenue
- **Performance Max Campaign Support**: Special handling for Performance Max campaigns
- **ROAS & Profitability Metrics**: Calculates return on ad spend and profit for all levels of data
- **Automated OAuth2 Authentication**: Handles Google API authentication with token refresh

## Components

- `google_ads_analyzer.py` - Main script for retrieving and processing Google Ads data
- `credentials/` - Directory for storing authentication credentials

## Key Metrics Calculated

- **Basic Performance**: Clicks, Impressions, CTR, CPC, CPM
- **Conversion Metrics**: Conversions, Conversion Value
- **Financial Metrics**: 
  - Revenue: Directly from Google Ads
  - Adjusted Revenue: Reconciled with actual sales data
  - ROAS: Return on ad spend (Revenue ÷ Cost)
  - Adjusted ROAS: Using reconciled revenue
  - Profit: Revenue - Cost
  - Adjusted Profit: Using reconciled revenue
- **Visibility Metrics**: 
  - Search Impression Share
  - Lost Impression Share (Budget)

## Requirements

```
google-ads==18.0.0
google-auth-oauthlib==0.4.6
google-auth==2.6.0
grist-api==0.5.0
```

## Setup

1. Create a Google Ads Developer token
2. Set up OAuth credentials in the Google Cloud Console
3. Configure Grist API access
4. Update the configuration settings in the script
5. Run the script to authenticate and start analyzing data

## Usage

Basic usage:

```bash
python google_ads_analyzer.py
```

This will:
1. Authenticate with Google Ads API
2. Retrieve campaign, ad group, and search query data for the specified date range
3. Calculate performance metrics and adjust revenue based on actual sales data
4. Update the Grist database with the latest performance data

## Customization

The script can be customized to:
- Track different metrics by modifying the GraphQL queries
- Adjust the date range for analysis
- Add additional dimensions for more detailed reporting
 