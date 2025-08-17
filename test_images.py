#!/usr/bin/env python3
"""
Test script to verify image functionality with existing data structure
"""

import json
from pathlib import Path
from src.models import FarmShop

def test_image_functionality():
    """Test that the image functionality works with existing data"""
    
    print("🧪 Testing Image Functionality")
    print("=" * 40)
    
    # Test creating a FarmShop with images
    test_shop = FarmShop(
        name="Test Farm Shop",
        slug="test-farm-shop",
        location={
            "address": "123 Test Street",
            "city": "Test City",
            "county": "Test County",
            "postcode": "TE1 1ST",
            "lat": 51.5074,
            "lng": -0.1278
        },
        images=[
            "https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference=test1&key=test",
            "https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference=test2&key=test"
        ]
    )
    
    print(f"✅ Created test shop: {test_shop.name}")
    print(f"📸 Images: {len(test_shop.images)}")
    
    # Test JSON serialization
    shop_dict = test_shop.model_dump()
    print(f"✅ JSON serialization works: {len(shop_dict)} fields")
    
    # Check if images field exists
    if 'images' in shop_dict:
        print(f"✅ Images field present: {len(shop_dict['images'])} images")
    else:
        print("❌ Images field missing")
    
    # Test with existing data
    farms_file = Path("dist/farms.uk.json")
    if farms_file.exists():
        with open(farms_file, 'r') as f:
            farms_data = json.load(f)
        
        print(f"\n📊 Existing data analysis:")
        print(f"   Total farms: {len(farms_data)}")
        
        farms_with_images = sum(1 for farm in farms_data if farm.get('images'))
        total_images = sum(len(farm.get('images', [])) for farm in farms_data)
        
        print(f"   Farms with images: {farms_with_images}")
        print(f"   Total images: {total_images}")
        
        if farms_with_images > 0:
            print(f"   Average images per shop: {total_images/farms_with_images:.1f}")
        
        # Show sample farm with images
        for farm in farms_data[:3]:
            if farm.get('images'):
                print(f"\n🏪 Sample: {farm['name']}")
                print(f"   📸 {len(farm['images'])} images")
                break
    else:
        print("\n📝 No existing data found. Run ./google_places.sh to generate data with images.")
    
    print("\n✅ Image functionality test completed!")

if __name__ == "__main__":
    test_image_functionality()
