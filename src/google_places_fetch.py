#!/usr/bin/env python3
"""
Fetch UK farm shops using Google Places API.
Searches major UK cities and regions systematically.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import httpx
from models import FarmShop, Location, Contact
from utils_geo import slugify, haversine_km
from description_generator import enhance_place_data_with_description

# Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')
if not GOOGLE_API_KEY:
    print("❌ GOOGLE_PLACES_API_KEY environment variable required")
    sys.exit(1)

# Major UK cities/regions to search
UK_LOCATIONS = [
    # England - Major cities
    {"name": "London", "lat": 51.5074, "lng": -0.1278},
    {"name": "Manchester", "lat": 53.4808, "lng": -2.2426},
    {"name": "Birmingham", "lat": 52.4862, "lng": -1.8904},
    {"name": "Leeds", "lat": 53.8008, "lng": -1.5491},
    {"name": "Liverpool", "lat": 53.4084, "lng": -2.9916},
    {"name": "Sheffield", "lat": 53.3811, "lng": -1.4701},
    {"name": "Bristol", "lat": 51.4545, "lng": -2.5879},
    {"name": "Newcastle", "lat": 54.9783, "lng": -1.6178},
    {"name": "Nottingham", "lat": 52.9548, "lng": -1.1581},
    {"name": "Leicester", "lat": 52.6369, "lng": -1.1398},
    
    # Scotland
    {"name": "Edinburgh", "lat": 55.9533, "lng": -3.1883},
    {"name": "Glasgow", "lat": 55.8642, "lng": -4.2518},
    {"name": "Aberdeen", "lat": 57.1497, "lng": -2.0943},
    
    # Wales
    {"name": "Cardiff", "lat": 51.4816, "lng": -3.1791},
    {"name": "Swansea", "lat": 51.6214, "lng": -3.9436},
    
    # Northern Ireland
    {"name": "Belfast", "lat": 54.5973, "lng": -5.9301},
    
    # Rural areas (county centers)
    {"name": "Cornwall", "lat": 50.2660, "lng": -5.0527},
    {"name": "Devon", "lat": 50.7156, "lng": -3.5309},
    {"name": "Somerset", "lat": 51.1052, "lng": -2.9262},
    {"name": "Dorset", "lat": 50.7488, "lng": -2.3445},
    {"name": "Kent", "lat": 51.2787, "lng": 0.5217},
    {"name": "Sussex", "lat": 50.9097, "lng": -0.4617},
    {"name": "Norfolk", "lat": 52.6143, "lng": 0.8883},
    {"name": "Suffolk", "lat": 52.1872, "lng": 0.9708},
    {"name": "Essex", "lat": 51.7500, "lng": 0.5000},
    {"name": "Hertfordshire", "lat": 51.8098, "lng": -0.2377},
    {"name": "Bedfordshire", "lat": 52.0026, "lng": -0.4653},
    {"name": "Buckinghamshire", "lat": 51.8167, "lng": -0.8167},
    {"name": "Oxfordshire", "lat": 51.7500, "lng": -1.2500},
    {"name": "Gloucestershire", "lat": 51.8642, "lng": -2.2380},
    {"name": "Wiltshire", "lat": 51.3492, "lng": -1.9927},
    {"name": "Hampshire", "lat": 51.0577, "lng": -1.3080},
    {"name": "Surrey", "lat": 51.2500, "lng": -0.3333},
    {"name": "Berkshire", "lat": 51.4000, "lng": -1.0000},
    {"name": "Warwickshire", "lat": 52.2833, "lng": -1.5833},
    {"name": "Worcestershire", "lat": 52.1919, "lng": -2.2215},
    {"name": "Herefordshire", "lat": 52.0765, "lng": -2.6544},
    {"name": "Shropshire", "lat": 52.6599, "lng": -2.7237},
    {"name": "Staffordshire", "lat": 52.8833, "lng": -2.0333},
    {"name": "Derbyshire", "lat": 53.1333, "lng": -1.6000},
    {"name": "Nottinghamshire", "lat": 53.1333, "lng": -1.2000},
    {"name": "Lincolnshire", "lat": 53.1000, "lng": -0.2000},
    {"name": "Yorkshire", "lat": 53.9597, "lng": -1.0792},
    {"name": "Lancashire", "lat": 53.8000, "lng": -2.6000},
    {"name": "Cheshire", "lat": 53.1667, "lng": -2.5833},
    {"name": "Cumbria", "lat": 54.5772, "lng": -2.7975},
    {"name": "Northumberland", "lat": 55.2083, "lng": -2.0784},
    {"name": "Durham", "lat": 54.7761, "lng": -1.5733},
    {"name": "North Yorkshire", "lat": 54.0000, "lng": -1.5000},
    {"name": "East Yorkshire", "lat": 53.8419, "lng": -0.4276},
    {"name": "South Yorkshire", "lat": 53.5000, "lng": -1.3000},
    {"name": "West Yorkshire", "lat": 53.8000, "lng": -1.5491},
]

async def search_places_nearby(client: httpx.AsyncClient, lat: float, lng: float, radius: int = 50000) -> List[Dict[str, Any]]:
    """Search for farm shops near a location."""
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "keyword": "farm shop",
        "type": "food",
        "key": GOOGLE_API_KEY
    }
    
    all_results = []
    next_page_token = None
    
    try:
        while True:
            if next_page_token:
                params["pagetoken"] = next_page_token
                await asyncio.sleep(2)  # Required delay for pagetoken
            
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] != "OK" and data["status"] != "ZERO_RESULTS":
                print(f"⚠️  API error for {lat},{lng}: {data['status']}")
                break
            
            if data["status"] == "ZERO_RESULTS":
                break
            
            all_results.extend(data.get("results", []))
            next_page_token = data.get("next_page_token")
            
            if not next_page_token:
                break
                
    except Exception as e:
        print(f"❌ Error searching near {lat},{lng}: {e}")
    
    return all_results

async def get_place_details(client: httpx.AsyncClient, place_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed information for a specific place."""
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,formatted_phone_number,website,opening_hours,geometry,types,photos",
        "key": GOOGLE_API_KEY
    }
    
    try:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data["status"] == "OK":
            return data["result"]
        else:
            print(f"⚠️  Details error for {place_id}: {data['status']}")
            return None
            
    except Exception as e:
        print(f"❌ Error getting details for {place_id}: {e}")
        return None

