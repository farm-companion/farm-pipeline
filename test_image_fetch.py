#!/usr/bin/env python3
"""
Test script to demonstrate image fetching for existing farms
"""

import json
from pathlib import Path

def test_image_fetch():
    """Test the image fetching process"""
    
    print("🧪 Testing Image Fetch Process")
    print("=" * 40)
    
    # Load existing farms
    farms_file = Path(__file__).parent.parent / "farm-frontend" / "public" / "data" / "farms.uk.json"
    
    if not farms_file.exists():
        print("❌ Farms data file not found")
        return
    
    with open(farms_file, 'r') as f:
        farms = json.load(f)
    
    print(f"📊 Found {len(farms)} existing farms")
    
    # Show sample farms that would get images
    print("\n🏪 Sample farms that would get images:")
    for i, farm in enumerate(farms[:5]):
        shop_name = farm['name']
        address = f"{farm['location']['address']}, {farm['location']['city']}"
        has_images = bool(farm.get('images'))
        
        status = f"✅ Has {len(farm['images'])} images" if has_images else "📸 Would get images"
        
        print(f"  {i+1}. {shop_name}")
        print(f"     📍 {address}")
        print(f"     {status}")
        print()
    
    # Show the process
    print("🔄 Image Fetch Process:")
    print("  1. Load existing farm data")
    print("  2. Search Google Places for each farm")
    print("  3. Get up to 3 images per farm")
    print("  4. Add images to existing data")
    print("  5. Save updated data")
    
    # Show cost estimation
    print("\n💰 Cost Estimation:")
    print("  • Text Search: $0.017 per farm")
    print("  • Place Details: $0.017 per farm")
    print("  • Photos (3 per farm): $0.021 per farm")
    print("  • Total per farm: ~$0.055")
    print("  • 10 farms: ~$0.55")
    print("  • 100 farms: ~$5.50")
    
    # Show benefits
    print("\n🎯 Benefits:")
    print("  ✅ Real, authentic farm shop photos")
    print("  ✅ No changes to existing data")
    print("  ✅ Fast implementation")
    print("  ✅ Cost-effective")
    print("  ✅ Professional appearance")
    
    # Show setup steps
    print("\n🚀 Setup Steps:")
    print("  1. Get Google Places API key")
    print("  2. Set environment variable: GOOGLE_PLACES_API_KEY")
    print("  3. Run: ./fetch_images.sh")
    print("  4. Check the frontend for new images")
    
    print("\n✅ Image fetch test completed!")

if __name__ == "__main__":
    test_image_fetch()
