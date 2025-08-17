#!/usr/bin/env python3
"""
Script to add sample images to farm shops for demonstration purposes.
This adds placeholder images from Unsplash to show how the image gallery works.
"""

import json
import os
from pathlib import Path

# Sample images from Unsplash (free to use, high quality)
SAMPLE_IMAGES = [
    "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop",
    "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=800&h=600&fit=crop", 
    "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop",
    "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=800&h=600&fit=crop",
    "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop"
]

def add_sample_images():
    """Add sample images to some farm shops for demonstration."""
    
    # Path to the farms data file
    farms_file = Path(__file__).parent.parent / "farm-frontend" / "public" / "data" / "farms.uk.json"
    
    if not farms_file.exists():
        print(f"Error: Farms data file not found at {farms_file}")
        return
    
    # Read the current data
    with open(farms_file, 'r', encoding='utf-8') as f:
        farms = json.load(f)
    
    # Add images to the first 5 farms (for demonstration)
    farms_with_images = 0
    for i, farm in enumerate(farms[:5]):
        if not farm.get('images'):
            # Add 2-3 sample images per farm
            num_images = min(3, len(SAMPLE_IMAGES))
            farm['images'] = SAMPLE_IMAGES[:num_images]
            farms_with_images += 1
            print(f"Added {num_images} images to {farm['name']}")
    
    # Write back the updated data
    with open(farms_file, 'w', encoding='utf-8') as f:
        json.dump(farms, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Added images to {farms_with_images} farm shops")
    print("The image gallery will now show sample farm shop photos!")

if __name__ == "__main__":
    add_sample_images()