async def get_place_images(client: httpx.AsyncClient, place_id: str, photos: List[Dict[str, Any]], max_images: int = 3) -> List[str]:
    """Get image URLs for a place from Google Places API."""
    image_urls = []
    
    if not photos:
        return image_urls
    
    # Limit to max_images
    photos = photos[:max_images]
    
    for i, photo in enumerate(photos):
        try:
            photo_reference = photo.get('photo_reference')
            if not photo_reference:
                continue
            
            # Build Google Places photo URL
            image_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference={photo_reference}&key={GOOGLE_API_KEY}"
            image_urls.append(image_url)
            
            print(f"    📸 Added image {i+1} for {place_id}")
            
            # Rate limiting between image requests
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"    ❌ Error getting image {i+1} for {place_id}: {e}")
            continue
    
    return image_urls

def parse_address(address: str) -> Dict[str, str]:
    """Parse address into components."""
    # Basic parsing - you might want to use a proper address parser
    parts = address.split(',')
    if len(parts) >= 2:
        street = parts[0].strip()
        city = parts[-2].strip() if len(parts) > 2 else parts[-1].strip()
        postcode = parts[-1].strip()
        
        # Extract county from address
        county = ""
        for part in parts[1:-1]:
            part = part.strip()
            if any(county_name in part.lower() for county_name in [
                'county', 'shire', 'hampshire', 'sussex', 'essex', 'kent', 'norfolk', 'suffolk'
            ]):
                county = part
                break
        
        return {
            "address": street,
            "city": city,
            "county": county,
            "postcode": postcode
        }
    
    return {"address": address, "city": "", "county": "", "postcode": ""}

