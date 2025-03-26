# Product Image Management System

A comprehensive solution for processing, managing, and optimizing product images for e-commerce platforms, with special focus on jewelry product variations and visual consistency.

## Features

### Image Processing

- **Batch Processing**: Efficiently process thousands of images with configurable settings
- **Resizing and Optimization**: Automatically resize and optimize images for web and mobile
- **Metal Variation Generator**: Algorithmically create white gold, rose gold, and other metal variations from a single source image
- **Watermarking System**: Add customizable watermarks with adjustable positioning and opacity

### Quality Management

- **Consistency Verification**: Ensure visual consistency across product variations
- **Metadata Validation**: Verify and maintain accurate EXIF and other metadata
- **Error Detection**: Identify problematic images (low resolution, poor quality, etc.)
- **Auto-enhancement**: Intelligent contrast, brightness, and color adjustments

### Organization & Workflow

- **Naming Convention System**: Implement intelligent naming schemes based on product attributes
- **Directory Structure Manager**: Organize images into structured directories for easy access
- **Bulk Upload Utilities**: Upload large image sets with progress tracking and error recovery
- **Cross-platform Sync**: Synchronize images across Shopify, CDN, and local storage

### Transformation Pipeline

- **Style Consistency**: Apply consistent styling across product categories
- **Background Removal**: Automated removal of backgrounds with edge refinement
- **Shadow Generation**: Add consistent drop shadows for product depth
- **Reflection Effects**: Apply subtle reflection effects for jewelry products

## Architecture

The system consists of five main components:

1. **Image Processor**: Core engine for image manipulations and transformations
2. **Workflow Manager**: Handles batch processing, queueing, and job management
3. **Storage Connector**: Interface for various storage systems (local, S3, Shopify)
4. **Quality Validator**: Ensures images meet quality and consistency standards
5. **Web Interface**: Optional UI for manual operations and status monitoring

## Setup

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Configure storage connections in `config.json`:
```json
{
  "shopify": {
    "api_key": "your_api_key",
    "password": "your_password",
    "store_url": "your-store.myshopify.com"
  },
  "aws": {
    "access_key": "your_access_key",
    "secret_key": "your_secret_key",
    "bucket": "your-image-bucket"
  }
}
```

3. Set up processing profiles in `profiles.json`

4. Run the system:
```bash
python image_manager.py --profile=default
```

## Requirements

```
Pillow>=9.0.0
numpy>=1.20.0
pyyaml>=6.0
boto3>=1.20.0
shopify-api>=9.0.0
opencv-python>=4.5.0
requests>=2.25.0
tqdm>=4.60.0
colorama>=0.4.4
```

## Usage Examples

### Process a Single Product's Images

```bash
python image_manager.py --product=123456789 --operations=resize,optimize,watermark
```

### Generate Metal Variations

```bash
python image_manager.py --source=ring_main.jpg --metals=white_gold,rose_gold,platinum
```

### Bulk Processing

```bash
python image_manager.py --directory=new_products --recursive --profile=jewelry
```

### Synchronization

```bash
python sync_images.py --source=local --target=shopify --collection=new_arrivals
```

## Image Transformation Pipeline

The transformation pipeline applies the following operations in sequence:

1. **Pre-processing**: Format conversion, initial resizing
2. **Background Handling**: Background removal or standardization
3. **Color Correction**: White balance, color enhancement
4. **Metal Variation**: Generation of metal variations (if applicable)
5. **Effect Application**: Shadows, reflections, highlights
6. **Quality Optimization**: Sharpening, noise reduction
7. **Output Preparation**: Final resizing, format conversion, compression
8. **Metadata Embedding**: Add or update product metadata in image

## Performance

- Processes approximately 500 images per minute on standard hardware
- Support for GPU acceleration with OpenCV CUDA integration
- Parallel processing utilizing multiple CPU cores
- Intelligent caching system to avoid redundant operations

## Notes

- Optimized for jewelry product images but applicable to other product categories
- Special handling for reflective materials (metals, gemstones) with custom algorithms
- Error recovery system automatically retries failed operations
- Detailed logging for tracking processing history and troubleshooting 