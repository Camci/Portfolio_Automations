# Jewelry Weight Management System

A specialized tool for calculating, storing, and managing jewelry weights for accurate pricing and inventory management in Shopify-based jewelry stores.

## Features

### Weight Calculation

- **Metal Weight Calculation**: Automatically calculate metal weights based on dimensions and density
- **Stone Weight Estimation**: Calculate gemstone weights based on shape, dimensions, and specific gravity
- **Chain Weight Calculation**: Specialized formula for chain jewelry accounting for link type and pattern
- **Custom Components**: Support for custom jewelry components with predefined weights

### Product Integration

- **Shopify Integration**: Store calculated weights in Shopify product metafields
- **Batch Processing**: Process entire product catalogs with high efficiency
- **Weight Verification**: Cross-check calculated weights against actual weights
- **Audit Trail**: Track weight changes and modifications with timestamps

### Business Logic

- **Price Calculation**: Automatically calculate prices based on weight and current metal market prices
- **Metal Cost Updates**: Update metal costs based on market fluctuations
- **Profit Margin Analysis**: Calculate margins based on materials cost and selling price
- **Competitive Analysis**: Compare pricing against market benchmarks

## Architecture

The system consists of three main components:

1. **Weight Calculator**: Core engine for jewelry weight calculations
2. **Shopify Connector**: Interface for accessing and updating Shopify product data
3. **Admin Interface**: User interface for manual calculations and batch operations

## Setup

1. Configure Shopify API credentials in `config.json`:
   - API Key
   - API Secret
   - Access Token
   - Store URL

2. Set up metal densities and pricing in `materials.json`

3. Run the weight management system:
```bash
python jewelry_weight_manager.py
```

## Requirements

```
requests>=2.25.0
pandas>=1.3.0
numpy>=1.20.0
PyYAML>=6.0
```

## Usage Examples

### Calculate Single Product Weight

```python
from weight_calculator import calculate_ring_weight

weight = calculate_ring_weight(
    metal_type="14k Gold",
    ring_size=7,
    band_width=2.0,  # mm
    band_thickness=1.5,  # mm
    shank_style="comfort fit"
)
```

### Batch Update Product Weights

```bash
python update_weights.py --collection="rings" --metal-type="14k Gold"
```

### Update Metal Prices

```bash
python update_metal_prices.py --source="kitco" --metals="gold,silver,platinum"
```

## Formulas and Methodology

The system uses industry-standard jewelry weight calculation formulas:

- Ring weights based on cylindrical volume with adjustments for shank style
- Stone weights based on geometric formulas for various cut shapes
- Chain weights based on link density and pattern multipliers

## Notes

- All measurements should be input in millimeters
- Weights are calculated and stored in grams
- Density values for common metals are pre-configured
- Custom density values can be added for specialty alloys 