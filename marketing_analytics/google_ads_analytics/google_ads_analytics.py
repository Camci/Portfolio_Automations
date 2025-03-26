#!/usr/bin/env python3
"""
Google Ads Analytics System

A comprehensive toolkit for Google Ads data analysis and visualization, enabling
data-driven marketing decisions and campaign optimization.
"""

import os
import sys
import yaml
import json
import logging
import argparse
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('google_ads_analytics.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("google-ads-analytics")

# Configuration paths
CONFIG_FILE = "config.yaml"
CREDENTIALS_FILE = "credentials.json"
OUTPUT_DIR = "reports"
CACHE_DIR = ".cache"

class GoogleAdsConnector:
    """Handles authentication and data retrieval from Google Ads API."""
    
    def __init__(self, credentials_path):
        """
        Initialize the Google Ads API client.
        
        Args:
            credentials_path (str): Path to the credentials JSON file
        """
        self.client = None
        self.credentials_path = credentials_path
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Google Ads API client using credentials."""
        try:
            # Load credentials from file
            with open(self.credentials_path, 'r') as f:
                credentials = json.load(f)
            
            # Create credentials configuration for GoogleAdsClient
            client_config = {
                "client_id": credentials.get("client_id"),
                "client_secret": credentials.get("client_secret"),
                "refresh_token": credentials.get("refresh_token"),
                "developer_token": credentials.get("developer_token"),
                "login_customer_id": credentials.get("login_customer_id")
            }
            
            # Initialize client
            self.client = GoogleAdsClient.load_from_dict(client_config)
            logger.info("Successfully initialized Google Ads client")
        except Exception as e:
            logger.error(f"Failed to initialize Google Ads client: {e}")
            sys.exit(1)
    
    def get_customer_ids(self):
        """
        Get a list of accessible customer IDs.
        
        Returns:
            list: List of customer IDs
        """
        customer_service = self.client.get_service("CustomerService")
        accessible_customers = customer_service.list_accessible_customers()
        
        customer_ids = []
        
        # Extract customer IDs from resource names
        for resource_name in accessible_customers.resource_names:
            customer_id = resource_name.split('/')[-1]
            customer_ids.append(customer_id)
        
        return customer_ids
    
    def get_campaigns(self, customer_id):
        """
        Get campaigns for a specific customer ID.
        
        Args:
            customer_id (str): Google Ads customer ID
            
        Returns:
            list: List of campaign data dictionaries
        """
        ga_service = self.client.get_service("GoogleAdsService")
        
        query = """
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.advertising_channel_type,
                campaign.bidding_strategy_type,
                campaign.start_date,
                campaign.end_date,
                campaign.serving_status,
                campaign_budget.amount_micros
            FROM campaign
            WHERE campaign.status != 'REMOVED'
            ORDER BY campaign.id
        """
        
        try:
            stream = ga_service.search_stream(customer_id=customer_id, query=query)
            
            campaigns = []
            
            # Process the results
            for batch in stream:
                for row in batch.results:
                    campaign = row.campaign
                    budget = row.campaign_budget
                    
                    campaign_data = {
                        "id": campaign.id,
                        "name": campaign.name,
                        "status": campaign.status,
                        "channel_type": campaign.advertising_channel_type,
                        "bidding_strategy": campaign.bidding_strategy_type,
                        "start_date": campaign.start_date,
                        "end_date": campaign.end_date,
                        "serving_status": campaign.serving_status,
                        "budget": budget.amount_micros / 1000000 if budget.amount_micros else 0
                    }
                    
                    campaigns.append(campaign_data)
            
            return campaigns
        
        except GoogleAdsException as ex:
            logger.error(f"Request with ID '{ex.request_id}' failed with status '{ex.error.code().name}'")
            for error in ex.failure.errors:
                logger.error(f"\tError with message '{error.message}'")
                if error.location:
                    for field_path_element in error.location.field_path_elements:
                        logger.error(f"\t\tOn field: {field_path_element.field_name}")
            sys.exit(1)
    
    def get_campaign_performance(self, customer_id, campaign_id=None, start_date=None, end_date=None):
        """
        Get performance metrics for campaigns.
        
        Args:
            customer_id (str): Google Ads customer ID
            campaign_id (str, optional): Specific campaign ID to analyze
            start_date (str, optional): Start date in format YYYY-MM-DD
            end_date (str, optional): End date in format YYYY-MM-DD
            
        Returns:
            list: List of performance data dictionaries
        """
        ga_service = self.client.get_service("GoogleAdsService")
        
        # Set default date range if not provided
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        # Construct the query
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value,
                segments.date
            FROM campaign
            WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
        """
        
        # Add campaign ID filter if specified
        if campaign_id:
            query += f" AND campaign.id = {campaign_id}"
        
        try:
            stream = ga_service.search_stream(customer_id=customer_id, query=query)
            
            performance_data = []
            
            # Process the results
            for batch in stream:
                for row in batch.results:
                    campaign = row.campaign
                    metrics = row.metrics
                    segments = row.segments
                    
                    data = {
                        "campaign_id": campaign.id,
                        "campaign_name": campaign.name,
                        "date": segments.date,
                        "impressions": metrics.impressions,
                        "clicks": metrics.clicks,
                        "cost": metrics.cost_micros / 1000000,
                        "conversions": metrics.conversions,
                        "conversion_value": metrics.conversions_value,
                        "ctr": metrics.ctr if metrics.impressions > 0 else 0,
                        "cpc": metrics.average_cpc / 1000000 if metrics.clicks > 0 else 0,
                        "roas": metrics.conversions_value / (metrics.cost_micros / 1000000) if metrics.cost_micros > 0 else 0
                    }
                    
                    performance_data.append(data)
            
            return performance_data
        
        except GoogleAdsException as ex:
            logger.error(f"Request with ID '{ex.request_id}' failed with status '{ex.error.code().name}'")
            for error in ex.failure.errors:
                logger.error(f"\tError with message '{error.message}'")
                if error.location:
                    for field_path_element in error.location.field_path_elements:
                        logger.error(f"\t\tOn field: {field_path_element.field_name}")
            sys.exit(1)


class DataProcessor:
    """Processes and analyzes Google Ads data."""
    
    def __init__(self, output_dir=OUTPUT_DIR, cache_dir=CACHE_DIR):
        """
        Initialize the data processor.
        
        Args:
            output_dir (str): Directory for saving output reports
            cache_dir (str): Directory for caching data
        """
        self.output_dir = output_dir
        self.cache_dir = cache_dir
        
        # Create directories if they don't exist
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(cache_dir, exist_ok=True)
    
    def process_campaign_performance(self, performance_data):
        """
        Process campaign performance data.
        
        Args:
            performance_data (list): Raw performance data from Google Ads API
            
        Returns:
            pandas.DataFrame: Processed performance dataframe
        """
        if not performance_data:
            logger.warning("No performance data to process")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(performance_data)
        
        # Convert date string to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Calculate additional metrics
        df['cpa'] = df['cost'] / df['conversions'].replace(0, np.nan)
        df['cpa'] = df['cpa'].fillna(0)
        
        logger.info(f"Processed {len(df)} rows of campaign performance data")
        return df
    
    def analyze_campaign_trends(self, df):
        """
        Analyze trends in campaign performance over time.
        
        Args:
            df (pandas.DataFrame): Processed performance dataframe
            
        Returns:
            dict: Trend analysis results
        """
        if df.empty:
            logger.warning("No data for trend analysis")
            return {}
        
        # Group by date and aggregate metrics
        daily_metrics = df.groupby('date').agg({
            'impressions': 'sum',
            'clicks': 'sum',
            'cost': 'sum',
            'conversions': 'sum',
            'conversion_value': 'sum'
        }).reset_index()
        
        # Calculate daily metrics
        daily_metrics['ctr'] = daily_metrics['clicks'] / daily_metrics['impressions'] * 100
        daily_metrics['cpc'] = daily_metrics['cost'] / daily_metrics['clicks']
        daily_metrics['roas'] = daily_metrics['conversion_value'] / daily_metrics['cost']
        
        # Replace NaN values
        daily_metrics = daily_metrics.fillna(0)
        
        # Calculate trending metrics
        trends = {
            'impressions_trend': self._calculate_trend(daily_metrics['impressions']),
            'clicks_trend': self._calculate_trend(daily_metrics['clicks']),
            'cost_trend': self._calculate_trend(daily_metrics['cost']),
            'conversions_trend': self._calculate_trend(daily_metrics['conversions']),
            'ctr_trend': self._calculate_trend(daily_metrics['ctr']),
            'cpc_trend': self._calculate_trend(daily_metrics['cpc']),
            'roas_trend': self._calculate_trend(daily_metrics['roas'])
        }
        
        return {
            'daily_metrics': daily_metrics,
            'trends': trends
        }
    
    def _calculate_trend(self, series):
        """
        Calculate the trend of a metric over time.
        
        Args:
            series (pandas.Series): Time series data
            
        Returns:
            float: Trend percentage change
        """
        if len(series) < 2 or series.sum() == 0:
            return 0
        
        # For simplicity, compare average of first half with average of second half
        half_point = len(series) // 2
        if half_point == 0:
            return 0
        
        first_half = series[:half_point].mean()
        second_half = series[half_point:].mean()
        
        if first_half == 0:
            return 0
        
        return ((second_half - first_half) / first_half) * 100
    
    def generate_performance_report(self, df, output_file=None):
        """
        Generate a performance report from processed data.
        
        Args:
            df (pandas.DataFrame): Processed performance dataframe
            output_file (str, optional): Output file path
            
        Returns:
            str: Path to the generated report
        """
        if df.empty:
            logger.warning("No data for performance report")
            return None
        
        # Set default output file if not provided
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(self.output_dir, f"performance_report_{timestamp}.csv")
        
        # Group by campaign and aggregate metrics
        campaign_summary = df.groupby(['campaign_id', 'campaign_name']).agg({
            'impressions': 'sum',
            'clicks': 'sum',
            'cost': 'sum',
            'conversions': 'sum',
            'conversion_value': 'sum'
        }).reset_index()
        
        # Calculate summary metrics
        campaign_summary['ctr'] = campaign_summary['clicks'] / campaign_summary['impressions'] * 100
        campaign_summary['cpc'] = campaign_summary['cost'] / campaign_summary['clicks']
        campaign_summary['cpa'] = campaign_summary['cost'] / campaign_summary['conversions']
        campaign_summary['roas'] = campaign_summary['conversion_value'] / campaign_summary['cost']
        
        # Replace NaN values
        campaign_summary = campaign_summary.fillna(0)
        
        # Save to CSV
        campaign_summary.to_csv(output_file, index=False)
        logger.info(f"Performance report saved to {output_file}")
        
        return output_file
    
    def visualize_campaign_performance(self, df, output_dir=None):
        """
        Create visualizations for campaign performance.
        
        Args:
            df (pandas.DataFrame): Processed performance dataframe
            output_dir (str, optional): Directory to save visualizations
            
        Returns:
            list: Paths to the generated visualization files
        """
        if df.empty:
            logger.warning("No data for visualizations")
            return []
        
        # Set default output directory if not provided
        if not output_dir:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = os.path.join(self.output_dir, f"visualizations_{timestamp}")
            os.makedirs(output_dir, exist_ok=True)
        
        visualization_files = []
        
        # Set up styles
        sns.set(style="whitegrid")
        plt.rcParams.update({'font.size': 12})
        
        # 1. Daily Trends
        try:
            daily_df = df.groupby('date').agg({
                'clicks': 'sum',
                'impressions': 'sum',
                'cost': 'sum',
                'conversions': 'sum'
            }).reset_index()
            
            # Plot clicks and impressions
            fig, ax1 = plt.subplots(figsize=(12, 6))
            
            color = 'tab:blue'
            ax1.set_xlabel('Date')
            ax1.set_ylabel('Clicks', color=color)
            ax1.plot(daily_df['date'], daily_df['clicks'], color=color, marker='o', linestyle='-')
            ax1.tick_params(axis='y', labelcolor=color)
            
            ax2 = ax1.twinx()
            color = 'tab:red'
            ax2.set_ylabel('Impressions', color=color)
            ax2.plot(daily_df['date'], daily_df['impressions'], color=color, marker='x', linestyle='-')
            ax2.tick_params(axis='y', labelcolor=color)
            
            fig.tight_layout()
            plt.title('Daily Clicks and Impressions')
            
            trends_file = os.path.join(output_dir, 'daily_trends.png')
            plt.savefig(trends_file)
            plt.close()
            visualization_files.append(trends_file)
            
            # Plot cost and conversions
            fig, ax1 = plt.subplots(figsize=(12, 6))
            
            color = 'tab:green'
            ax1.set_xlabel('Date')
            ax1.set_ylabel('Cost ($)', color=color)
            ax1.plot(daily_df['date'], daily_df['cost'], color=color, marker='o', linestyle='-')
            ax1.tick_params(axis='y', labelcolor=color)
            
            ax2 = ax1.twinx()
            color = 'tab:purple'
            ax2.set_ylabel('Conversions', color=color)
            ax2.plot(daily_df['date'], daily_df['conversions'], color=color, marker='x', linestyle='-')
            ax2.tick_params(axis='y', labelcolor=color)
            
            fig.tight_layout()
            plt.title('Daily Cost and Conversions')
            
            conv_file = os.path.join(output_dir, 'cost_conversions.png')
            plt.savefig(conv_file)
            plt.close()
            visualization_files.append(conv_file)
            
        except Exception as e:
            logger.error(f"Error creating daily trends visualization: {e}")
        
        # 2. Campaign Comparison
        try:
            # Group by campaign
            campaign_df = df.groupby('campaign_name').agg({
                'clicks': 'sum',
                'impressions': 'sum',
                'cost': 'sum',
                'conversions': 'sum'
            }).reset_index()
            
            # Calculate CTR
            campaign_df['ctr'] = campaign_df['clicks'] / campaign_df['impressions'] * 100
            
            # Sort by clicks
            campaign_df = campaign_df.sort_values('clicks', ascending=False).head(10)
            
            # Plot
            plt.figure(figsize=(12, 6))
            sns.barplot(x='clicks', y='campaign_name', data=campaign_df)
            plt.title('Top Campaigns by Clicks')
            plt.tight_layout()
            
            campaign_file = os.path.join(output_dir, 'campaign_comparison.png')
            plt.savefig(campaign_file)
            plt.close()
            visualization_files.append(campaign_file)
            
            # Plot CTR
            plt.figure(figsize=(12, 6))
            sns.barplot(x='ctr', y='campaign_name', data=campaign_df)
            plt.title('Campaign CTR (%)')
            plt.tight_layout()
            
            ctr_file = os.path.join(output_dir, 'campaign_ctr.png')
            plt.savefig(ctr_file)
            plt.close()
            visualization_files.append(ctr_file)
            
        except Exception as e:
            logger.error(f"Error creating campaign comparison visualization: {e}")
        
        logger.info(f"Created {len(visualization_files)} visualization files in {output_dir}")
        return visualization_files


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


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Google Ads Analytics')
    parser.add_argument('--account-id', type=str, help='Google Ads account ID')
    parser.add_argument('--campaign-id', type=str, help='Specific campaign ID to analyze')
    parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--output-dir', type=str, default=OUTPUT_DIR, help='Output directory for reports')
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # Initialize Google Ads connector
    connector = GoogleAdsConnector(CREDENTIALS_FILE)
    
    # Get account ID if not provided
    if not args.account_id:
        customer_ids = connector.get_customer_ids()
        if not customer_ids:
            logger.error("No accessible Google Ads accounts found")
            sys.exit(1)
        
        args.account_id = customer_ids[0]
        logger.info(f"Using account ID: {args.account_id}")
    
    # Get campaign performance data
    performance_data = connector.get_campaign_performance(
        customer_id=args.account_id,
        campaign_id=args.campaign_id,
        start_date=args.start_date,
        end_date=args.end_date
    )
    
    # Initialize data processor
    processor = DataProcessor(output_dir=args.output_dir)
    
    # Process performance data
    df = processor.process_campaign_performance(performance_data)
    
    if not df.empty:
        # Analyze trends
        trend_analysis = processor.analyze_campaign_trends(df)
        
        # Generate performance report
        report_file = processor.generate_performance_report(df)
        
        # Create visualizations
        visualization_files = processor.visualize_campaign_performance(df)
        
        logger.info("Analysis completed successfully")
        
        # Output summary
        print("\nGoogle Ads Analytics Summary:")
        print(f"Account ID: {args.account_id}")
        if args.campaign_id:
            print(f"Campaign ID: {args.campaign_id}")
        print(f"Date Range: {args.start_date or 'Last 30 days'} to {args.end_date or 'Today'}")
        print(f"Performance Report: {report_file}")
        print(f"Visualizations: {len(visualization_files)} files generated")
        
        # Print trend analysis
        if trend_analysis and 'trends' in trend_analysis:
            print("\nTrend Analysis (% change):")
            for metric, value in trend_analysis['trends'].items():
                print(f"  {metric}: {value:.2f}%")
    else:
        logger.warning("No data to analyze")
        print("No data found for the specified parameters")


if __name__ == "__main__":
    main() 