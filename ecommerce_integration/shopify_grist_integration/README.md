# Shopify-Grist Integration

A bidirectional synchronization system that keeps Shopify e-commerce data in sync with Grist spreadsheets, enabling efficient inventory management and order tracking.

## Features

### Data Synchronization

- **Bidirectional Sync**: Changes in either Shopify or Grist are reflected in the other platform
- **Conflict Resolution**: Smart handling of conflicting changes with configurable priority rules
- **Selective Sync**: Configure which fields and records to synchronize
- **Real-time Updates**: Near real-time data transfer with configurable polling intervals

### Shopify Integration

- **Product Sync**: Inventory levels, prices, SKUs, and metadata
- **Order Sync**: Order status, fulfillment, and customer information
- **Collections**: Sync product categorization and organization
- **Metafields**: Support for custom metafields for extended data storage

### Grist Integration

- **Custom Column Mapping**: Flexible mapping between Shopify fields and Grist columns
- **Formula Support**: Preserves and updates Grist formulas during synchronization
- **Bulk Operations**: Efficient handling of large datasets with batched API calls
- **Change Detection**: Smart detection of modified records to minimize API usage

## Architecture

The integration uses a hub-and-spoke architecture with:

1. **Sync Engine**: Core logic for bidirectional data synchronization
2. **Shopify Connector**: Handles Shopify API authentication and data operations
3. **Grist Connector**: Manages Grist API interactions and data transformations
4. **Configuration Manager**: Stores and applies sync rules and field mappings

## Setup

1. Configure Shopify API credentials:
   - API Key
   - API Secret
   - Access Token
   - Store URL

2. Configure Grist API credentials:
   - API Key
   - Document ID
   - Workspace ID

3. Set up field mappings in the configuration file

4. Run the synchronization:
```bash
python shopify_grist_sync.py
```

## Requirements

```
requests>=2.25.0
pandas>=1.3.0
PyYAML>=6.0
schedule>=1.1.0
```

## Usage Examples

### One-time Sync

```bash
python shopify_grist_sync.py --mode=once
```

### Continuous Sync

```bash
python shopify_grist_sync.py --mode=continuous --interval=15
```

### Selective Field Sync

```bash
python shopify_grist_sync.py --fields=inventory,price
```

## Limitations

- API rate limits may affect synchronization speed for large catalogs
- Complex nested data structures require custom mapping rules
- Certain Shopify features (e.g., draft orders) have limited support in the current version

## Future Enhancements

- WebSocket support for real-time updates
- Enhanced conflict resolution strategies
- Support for additional Shopify resources
- Web interface for configuration management 