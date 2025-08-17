#!/usr/bin/env python3
"""
Generate rich descriptions for farm shops using Google Places data.
"""

import os
import re
from typing import Dict, Any, List, Optional

def extract_offerings_from_place_data(place_data: Dict[str, Any]) -> List[str]:
    """Extract offerings from Google Places data."""
    offerings = []
    
    # Check business types
    types = place_data.get('types', [])
    if 'food' in types:
        offerings.append('fresh produce')
    if 'store' in types:
        offerings.append('farm shop')
    if 'restaurant' in types:
        offerings.append('café')
    if 'bakery' in types:
        offerings.append('bakery')
    if 'grocery_or_supermarket' in types:
        offerings.append('grocery')
    
    # Check for specific keywords in name or types
    name = place_data.get('name', '').lower()
    if 'organic' in name or 'organic' in str(types):
        offerings.append('organic produce')
    if 'dairy' in name or 'milk' in name:
        offerings.append('dairy products')
    if 'meat' in name or 'butcher' in name:
        offerings.append('meat')
    if 'eggs' in name or 'poultry' in name:
        offerings.append('eggs')
    if 'honey' in name:
        offerings.append('honey')
    if 'jam' in name or 'preserves' in name:
        offerings.append('preserves')
    
    # Default offerings if none found
    if not offerings:
        offerings = ['farm shop', 'fresh produce']
    
    return list(set(offerings))  # Remove duplicates

def generate_description(place_data: Dict[str, Any]) -> str:
    """Generate a rich description for a farm shop."""
    name = place_data.get('name', 'This farm shop')
    address_info = place_data.get('formatted_address', '')
    types = place_data.get('types', [])
    rating = place_data.get('rating')
    user_ratings_total = place_data.get('user_ratings_total', 0)
    
    # Extract location details
    county = ''
    city = ''
    if address_info:
        parts = address_info.split(', ')
        if len(parts) >= 2:
            city = parts[-2] if parts[-2] and not parts[-2].isdigit() else ''
            county = parts[-3] if len(parts) >= 3 and not parts[-3].isdigit() else ''
    
    # Generate offerings
    offerings = extract_offerings_from_place_data(place_data)
    
    # Build description
    description_parts = []
    
    # Opening
    if county:
        description_parts.append(f"Located in the heart of {county}")
    elif city:
        description_parts.append(f"Situated in {city}")
    else:
        description_parts.append("Nestled in the countryside")
    
    # What they offer
    if len(offerings) == 1:
        description_parts.append(f"{name} specializes in {offerings[0]}.")
    elif len(offerings) == 2:
        description_parts.append(f"{name} offers {offerings[0]} and {offerings[1]}.")
    else:
        offerings_text = ', '.join(offerings[:-1]) + f" and {offerings[-1]}"
        description_parts.append(f"{name} provides {offerings_text}.")
    
    # Quality indicators
    if rating and rating >= 4.0:
        description_parts.append("Known for their high-quality, locally-sourced products.")
    elif rating and rating >= 3.5:
        description_parts.append("A trusted source for fresh, local produce.")
    else:
        description_parts.append("Supporting local farmers and sustainable agriculture.")
    
    # Community aspect
    description_parts.append("Perfect for those looking to support local businesses and enjoy the freshest seasonal produce.")
    
    # Join the description
    description = ' '.join(description_parts)
    
    # Ensure it's not too long (aim for 150-200 words)
    if len(description) > 300:
        # Truncate and add ellipsis
        description = description[:297] + "..."
    
    return description

def enhance_place_data_with_description(place_data: Dict[str, Any]) -> Dict[str, Any]:
    """Enhance place data with generated description and offerings."""
    # Generate description
    description = generate_description(place_data)
    
    # Extract offerings
    offerings = extract_offerings_from_place_data(place_data)
    
    # Add to place data
    enhanced_data = place_data.copy()
    enhanced_data['generated_description'] = description
    enhanced_data['extracted_offerings'] = offerings
    
    return enhanced_data
