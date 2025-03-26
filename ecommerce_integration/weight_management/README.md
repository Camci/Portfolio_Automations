# Jewelry Weight Management System

This project provides a comprehensive solution for managing product weights across a large jewelry inventory. It automatically calculates weights for different metal types and karats based on reference products, significantly reducing manual data entry.

## Features

- **Base Weight Calculation**: Uses 10K gold products as reference points to calculate weights for other metal types
- **Multi-karat Support**: Automatically generates weights for 14K, 18K, 21K, and 22K variants
- **Metal Color Variations**: Handles Yellow Gold, Rose Gold, and White Gold variants
- **Chain Length Variations**: Calculates weights for different chain lengths based on reference measurements
- **Bulk Update System**: Updates thousands of product variants in Shopify efficiently with parallel processing

## Key Files

- `weight_update_system.py` - Main system for calculating and updating weights
- `10K_to_all_weights.py` - Specialized tool for converting 10K weights to all variants
- `14K_to_All_Weight.py` - Alternative calculation starting from 14K reference weights

## Mathematical Model

The system uses the following calculations:

1. **Karat Conversion**:
   - 14K from 10K: Weight × (1 / 0.89)
   - 18K from 14K: Weight × 1.18
   - 21K from 14K: Weight × 1.28
   - 22K from 14K: Weight × 1.30

2. **Length Adjustments**:
   For different chain dimensions (3mm, 4mm, 5mm), specific weight increments are added based on length differences.

## Requirements

```
requests==2.28.1
pandas==1.5.3
```

## Usage

Basic usage:

```python
python weight_update_system.py
```

The system will:
1. Retrieve all product variants from Shopify
2. Identify 10K reference products with known weights
3. Calculate weights for all other variants using the mathematical model
4. Generate weights for additional lengths
5. Update all variants in the Shopify store

## Performance

- The system uses concurrent processing to handle thousands of updates efficiently
- Built-in rate limiting prevents API throttling
- Error handling ensures the process continues even if individual updates fail

This tool has successfully managed weights for catalogs with over 10,000 jewelry variants. 