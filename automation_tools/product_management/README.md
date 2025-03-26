# Shopify Product Management Tools

A collection of automation tools for managing Shopify product data, options, variants, and metadata at scale.

## Tools Included

### SKU Updater (`sku_updater.py`)

A tool that automates the generation and updating of SKUs for Shopify products based on standardized patterns.

#### Features

- Fetches products from Shopify using GraphQL API with pagination
- Applies configurable SKU formatting rules based on product titles and variant options
- Handles special cases (e.g., black edition products)
- Implements local caching to reduce API calls during development
- Includes dry-run mode to preview changes before applying them

#### Usage

```bash
python sku_updater.py
```

### Variant Manager (`variant_manager.py`)

A tool for bulk management of product variants, including reorganizing option structures and controlling allowed values.

#### Features

- Removes unneeded product options (e.g., converting 3 options to 2)
- Restricts allowed values for specific options (e.g., only allowing certain metal types)
- Handles duplicate variant resolution by automatically removing redundant variants
- Updates product option structure while preserving existing variants where possible

#### Usage

```bash
python variant_manager.py
```

### Metadata Transfer (`metadata_transfer.py`)

A tool for transferring metafield data between Shopify stores or enriching CSV exports with metafield values.

#### Features

- Parallel processing with thread pooling for efficient API utilization
- Progress tracking with tqdm for visibility into long-running operations
- Handles large product catalogs efficiently through batching and deduplication
- Preserves CSV structure while adding new columns for metafield data

#### Usage

```bash
python metadata_transfer.py
```

## Requirements

```
requests==2.28.1
pandas==1.5.3
tqdm==4.64.1
```

## Configuration

Each script requires configuration of Shopify API credentials:

- `STORE_URL`: Your Shopify store URL (without https://)
- `ADMIN_API_TOKEN` or `ACCESS_TOKEN`: Your Shopify Admin API access token
- `API_VERSION`: The Shopify API version to use

## Notes

- These tools use the Shopify GraphQL Admin API for most operations, which provides better performance and more capabilities than the REST API
- Concurrent operations are implemented with appropriate rate limiting to avoid API throttling
- Error handling includes retries and logging for robust operation 