# Dynamic Pricing System

This project provides an automated pricing system for jewelry products based on real-time gold market prices. It retrieves current and historical gold prices from a metals API, tracks price trends in a Grist database, and updates product prices accordingly.

## Features

- **Live Market Data Integration**: Connects to Metals API for up-to-date gold spot prices
- **Historical Price Tracking**: Maintains a database of gold prices over time
- **Threshold-Based Updates**: Only updates product prices when gold price changes exceed a configurable threshold
- **Proportional Price Adjustment**: Calculates price adjustments based on gold karat and weight
- **Market Trend Analysis**: Compares current prices to historical baselines

## Key Files

- `gold_price_updater.py` - Main script for retrieving gold prices and updating product prices
- `gold_price_daily.py` - Scheduled task for daily gold price updates

## Mathematical Model

The system uses the following formula to calculate price adjustments:

```
Price Factor = Current Gold Price / Base Gold Price
New Product Price = Base Product Price × Price Factor
```

For example, if gold increases from $1800 to $1890 (a 5% increase), product prices would increase by the same percentage.

## Requirements

```
requests==2.28.1
grist-api==0.5.0
pytz==2022.1
```

## Setup

1. Sign up for a Metals API key
2. Configure Grist API access
3. Set up your threshold preferences
4. Schedule the script to run at desired intervals

## Usage

Basic usage:

```bash
python gold_price_updater.py
```

This will:
1. Retrieve the latest gold prices
2. Store them in your Grist database
3. Compare to historical prices
4. Update product prices if the change exceeds your threshold

## Integration Points

The system is designed to integrate with:
- Shopify product pricing API
- Grist database for price history and reporting
- Email notification systems for price change alerts 