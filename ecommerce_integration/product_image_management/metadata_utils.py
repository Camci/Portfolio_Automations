#!/usr/bin/env python3
"""
Metadata Utilities for Product Image Management System

Tools for extracting, manipulating, and validating image metadata
specifically for e-commerce product images.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
import re

# These imports would be used in a real implementation
# from PIL import Image, ExifTags
# import piexif

logger = logging.getLogger('image-manager.metadata')

# Constants for metadata fields
PRODUCT_ID_FIELD = "ProductID"
SKU_FIELD = "SKU"
PRODUCT_TYPE_FIELD = "ProductType"
METAL_TYPE_FIELD = "MetalType"
VARIATION_FIELD = "Variation"
ANGLE_FIELD = "Angle"
TIMESTAMP_FIELD = "Timestamp"
AUTHOR_FIELD = "Author"
COPYRIGHT_FIELD = "Copyright"
SOFTWARE_FIELD = "Software"
VERSION_FIELD = "Version"

# Standard photography angles for jewelry
STANDARD_ANGLES = [
    "front", "side", "back", "top", "angle", 
    "detail", "lifestyle", "packaging", "model"
]

# Regular expressions for extracting information from filenames
FILENAME_PATTERNS = {
    "product_id": r"(?:^|[_-])([A-Z0-9]{6,10})(?:[_-]|$)",
    "sku": r"(?:^|[_-])([A-Z0-9]{2,6}-[A-Z0-9]{3,8})(?:[_-]|$)",
    "metal": r"(?:^|[_-])((?:yellow|white|rose)_?gold|silver|platinum)(?:[_-]|$)",
    "angle": r"(?:^|[_-])(front|side|back|top|angle|detail|lifestyle|packaging|model)(?:[_-]|$)"
}


class MetadataExtractor:
    """Extracts and manages image metadata."""
    
    def __init__(self, config=None):
        """Initialize the metadata extractor with optional configuration."""
        self.config = config or {}
    
    def extract_from_image(self, image_path):
        """
        Extract metadata from image EXIF and other embedded data.
        
        Args:
            image_path (str): Path to the image file
                
        Returns:
            dict: Extracted metadata
        """
        image_path = Path(image_path)
        if not image_path.exists():
            logger.error(f"Image not found: {image_path}")
            return {}
        
        logger.info(f"Extracting metadata from image: {image_path}")
        
        # In a real implementation, this would use PIL or piexif to extract EXIF data
        # metadata = {}
        # with Image.open(image_path) as img:
        #     if hasattr(img, '_getexif') and img._getexif():
        #         exif = {
        #             ExifTags.TAGS[k]: v
        #             for k, v in img._getexif().items()
        #             if k in ExifTags.TAGS
        #         }
        #         metadata.update(exif)
        
        # Simulate metadata extraction
        metadata = {
            "FileName": image_path.name,
            "FileSize": image_path.stat().st_size,
            "LastModified": datetime.fromtimestamp(image_path.stat().st_mtime).isoformat(),
            "FileExtension": image_path.suffix.lower()
        }
        
        # Extract information from filename
        filename_metadata = self.extract_from_filename(image_path.name)
        metadata.update(filename_metadata)
        
        return metadata
    
    def extract_from_filename(self, filename):
        """
        Extract metadata from the filename using patterns.
        
        Args:
            filename (str): Image filename
                
        Returns:
            dict: Extracted metadata
        """
        metadata = {}
        
        # Apply each pattern to extract information
        for key, pattern in FILENAME_PATTERNS.items():
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                metadata[key] = match.group(1).lower()
        
        return metadata
    
    def extract_from_directory(self, directory_path):
        """
        Extract metadata from directory structure.
        
        Args:
            directory_path (str): Path containing the image
                
        Returns:
            dict: Extracted metadata
        """
        path = Path(directory_path)
        metadata = {}
        
        # Parse directory structure
        parts = path.parts
        
        # Look for product collections in path
        collections = ["rings", "earrings", "necklaces", "bracelets", "pendants"]
        for collection in collections:
            if collection in parts:
                metadata["collection"] = collection
                break
        
        # Look for metal types in path
        metals = ["gold", "silver", "platinum"]
        for metal in metals:
            if metal in parts:
                metadata["metal"] = metal
                break
        
        return metadata
    
    def generate_standard_metadata(self, product_id, sku=None, **kwargs):
        """
        Generate standard metadata for a product image.
        
        Args:
            product_id (str): Product identifier
            sku (str, optional): SKU code
            **kwargs: Additional metadata fields
                
        Returns:
            dict: Standard metadata
        """
        metadata = {
            PRODUCT_ID_FIELD: product_id,
            TIMESTAMP_FIELD: datetime.now().isoformat(),
            SOFTWARE_FIELD: "ProductImageManager",
            VERSION_FIELD: "1.0"
        }
        
        if sku:
            metadata[SKU_FIELD] = sku
        
        # Add additional metadata
        for key, value in kwargs.items():
            metadata[key] = value
        
        return metadata


class MetadataWriter:
    """Writes metadata to image files and sidecar files."""
    
    def __init__(self, config=None):
        """Initialize the metadata writer with optional configuration."""
        self.config = config or {}
    
    def write_to_image(self, image_path, metadata):
        """
        Write metadata directly to image EXIF.
        
        Args:
            image_path (str): Path to the image file
            metadata (dict): Metadata to write
                
        Returns:
            bool: Success status
        """
        image_path = Path(image_path)
        if not image_path.exists():
            logger.error(f"Image not found: {image_path}")
            return False
        
        logger.info(f"Writing metadata to image: {image_path}")
        
        # In a real implementation, this would use piexif to write EXIF data
        # exif_dict = piexif.load(str(image_path))
        # 
        # for key, value in metadata.items():
        #     if key in ExifTags.TAGS.values():
        #         # Find the numeric key for this tag
        #         for num_key, tag_name in ExifTags.TAGS.items():
        #             if tag_name == key:
        #                 exif_dict["0th"][num_key] = str(value)
        #                 break
        # 
        # exif_bytes = piexif.dump(exif_dict)
        # piexif.insert(exif_bytes, str(image_path))
        
        logger.info(f"Metadata written to image: {image_path}")
        return True
    
    def write_to_sidecar(self, image_path, metadata, format="json"):
        """
        Write metadata to a sidecar file.
        
        Args:
            image_path (str): Path to the image file
            metadata (dict): Metadata to write
            format (str): Sidecar format (json, xmp)
                
        Returns:
            str: Path to the sidecar file
        """
        image_path = Path(image_path)
        
        if format.lower() == "json":
            sidecar_path = image_path.with_suffix(".json")
            
            with open(sidecar_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Metadata written to JSON sidecar: {sidecar_path}")
            return str(sidecar_path)
            
        elif format.lower() == "xmp":
            sidecar_path = image_path.with_suffix(".xmp")
            
            # In a real implementation, this would create an XMP file
            # with open(sidecar_path, 'w') as f:
            #     f.write("<x:xmpmeta xmlns:x='adobe:ns:meta/'>\n")
            #     # ... XMP format content
            #     f.write("</x:xmpmeta>")
            
            logger.info(f"Metadata written to XMP sidecar: {sidecar_path}")
            return str(sidecar_path)
            
        else:
            logger.error(f"Unsupported sidecar format: {format}")
            return None


class NamingConvention:
    """Manages consistent file naming."""
    
    def __init__(self, config=None):
        """Initialize naming convention with optional configuration."""
        self.config = config or {}
        self.pattern = self.config.get("pattern", "{product_id}_{metal}_{angle}")
        self.separator = self.config.get("separator", "_")
        self.lowercase = self.config.get("lowercase", True)
    
    def generate_filename(self, metadata, extension=".jpg"):
        """
        Generate a filename from metadata.
        
        Args:
            metadata (dict): Image metadata
            extension (str): File extension
                
        Returns:
            str: Generated filename
        """
        # Create a dictionary with lowercase keys for pattern formatting
        format_dict = {}
        for key, value in metadata.items():
            format_dict[key.lower()] = value
        
        # Try to format the pattern with available metadata
        try:
            filename = self.pattern.format(**format_dict)
        except KeyError as e:
            logger.warning(f"Missing metadata for filename pattern: {e}")
            # Fall back to a simpler pattern
            if "product_id" in format_dict:
                filename = f"{format_dict['product_id']}"
                if "metal" in format_dict:
                    filename += f"{self.separator}{format_dict['metal']}"
                if "angle" in format_dict:
                    filename += f"{self.separator}{format_dict['angle']}"
            else:
                # If even product_id is missing, use a timestamp
                filename = f"img_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Apply lowercase if configured
        if self.lowercase:
            filename = filename.lower()
        
        # Ensure the extension starts with a dot
        if not extension.startswith("."):
            extension = f".{extension}"
        
        return f"{filename}{extension}"
    
    def parse_filename(self, filename):
        """
        Parse a filename to extract metadata.
        
        Args:
            filename (str): Filename to parse
                
        Returns:
            dict: Extracted metadata
        """
        extractor = MetadataExtractor()
        return extractor.extract_from_filename(filename)
    
    def rename_file(self, image_path, metadata=None):
        """
        Rename a file according to naming convention.
        
        Args:
            image_path (str): Path to the image file
            metadata (dict, optional): Metadata to use for naming
                
        Returns:
            str: New file path
        """
        image_path = Path(image_path)
        if not image_path.exists():
            logger.error(f"Image not found: {image_path}")
            return None
        
        # If metadata not provided, extract it
        if metadata is None:
            extractor = MetadataExtractor()
            metadata = extractor.extract_from_image(image_path)
        
        # Generate new filename
        new_filename = self.generate_filename(metadata, image_path.suffix)
        new_path = image_path.parent / new_filename
        
        # Rename the file
        if image_path != new_path:
            logger.info(f"Renaming {image_path} to {new_path}")
            image_path.rename(new_path)
        
        return str(new_path)


class MetadataValidator:
    """Validates image metadata against rules."""
    
    def __init__(self, config=None):
        """Initialize the validator with optional configuration."""
        self.config = config or {}
        self.required_fields = [PRODUCT_ID_FIELD]
    
    def validate(self, metadata):
        """
        Validate metadata against rules.
        
        Args:
            metadata (dict): Metadata to validate
                
        Returns:
            dict: Validation results
        """
        errors = []
        warnings = []
        
        # Check required fields
        for field in self.required_fields:
            if field not in metadata:
                errors.append(f"Missing required field: {field}")
        
        # Check product ID format
        if PRODUCT_ID_FIELD in metadata:
            product_id = metadata[PRODUCT_ID_FIELD]
            if not re.match(r'^[A-Z0-9]{6,10}$', product_id):
                warnings.append(f"Product ID format may be invalid: {product_id}")
        
        # Check metal type if present
        if METAL_TYPE_FIELD in metadata:
            metal = metadata[METAL_TYPE_FIELD].lower()
            valid_metals = ["yellow_gold", "white_gold", "rose_gold", "silver", "platinum"]
            if metal not in valid_metals:
                warnings.append(f"Unrecognized metal type: {metal}")
        
        # Check angle if present
        if ANGLE_FIELD in metadata:
            angle = metadata[ANGLE_FIELD].lower()
            if angle not in STANDARD_ANGLES:
                warnings.append(f"Non-standard angle: {angle}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }


def extract_bulk_metadata(directory, recursive=False):
    """
    Extract metadata from all images in a directory.
    
    Args:
        directory (str): Directory containing images
        recursive (bool): Whether to process subdirectories
            
    Returns:
        dict: Mapping from file paths to metadata
    """
    directory_path = Path(directory)
    if not directory_path.exists():
        logger.error(f"Directory not found: {directory_path}")
        return {}
    
    # Find all image files
    image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.tiff']
    
    if recursive:
        image_files = [
            f for f in directory_path.glob('**/*')
            if f.is_file() and f.suffix.lower() in image_extensions
        ]
    else:
        image_files = [
            f for f in directory_path.glob('*')
            if f.is_file() and f.suffix.lower() in image_extensions
        ]
    
    if not image_files:
        logger.warning(f"No image files found in {directory_path}")
        return {}
    
    # Extract metadata from each image
    results = {}
    extractor = MetadataExtractor()
    
    for image_path in image_files:
        metadata = extractor.extract_from_image(image_path)
        results[str(image_path)] = metadata
    
    return results


def apply_bulk_metadata(directory, metadata_dict, recursive=False):
    """
    Apply common metadata to all images in a directory.
    
    Args:
        directory (str): Directory containing images
        metadata_dict (dict): Metadata to apply
        recursive (bool): Whether to process subdirectories
            
    Returns:
        dict: Results of operation
    """
    directory_path = Path(directory)
    if not directory_path.exists():
        logger.error(f"Directory not found: {directory_path}")
        return {"status": "error", "message": "Directory not found"}
    
    # Find all image files
    image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.tiff']
    
    if recursive:
        image_files = [
            f for f in directory_path.glob('**/*')
            if f.is_file() and f.suffix.lower() in image_extensions
        ]
    else:
        image_files = [
            f for f in directory_path.glob('*')
            if f.is_file() and f.suffix.lower() in image_extensions
        ]
    
    if not image_files:
        logger.warning(f"No image files found in {directory_path}")
        return {"status": "warning", "message": "No image files found"}
    
    # Apply metadata to each image
    success_count = 0
    failed_count = 0
    writer = MetadataWriter()
    
    for image_path in image_files:
        try:
            # Write to sidecar JSON for simplicity
            writer.write_to_sidecar(image_path, metadata_dict)
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to apply metadata to {image_path}: {e}")
            failed_count += 1
    
    return {
        "status": "success",
        "total": len(image_files),
        "success": success_count,
        "failed": failed_count
    }


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    extractor = MetadataExtractor()
    metadata = extractor.generate_standard_metadata(
        product_id="ABC123",
        sku="ABC-123",
        metal_type="yellow_gold",
        angle="front"
    )
    
    print(json.dumps(metadata, indent=2))
    
    naming = NamingConvention({
        "pattern": "{product_id}_{metal_type}_{angle}",
        "lowercase": True
    })
    
    filename = naming.generate_filename(metadata)
    print(f"Generated filename: {filename}")
    
    validator = MetadataValidator()
    validation = validator.validate(metadata)
    print(f"Validation result: {validation}") 