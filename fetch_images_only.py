#!/usr/bin/env python3
"""
Hybrid image fetching: Google Places (real photos) + fallback to curated farm images.
This script prioritizes real farm photos from Google Places, with fallback to quality farm images.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import httpx
import time
import random

# Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')
if not GOOGLE_API_KEY:
    print("❌ GOOGLE_PLACES_API_KEY environment variable required")
    print("Please set your Google Places API key:")
    print("export GOOGLE_PLACES_API_KEY='your_api_key_here'")
    sys.exit(1)

# High-quality fallback farm images (curated)
FALLBACK_IMAGES = [
    "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop",
    "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=800&h=600&fit=crop",
    "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop",
    "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=800&h=600&fit=crop",
    "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop",
    "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=800&h=600&fit=crop",
    "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop",
    "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=800&h=600&fit=crop",
    "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop",
    "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=800&h=600&fit=crop"
]

class ImageFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/place"
        self.session = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        
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
    
    async def get_place_images(self, place_id: str, max_images: int = 1) -> List[str]:
        """Get image URLs for a place from Google Places API with proper redirect handling"""
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
                    photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference={photo_reference}&key={self.api_key}"
                    
                    # Follow the redirect to get the actual image URL
                    try:
                        photo_response = await self.session.head(photo_url)
                        if photo_response.status_code == 200:
                            # If it's a redirect, get the final URL
                            final_url = str(photo_response.url)
                            image_urls.append(final_url)
                            print(f"      📸 Added real Google Places image {i+1}")
                        else:
                            print(f"      ⚠️  Photo {i+1} returned status {photo_response.status_code}")
                    except Exception as photo_error:
                        print(f"      ⚠️  Error following redirect for photo {i+1}: {photo_error}")
                        # Fallback to original URL
                        image_urls.append(photo_url)
                    
                    # Rate limiting between image requests
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    print(f"      ❌ Error getting image {i+1}: {e}")
                    continue
            
            return image_urls
            
        except Exception as e:
            print(f"    ❌ Error getting images for {place_id}: {e}")
            return []
    
    def get_fallback_image(self, shop_name: str) -> str:
        """Get a curated fallback farm image"""
        return random.choice(FALLBACK_IMAGES)
    
    async def process_farm_images(self, farm: Dict) -> List[str]:
        """Process a single farm to get images - Google Places first, fallback second"""
        shop_name = farm.get('name', 'Unknown Farm')
        print(f"🔍 Processing: {shop_name}")
        
        # Try Google Places first (real photos)
        try:
            address = f"{farm['location']['address']}, {farm['location']['city']}"
            
            # Search for the place
            place_id = await self.search_place(shop_name, address)
            if place_id:
                # Get images from Google Places
                images = await self.get_place_images(place_id)
                if images:
                    print(f"    ✅ Found {len(images)} real Google Places images")
                    return images
                else:
                    print(f"    ⚠️  No Google Places images found, using fallback")
            else:
                print(f"    ⚠️  Place not found in Google Places, using fallback")
                
        except Exception as e:
            print(f"    ⚠️  Google Places error: {e}, using fallback")
        
        # Fallback to curated farm image
        fallback_image = self.get_fallback_image(shop_name)
        print(f"    📸 Using curated fallback image")
        return [fallback_image]

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
    print("🖼️  Starting hybrid image fetch for existing farm shops...")
    print(f"🔑 Using Google Places API + fallback images")
    
    # Load existing farms
    try:
        farms = await load_existing_farms()
        print(f"📊 Loaded {len(farms)} existing farms")
    except Exception as e:
        print(f"❌ Error loading farms: {e}")
        return
    
    # Initialize image fetcher
    fetcher = ImageFetcher(GOOGLE_API_KEY)
    
    # Process farms that need images (clear existing problematic URLs)
    farms_to_process = []
    for farm in farms:
        # Clear existing problematic URLs
        if farm.get('images'):
            # Check if it's a problematic URL (contains photoreference or is fallback)
            if any('photoreference' in img or 'unsplash.com' in img for img in farm['images']):
                print(f"🔄 Clearing existing images for {farm['name']}")
                farm['images'] = []
        
        # Add to processing list if no images
        if not farm.get('images') or len(farm['images']) == 0:
            farms_to_process.append(farm)
    
    print(f"📋 Found {len(farms_to_process)} farms that need images")
    
    # Process first 20 farms that need images
    processed_count = 0
    farms_with_images = 0
    total_images = 0
    google_places_count = 0
    fallback_count = 0
    
    for i, farm in enumerate(farms_to_process):
        try:
            images = await fetcher.process_farm_images(farm)
            if images:
                farm['images'] = images
                farms_with_images += 1
                total_images += len(images)
                
                # Track source
                if any('googleusercontent.com' in img for img in images):
                    google_places_count += 1
                    print(f"✅ Added {len(images)} real Google Places images to {farm['name']}")
                else:
                    fallback_count += 1
                    print(f"✅ Added {len(images)} fallback image to {farm['name']}")
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
        print(f"🏪 Google Places images: {google_places_count}")
        print(f"🖼️  Fallback images: {fallback_count}")
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
