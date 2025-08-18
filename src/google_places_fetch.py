#!/usr/bin/env python3
"""
Fetch UK farm shops using Google Places API.
Searches major UK cities and regions systematically.
"""

import asyncio
import json
import os
import sys
import argparse
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
    page_token = None
    
    while True:
        if page_token:
            params["pagetoken"] = page_token
        
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] == "OK":
                all_results.extend(data["results"])
                page_token = data.get("next_page_token")
                
                if not page_token:
                    break
                    
                # Wait before requesting next page
                await asyncio.sleep(2)
            else:
                print(f"⚠️  API Error: {data['status']} - {data.get('error_message', 'Unknown error')}")
                break
                
        except Exception as e:
            print(f"❌ Error fetching places: {e}")
            break
    
    return all_results

async def get_place_details(client: httpx.AsyncClient, place_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed information for a place."""
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,address_components,international_phone_number,rating,user_ratings_total,price_level,reviews,editorial_summary,photos,website,url",
        "key": GOOGLE_API_KEY
    }
    
    try:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data["status"] == "OK":
            return data["result"]
        else:
            print(f"⚠️  Details API Error: {data['status']} for {place_id}")
            return None
            
    except Exception as e:
        print(f"❌ Error fetching details for {place_id}: {e}")
        return None

async def get_place_images(client: httpx.AsyncClient, place_id: str, photos: List[Dict], max_images: int = 1) -> List[str]:
    """Get image URLs for a place."""
    image_urls = []
    
    for i, photo in enumerate(photos[:max_images]):
        try:
            # Get the photo reference
            photo_ref = photo.get("photo_reference")
            if not photo_ref:
                continue
            
            # Construct the image URL
            image_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference={photo_ref}&key={GOOGLE_API_KEY}"
            
            # Verify the image URL is accessible
            async with httpx.AsyncClient(follow_redirects=True) as img_client:
                head_response = await img_client.head(image_url)
                if head_response.status_code == 200:
                    image_urls.append(image_url)
                else:
                    print(f"⚠️  Image not accessible for {place_id}")
                    
        except Exception as e:
            print(f"❌ Error processing image for {place_id}: {e}")
            continue
    
    return image_urls

def parse_address_components(address_components: List[Dict], formatted_address: str) -> Dict[str, str]:
    """Parse address components into structured format."""
    result = {
        "address": "",
        "city": "",
        "county": "",
        "postcode": "",
        "country": ""
    }
    
    for component in address_components:
        types = component.get("types", [])
        long_name = component.get("long_name", "")
        short_name = component.get("short_name", "")
        
        if "street_number" in types or "route" in types:
            if result["address"]:
                result["address"] += ", " + long_name
            else:
                result["address"] = long_name
        elif "locality" in types or "sublocality" in types:
            result["city"] = long_name
        elif "administrative_area_level_1" in types:
            result["county"] = long_name
        elif "postal_code" in types:
            result["postcode"] = long_name
        elif "country" in types:
            result["country"] = long_name
    
    # Fallback: if no structured address, use formatted address
    if not result["address"]:
        parts = formatted_address.split(',')
        if len(parts) >= 2:
            result["address"] = parts[0].strip()
            if len(parts) > 2:
                result["city"] = parts[-2].strip()
            result["postcode"] = parts[-1].strip()
    
    return result

def parse_address(address: str) -> Dict[str, str]:
    """Legacy function for backward compatibility."""
    parts = address.split(',')
    if len(parts) >= 2:
        street = parts[0].strip()
        city = parts[-2].strip() if len(parts) > 2 else parts[-1].strip()
        postcode = parts[-1].strip()
        
        return {
            "address": street,
            "city": city,
            "county": "",
            "postcode": postcode
        }
    
    return {"address": address, "city": "", "county": "", "postcode": ""}

async def main():
    """Main function to fetch all UK farm shops."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Fetch UK farm shops from Google Places API')
    parser.add_argument('--no-images', action='store_true', help='Skip fetching images to save API calls')
    parser.add_argument('--images-only', action='store_true', help='Only fetch images for existing farms (requires farms.uk.json)')
    parser.add_argument('--max-images', type=int, default=1, help='Maximum number of images per farm (default: 1)')
    args = parser.parse_args()
    
    if args.images_only:
        await fetch_images_only(args.max_images)
        return
    
    print("🔍 Starting Google Places farm shop search...")
    if args.no_images:
        print("📸 Image fetching disabled - will save API calls")
    
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
                    
                    # Get images only if not disabled
                    if not args.no_images:
                        photos = details.get('photos', [])
                        if photos:
                            print(f"  📸 Found {len(photos)} photos for {place.get('name', 'Unknown')}")
                            images = await get_place_images(client, place_id, photos, args.max_images)
                            place['images'] = images
                        else:
                            place['images'] = []
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
    if not args.no_images:
        print(f"📸 {shops_with_images} shops have images ({shops_with_images/len(all_places)*100:.1f}%)")
    
    # Convert to FarmShop models
    shops = []
    for place in all_places:
        try:
            name = place.get('name', 'Unknown Farm Shop')
            
            # Use address components if available, otherwise fallback to formatted address
            if place.get('address_components'):
                address_info = parse_address_components(place.get('address_components', []), place.get('formatted_address', ''))
            else:
                address_info = parse_address(place.get('formatted_address', ''))
            
            # Create location object
            location = Location(
                lat=place.get('geometry', {}).get('location', {}).get('lat', 0),
                lng=place.get('geometry', {}).get('location', {}).get('lng', 0),
                address=address_info.get('address', ''),
                city=address_info.get('city', ''),
                county=address_info.get('county', ''),
                postcode=address_info.get('postcode', '')
            )
            
            # Create contact object
            contact = Contact(
                phone=place.get('international_phone_number', ''),
                email=None,  # Google Places doesn't provide email
                website=place.get('website', '')
            )
            
            # Create farm shop object
            shop = FarmShop(
                id=f"farm_{slugify(name)}",
                name=name,
                slug=slugify(name),
                location=location,
                contact=contact,
                offerings=place.get('offerings', []),
                images=place.get('images', []),
                rating=place.get('rating'),
                user_ratings_total=place.get('user_ratings_total'),
                price_level=place.get('price_level'),
                place_id=place.get('place_id'),
                types=place.get('types', [])
            )
            
            shops.append(shop)
            
        except Exception as e:
            print(f"❌ Error processing {place.get('name', 'Unknown')}: {e}")
            continue
    
    # Save to JSON files
    output_dir = Path("dist")
    output_dir.mkdir(exist_ok=True)
    
    # Save as JSON
    with open(output_dir / "farms.uk.json", "w", encoding="utf-8") as f:
        json.dump([shop.dict() for shop in shops], f, indent=2, ensure_ascii=False)
    
    # Save as GeoJSON for mapping
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }
    
    for shop in shops:
        feature = {
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
                "postcode": shop.location.postcode,
                "phone": shop.contact.phone,
                "website": shop.contact.website,
                "offerings": shop.offerings,
                "rating": shop.rating,
                "user_ratings_total": shop.user_ratings_total,
                "price_level": shop.price_level,
                "place_id": shop.place_id,
                "types": shop.types
            }
        }
        geojson["features"].append(feature)
    
    with open(output_dir / "farms.geo.json", "w", encoding="utf-8") as f:
        json.dump(geojson, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved {len(shops)} farm shops to dist/farms.uk.json and dist/farms.geo.json")

async def fetch_images_only(max_images: int = 1):
    """Fetch only images for existing farms."""
    print("📸 Fetching images for existing farms...")
    
    # Load existing farms
    try:
        with open("dist/farms.uk.json", "r", encoding="utf-8") as f:
            farms_data = json.load(f)
    except FileNotFoundError:
        print("❌ farms.uk.json not found. Run the main script first.")
        return
    
    updated_farms = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, farm in enumerate(farms_data):
            print(f"📸 Processing {i+1}/{len(farms_data)}: {farm['name']}")
            
            place_id = farm.get('place_id')
            if not place_id:
                print(f"  ⚠️  No place_id for {farm['name']}, skipping")
                updated_farms.append(farm)
                continue
            
            # Get place details to check for photos
            details = await get_place_details(client, place_id)
            if details and details.get('photos'):
                photos = details['photos']
                print(f"  📸 Found {len(photos)} photos")
                images = await get_place_images(client, place_id, photos, max_images)
                farm['images'] = images
            else:
                farm['images'] = []
                print(f"  📸 No photos found")
            
            updated_farms.append(farm)
            
            # Be nice to the API
            await asyncio.sleep(1)
    
    # Save updated farms
    with open("dist/farms.uk.json", "w", encoding="utf-8") as f:
        json.dump(updated_farms, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Updated {len(updated_farms)} farms with images")

if __name__ == "__main__":
    asyncio.run(main())
