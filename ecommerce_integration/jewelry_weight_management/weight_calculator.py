#!/usr/bin/env python3
"""
Jewelry Weight Calculator

This module provides functions for calculating the weight of various jewelry items
based on their dimensions, material, and other properties.
"""

import math
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('weight_calculator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("weight-calculator")

# Load metal density data from config file
def load_metal_densities():
    """Load metal density values from the materials.json file."""
    try:
        with open('materials.json', 'r') as f:
            materials = json.load(f)
            return materials.get('metal_densities', {})
    except Exception as e:
        logger.error(f"Failed to load metal densities: {e}")
        # Default values as fallback
        return {
            "10K Yellow Gold": 11.5,
            "14K Yellow Gold": 12.9,
            "18K Yellow Gold": 15.2,
            "10K White Gold": 11.5,
            "14K White Gold": 12.9,
            "18K White Gold": 15.2,
            "Sterling Silver": 10.36,
            "Platinum": 21.45
        }

# Load gemstone density data
def load_stone_densities():
    """Load stone density values from the materials.json file."""
    try:
        with open('materials.json', 'r') as f:
            materials = json.load(f)
            return materials.get('stone_densities', {})
    except Exception as e:
        logger.error(f"Failed to load stone densities: {e}")
        # Default values as fallback
        return {
            "Diamond": 3.52,
            "Sapphire": 4.0,
            "Ruby": 4.0,
            "Emerald": 2.76,
            "Amethyst": 2.65,
            "Aquamarine": 2.7,
            "Topaz": 3.5,
            "Cubic Zirconia": 5.8
        }

# Global variables for metal and stone densities
METAL_DENSITIES = load_metal_densities()
STONE_DENSITIES = load_stone_densities()

# US ring size to diameter mapping (mm)
RING_SIZE_TO_DIAMETER = {
    3: 14.1,
    3.5: 14.5,
    4: 14.9,
    4.5: 15.3,
    5: 15.7,
    5.5: 16.1,
    6: 16.5,
    6.5: 16.9,
    7: 17.3,
    7.5: 17.7,
    8: 18.1,
    8.5: 18.5,
    9: 18.9,
    9.5: 19.3,
    10: 19.7,
    10.5: 20.1,
    11: 20.5,
    11.5: 20.9,
    12: 21.3,
    12.5: 21.7,
    13: 22.1
}

def calculate_ring_weight(metal_type, ring_size, band_width, band_thickness, shank_style="standard"):
    """
    Calculate the weight of a ring based on its dimensions and metal type.
    
    Args:
        metal_type (str): The metal type (e.g., "14K Yellow Gold")
        ring_size (float): US ring size
        band_width (float): Width of the band in mm
        band_thickness (float): Thickness of the band in mm
        shank_style (str, optional): Style of the ring shank. Default is "standard"
            Options: "standard", "comfort fit", "euro shank", "cathedral"
    
    Returns:
        float: Weight of the ring in grams
    """
    # Get metal density
    if metal_type not in METAL_DENSITIES:
        logger.error(f"Unknown metal type: {metal_type}")
        raise ValueError(f"Unknown metal type: {metal_type}")
    
    density = METAL_DENSITIES[metal_type]
    
    # Get diameter from ring size
    if ring_size not in RING_SIZE_TO_DIAMETER:
        logger.warning(f"Ring size {ring_size} not in lookup table. Interpolating.")
        # Simple interpolation for sizes not in the table
        keys = sorted(RING_SIZE_TO_DIAMETER.keys())
        if ring_size < keys[0]:
            diameter = RING_SIZE_TO_DIAMETER[keys[0]]
        elif ring_size > keys[-1]:
            diameter = RING_SIZE_TO_DIAMETER[keys[-1]]
        else:
            for i in range(len(keys) - 1):
                if keys[i] < ring_size < keys[i + 1]:
                    lower_size = keys[i]
                    upper_size = keys[i + 1]
                    lower_diameter = RING_SIZE_TO_DIAMETER[lower_size]
                    upper_diameter = RING_SIZE_TO_DIAMETER[upper_size]
                    diameter = lower_diameter + (upper_diameter - lower_diameter) * (ring_size - lower_size) / (upper_size - lower_size)
                    break
    else:
        diameter = RING_SIZE_TO_DIAMETER[ring_size]
    
    # Calculate volume based on ring dimensions
    # For a standard ring, use the formula for a hollow cylinder
    radius = diameter / 2
    inner_radius = radius - band_thickness
    
    # Apply shank style adjustments
    style_factor = 1.0  # Default for standard shank
    if shank_style == "comfort fit":
        # Comfort fit has less metal on the inside, typically reducing weight by 10-15%
        style_factor = 0.9
    elif shank_style == "euro shank":
        # Euro shank has additional metal at the bottom, typically adding 15-20%
        style_factor = 1.18
    elif shank_style == "cathedral":
        # Cathedral settings have additional metal for the setting, adding 20-25%
        style_factor = 1.22
    
    # Calculate volume in cubic mm
    volume = math.pi * band_width * ((radius ** 2) - (inner_radius ** 2)) * style_factor
    
    # Convert volume to weight (density is in g/cm³, so convert mm³ to cm³)
    volume_cm3 = volume / 1000  # Convert mm³ to cm³
    weight = volume_cm3 * density
    
    logger.info(f"Calculated ring weight for {metal_type}, size {ring_size}: {weight:.2f}g")
    return weight

def calculate_stone_weight(stone_type, shape, dimensions):
    """
    Calculate the weight of a gemstone based on its type, shape, and dimensions.
    
    Args:
        stone_type (str): Type of gemstone (e.g., "Diamond", "Sapphire")
        shape (str): Shape of the stone (e.g., "round", "princess", "emerald", "oval")
        dimensions (dict): Dictionary of dimensions in mm:
            - For round: {"diameter": float}
            - For princess: {"length": float}
            - For emerald/oval: {"length": float, "width": float, "depth": float}
    
    Returns:
        dict: Dictionary containing weight in carats and additional info
    """
    # Get stone density
    if stone_type not in STONE_DENSITIES:
        logger.error(f"Unknown stone type: {stone_type}")
        raise ValueError(f"Unknown stone type: {stone_type}")
    
    density = STONE_DENSITIES[stone_type]
    volume_mm3 = 0
    
    # Calculate volume based on shape and dimensions
    if shape.lower() == "round":
        if "diameter" not in dimensions:
            raise ValueError("Round stones require 'diameter' dimension")
        
        diameter = dimensions["diameter"]
        depth = dimensions.get("depth", diameter * 0.6)  # Estimate depth if not provided
        
        # Use formula for round brilliant cut diamond
        volume_mm3 = 0.0027 * (diameter ** 2) * depth
    
    elif shape.lower() == "princess":
        if "length" not in dimensions:
            raise ValueError("Princess cut stones require 'length' dimension")
        
        length = dimensions["length"]
        depth = dimensions.get("depth", length * 0.7)  # Estimate depth if not provided
        
        # Use formula for princess cut diamond
        volume_mm3 = 0.0046 * (length ** 2) * depth
    
    elif shape.lower() in ["emerald", "oval"]:
        if "length" not in dimensions or "width" not in dimensions:
            raise ValueError(f"{shape.capitalize()} cut stones require 'length' and 'width' dimensions")
        
        length = dimensions["length"]
        width = dimensions["width"]
        depth = dimensions.get("depth", (length + width) * 0.3)  # Estimate depth if not provided
        
        # Formula depends on shape
        if shape.lower() == "emerald":
            volume_mm3 = 0.00219 * length * width * depth
        else:  # oval
            volume_mm3 = 0.00264 * length * width * depth
    
    else:
        logger.error(f"Unsupported stone shape: {shape}")
        raise ValueError(f"Unsupported stone shape: {shape}")
    
    # Calculate weight in carats (1 carat = 0.2 grams)
    # First calculate weight in grams, then convert to carats
    weight_grams = volume_mm3 * density / 1000  # Convert mm³ to cm³, then multiply by density (g/cm³)
    weight_carats = weight_grams / 0.2  # Convert grams to carats
    
    logger.info(f"Calculated {stone_type} {shape} weight: {weight_carats:.2f} carats")
    
    return {
        "weight_carats": weight_carats,
        "weight_grams": weight_grams,
        "volume_mm3": volume_mm3,
        "stone_type": stone_type,
        "shape": shape,
        "dimensions": dimensions
    }

def calculate_chain_weight(metal_type, length_mm, chain_type, link_diameter_mm=None):
    """
    Calculate the weight of a chain based on its metal, length, and chain type.
    
    Args:
        metal_type (str): The metal type (e.g., "14K Yellow Gold")
        length_mm (float): Chain length in mm
        chain_type (str): Type of chain (e.g., "cable", "curb", "figaro", "rope")
        link_diameter_mm (float, optional): Diameter of chain links in mm
    
    Returns:
        float: Weight of the chain in grams
    """
    # Get metal density
    if metal_type not in METAL_DENSITIES:
        logger.error(f"Unknown metal type: {metal_type}")
        raise ValueError(f"Unknown metal type: {metal_type}")
    
    density = METAL_DENSITIES[metal_type]
    
    # Chain type factors (weight per mm)
    chain_factors = {
        "cable": 0.35,
        "curb": 0.5,
        "figaro": 0.45,
        "rope": 0.6,
        "snake": 0.4,
        "box": 0.55,
        "herringbone": 0.7,
        "wheat": 0.65
    }
    
    if chain_type.lower() not in chain_factors:
        logger.error(f"Unsupported chain type: {chain_type}")
        raise ValueError(f"Unsupported chain type: {chain_type}")
    
    # Base factor based on chain type
    base_factor = chain_factors[chain_type.lower()]
    
    # Adjust for link size if provided
    if link_diameter_mm:
        # Standard link size is typically 2mm for the calculation factors
        link_factor = (link_diameter_mm / 2) ** 2
    else:
        link_factor = 1.0
    
    # Calculate weight
    weight = length_mm * base_factor * link_factor * (density / 10)
    
    logger.info(f"Calculated {metal_type} {chain_type} chain weight: {weight:.2f}g")
    return weight

# Additional helper functions for special cases

def estimate_setting_weight(setting_type, stone_count, metal_type):
    """
    Estimate weight of prongs, bezels, or other setting components.
    
    Args:
        setting_type (str): Type of setting (e.g., "prong", "bezel", "channel")
        stone_count (int): Number of stones in the setting
        metal_type (str): The metal type
    
    Returns:
        float: Estimated weight in grams
    """
    # Get metal density
    if metal_type not in METAL_DENSITIES:
        logger.error(f"Unknown metal type: {metal_type}")
        raise ValueError(f"Unknown metal type: {metal_type}")
    
    density = METAL_DENSITIES[metal_type]
    
    # Setting type base volumes in mm³
    setting_volumes = {
        "prong": 2.0,  # per prong
        "bezel": 12.0,  # per stone
        "channel": 8.0,  # per stone
        "pavé": 1.5,  # per stone
        "halo": 15.0,  # for entire halo
        "cathedral": 20.0  # additional structure
    }
    
    if setting_type.lower() not in setting_volumes:
        logger.error(f"Unsupported setting type: {setting_type}")
        raise ValueError(f"Unsupported setting type: {setting_type}")
    
    base_volume = setting_volumes[setting_type.lower()]
    
    # Calculate volume based on setting type
    if setting_type.lower() == "prong":
        # Typical rings have 4 or 6 prongs per stone
        prongs_per_stone = 4  # default assumption
        volume_mm3 = base_volume * prongs_per_stone * stone_count
    else:
        volume_mm3 = base_volume * stone_count
    
    # Convert volume to weight
    volume_cm3 = volume_mm3 / 1000  # Convert mm³ to cm³
    weight = volume_cm3 * density
    
    logger.info(f"Estimated {setting_type} setting weight for {stone_count} stones: {weight:.2f}g")
    return weight

if __name__ == "__main__":
    # Example usage
    ring_weight = calculate_ring_weight(
        metal_type="14K Yellow Gold",
        ring_size=7.0,
        band_width=3.0,
        band_thickness=1.5,
        shank_style="comfort fit"
    )
    print(f"Ring weight: {ring_weight:.2f}g")
    
    stone_weight = calculate_stone_weight(
        stone_type="Diamond",
        shape="round",
        dimensions={"diameter": 6.5, "depth": 4.0}
    )
    print(f"Stone weight: {stone_weight['weight_carats']:.2f} carats")
    
    chain_weight = calculate_chain_weight(
        metal_type="14K Yellow Gold",
        length_mm=500,
        chain_type="cable",
        link_diameter_mm=1.5
    )
    print(f"Chain weight: {chain_weight:.2f}g") 