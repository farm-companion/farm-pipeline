#!/usr/bin/env python3
"""
Fetch images for existing farm shops using Google Places API.
This script only adds images to existing farm data without changing other information.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import httpx
import time

# Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')
if not GOOGLE_API_KEY:
    print("❌ GOOGLE_PLACES_API_KEY environment variable required")
    print("Please set your Google Places API key:")
    print("export GOOGLE_PLACES_API_KEY='your_api_key_here'")
    sys.exit(1)

class ImageFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/place"
        self.session = httpx.AsyncClient(timeout=30.0)
        
    async def search_place(self, shop_name: str, address: str) -> Optional[str]:
        """Search for a place using Google Places API Text Search"""
        try:
            query = f"{shop_name} {address}"
            
            url = f"{self.base_url}/textsearch/json"
            params = {
                'query': query,
                'key': self.api_key,
                'type': 'establishment'
            }
            
            response = await self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                place = data['results'][0]
                print(f"    ✅ Found: {place['name']}")
                return place['place_id']
            else:
                print(f"    ❌ No place found for: {query}")
                return None
                
        except Exception as e:
            print(f"    ❌ Error searching for {shop_name}: {e}")
            return None
    
    async def get_place_images(self, place_id: str, max_images: int = 3) -> List[str]:
        """Get image URLs for a place from Google Places API"""
        try:
            url = f"{self.base_url}/details/json"
            params = {
                'place_id': place_id,
                'key': self.api_key,
                'fields': 'photos'
            }
            
            response = await self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] != 'OK' or 'photos' not in data.get('result', {}):
                return []
            
            photos = data['result']['photos']
            image_urls = []
            
            # Limit to max_images
            photos = photos[:max_images]
            
            for i, photo in enumerate(photos):
                try:
                    photo_reference = photo.get('photo_reference')
                    if not photo_reference:
                        continue
                    
                    # Build Google Places photo URL
                    image_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference={photo_reference}&key={self.api_key}"
                    image_urls.append(image_url)
                    
                    print(f"      📸 Added image {i+1}")
                    
                    # Rate limiting between image requests
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    print(f"      ❌ Error getting image {i+1}: {e}")
                    continue
            
            return image_urls
            
        except Exception as e:
            print(f"    ❌ Error getting images for {place_id}: {e}")
            return []
    
    async def process_farm_images(self, farm: Dict) -> List[str]:
        """Process a single farm to get images from Google Places"""
        shop_name = farm['name']
        address = f"{farm['location']['address']}, {farm['location']['city']}"
        
        print(f"🔍 Processing: {shop_name}")
        
        # Search for the place
        place_id = await self.search_place(shop_name, address)
        if not place_id:
            return []
        
        # Get images
        images = await self.get_place_images(place_id)
        
        if images:
            print(f"    ✅ Found {len(images)} images")
        else:
            print(f"    ❌ No images found")
        
        return images

async def load_existing_farms() -> List[Dict]:
    """Load existing farms data"""
    farms_file = Path(__file__).parent.parent / "farm-frontend" / "public" / "data" / "farms.uk.json"
    
    if not farms_file.exists():
        raise FileNotFoundError(f"Farms data file not found at {farms_file}")
    
    with open(farms_file, 'r', encoding='utf-8') as f:
        return json.load(f)

async def save_farms_data(farms: List[Dict]):
    """Save farms data back to file"""
    farms_file = Path(__file__).parent.parent / "farm-frontend" / "public" / "data" / "farms.uk.json"
    
    with open(farms_file, 'w', encoding='utf-8') as f:
        json.dump(farms, f, indent=2, ensure_ascii=False)

async def main():
    """Main function to fetch images for existing farms"""
    print("🖼️  Starting image fetch for existing farm shops...")
    print(f"🔑 Using API key: {GOOGLE_API_KEY[:10]}...")
    
    # Load existing farms
    try:
        farms = await load_existing_farms()
        print(f"📊 Loaded {len(farms)} existing farms")
    except Exception as e:
        print(f"❌ Error loading farms: {e}")
        return
    
    # Initialize image fetcher
    fetcher = ImageFetcher(GOOGLE_API_KEY)
    
    # Process farms (limit for testing)
    processed_count = 0
    farms_with_images = 0
    total_images = 0
    
    # Process first 10 farms for testing
    for i, farm in enumerate(farms[:10]):
        if farm.get('images'):
            print(f"⏭️  Skipping {farm['name']} - already has {len(farm['images'])} images")
            continue
        
        try:
            images = await fetcher.process_farm_images(farm)
            if images:
                farm['images'] = images
                farms_with_images += 1
                total_images += len(images)
                print(f"✅ Added {len(images)} images to {farm['name']}")
            else:
                farm['images'] = []
                print(f"❌ No images found for {farm['name']}")
            
            processed_count += 1
            
            # Rate limiting between farms
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"❌ Error processing {farm['name']}: {e}")
            continue
    
    # Save updated data
    try:
        await save_farms_data(farms)
        print(f"\n✅ Successfully processed {processed_count} farms")
        print(f"📸 {farms_with_images} farms now have images")
        print(f"🖼️  Total images added: {total_images}")
        print("💾 Updated farms data saved")
        
        # Show statistics
        all_farms_with_images = sum(1 for farm in farms if farm.get('images'))
        all_total_images = sum(len(farm.get('images', [])) for farm in farms)
        print(f"\n📊 Overall statistics:")
        print(f"   Total farms: {len(farms)}")
        print(f"   Farms with images: {all_farms_with_images}")
        print(f"   Total images: {all_total_images}")
        if all_farms_with_images > 0:
            print(f"   Average images per shop: {all_total_images/all_farms_with_images:.1f}")
        
    except Exception as e:
        print(f"❌ Error saving farms data: {e}")

if __name__ == "__main__":
    asyncio.run(main())
