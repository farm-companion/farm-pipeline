#!/usr/bin/env python3
"""
Convert farms.uk.json to farms.geo.json for map display
"""

import json
import sys
from pathlib import Path

def convert_to_geojson(input_file: str, output_file: str):
    """Convert farms JSON to GeoJSON format"""
    
    # Read the farms data
    with open(input_file, 'r', encoding='utf-8') as f:
        farms = json.load(f)
    
    # Create GeoJSON structure
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }
    
    # Convert each farm to a GeoJSON feature
    for farm in farms:
        # Check for different possible location formats
        lat = None
        lng = None
        
        if 'latitude' in farm and 'longitude' in farm:
            lat = farm['latitude']
            lng = farm['longitude']
        elif 'location' in farm and 'lat' in farm['location'] and 'lng' in farm['location']:
            lat = farm['location']['lat']
            lng = farm['location']['lng']
        
        if lat is not None and lng is not None:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(lng), float(lat)]
                },
                "properties": {
                    "id": farm.get('id', ''),
                    "name": farm.get('name', ''),
                    "slug": farm.get('slug', ''),
                    "address": farm.get('location', {}).get('address', '') if 'location' in farm else farm.get('address', ''),
                    "phone": farm.get('contact', {}).get('phone', '') if 'contact' in farm else farm.get('phone', ''),
                    "email": farm.get('contact', {}).get('email', '') if 'contact' in farm else farm.get('email', ''),
                    "website": farm.get('contact', {}).get('website', '') if 'contact' in farm else farm.get('website', ''),
                    "description": farm.get('description', ''),
                    "hours": farm.get('hours', {}),
                    "county": farm.get('location', {}).get('county', '') if 'location' in farm else farm.get('county', ''),
                    "rating": farm.get('rating'),
                    "user_ratings_total": farm.get('user_ratings_total'),
                    "price_level": farm.get('price_level'),
                    "place_id": farm.get('place_id', ''),
                    "types": farm.get('types', [])
                }
            }
            geojson["features"].append(feature)
    
    # Write the GeoJSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Converted {len(geojson['features'])} farms to GeoJSON")
    print(f"📁 Output: {output_file}")

if __name__ == "__main__":
    # Default paths
    input_file = "../farm-frontend/public/data/farms.uk.json"
    output_file = "../farm-frontend/public/data/farms.geo.json"
    
    # Use command line arguments if provided
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    # Check if input file exists
    if not Path(input_file).exists():
        print(f"❌ Input file not found: {input_file}")
        sys.exit(1)
    
    try:
        convert_to_geojson(input_file, output_file)
    except Exception as e:
        print(f"❌ Error converting to GeoJSON: {e}")
        sys.exit(1)