async def main():
    """Main function to fetch all UK farm shops."""
    print("🔍 Starting Google Places farm shop search...")
    
    all_places = []
    seen_place_ids = set()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for location in UK_LOCATIONS:
            print(f"📍 Searching near {location['name']}...")
            
            places = await search_places_nearby(client, location['lat'], location['lng'])
            
            for place in places:
                place_id = place.get('place_id')
                if place_id in seen_place_ids:
                    continue
                
                seen_place_ids.add(place_id)
                
                # Get detailed information
                details = await get_place_details(client, place_id)
                if details:
                    place.update(details)
                    
                    # Get images if available
                    photos = details.get('photos', [])
                    if photos:
                        print(f"  📸 Found {len(photos)} photos for {place.get('name', 'Unknown')}")
                        images = await get_place_images(client, place_id, photos)
                        place['images'] = images
                    else:
                        place['images'] = []
                
                # Enhance with description and offerings
                enhanced_place = enhance_place_data_with_description(place)
                all_places.append(enhanced_place)
                print(f"  ✅ Found: {place.get('name', 'Unknown')}")
            
            # Be nice to the API
            await asyncio.sleep(1)
    
    # Count shops with images
    shops_with_images = sum(1 for place in all_places if place.get('images'))
    print(f"\n📊 Found {len(all_places)} unique farm shops")
    print(f"📸 {shops_with_images} shops have images ({shops_with_images/len(all_places)*100:.1f}%)")
    
    # Convert to FarmShop models
    shops = []
    for place in all_places:
        try:
            name = place.get('name', 'Unknown Farm Shop')
            address_info = parse_address(place.get('formatted_address', ''))
            
            # Create FarmShop object
            shop = FarmShop(
                name=name,
                slug=slugify(name),
                location=Location(
                    address=address_info['address'],
                    city=address_info['city'],
                    county=address_info['county'],
                    postcode=address_info['postcode'],
                    lat=place.get('geometry', {}).get('location', {}).get('lat', 0),
                    lng=place.get('geometry', {}).get('location', {}).get('lng', 0)
                ),
                contact=Contact(
                    phone=place.get('formatted_phone_number', ''),
                    website=place.get('website', '')
                ),
                offerings=place.get('extracted_offerings', ['farm shop']),  # Use enhanced offerings
                description=place.get('generated_description'),  # Add generated description
                images=place.get('images', []),  # Add images from Google Places
                verified=False,
                adsenseEligible=True
            )
            
            shops.append(shop)
            
        except Exception as e:
            print(f"❌ Error processing {place.get('name', 'Unknown')}: {e}")
    
    # Save results
    output_dir = Path("dist")
    output_dir.mkdir(exist_ok=True)
    
    # Save as JSON
    with open(output_dir / "farms.uk.json", "w") as f:
        json.dump([shop.model_dump() for shop in shops], f, indent=2)
    
    # Save as GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [shop.location.lng, shop.location.lat]
                },
                "properties": {
                    "id": shop.id,
                    "name": shop.name,
                    "slug": shop.slug,
                    "address": shop.location.address,
                    "city": shop.location.city,
                    "county": shop.location.county,
                    "postcode": shop.location.postcode
                }
            }
            for shop in shops
        ]
    }
    
    with open(output_dir / "farms.geo.json", "w") as f:
        json.dump(geojson, f, indent=2)
    
    # Count total images
    total_images = sum(len(shop.images) for shop in shops)
    print(f"✅ Saved {len(shops)} farm shops with {total_images} images to dist/farms.uk.json and dist/farms.geo.json")

if __name__ == "__main__":
    asyncio.run(main())
