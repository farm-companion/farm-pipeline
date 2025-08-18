#!/bin/bash

# Google Places API Operations Script
# This script provides easy commands for different Google Places operations

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if API key is set
check_api_key() {
    if [ -z "$GOOGLE_PLACES_API_KEY" ]; then
        print_error "GOOGLE_PLACES_API_KEY environment variable is not set"
        echo "Please set it with: export GOOGLE_PLACES_API_KEY='your-api-key'"
        exit 1
    fi
    print_success "API key is configured"
}

# Function to show usage
show_usage() {
    echo "Google Places API Operations"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  data-only     - Fetch farm data only (no images) - FAST & CHEAP"
    echo "  data+images   - Fetch farm data with images - SLOWER & MORE EXPENSIVE"
    echo "  images-only   - Fetch images for existing farms - MEDIUM SPEED"
    echo "  update-data   - Update existing farm data (address, contact, etc.)"
    echo "  help          - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 data-only     # Quick data fetch, saves API calls"
    echo "  $0 images-only   # Add images to existing farms"
    echo "  $0 data+images   # Full fetch with images"
    echo ""
    echo "Cost Guide:"
    echo "  - data-only: ~$5-10 (basic data)"
    echo "  - images-only: ~$10-20 (just images)"
    echo "  - data+images: ~$15-30 (everything)"
    echo ""
}

# Function to fetch data only (no images)
fetch_data_only() {
    print_status "Fetching farm data only (no images) - FAST & CHEAP"
    check_api_key
    
    cd "$(dirname "$0")"
    python3 src/google_places_fetch.py --no-images
    
    print_success "Data fetch complete! Copying to frontend..."
    cp dist/farms.uk.json ../farm-frontend/public/data/
    cp dist/farms.geo.json ../farm-frontend/public/data/
    print_success "Files copied to frontend"
}

# Function to fetch data with images
fetch_data_with_images() {
    print_status "Fetching farm data with images - SLOWER & MORE EXPENSIVE"
    check_api_key
    
    cd "$(dirname "$0")"
    python3 src/google_places_fetch.py
    
    print_success "Data + images fetch complete! Copying to frontend..."
    cp dist/farms.uk.json ../farm-frontend/public/data/
    cp dist/farms.geo.json ../farm-frontend/public/data/
    print_success "Files copied to frontend"
}

# Function to fetch images only
fetch_images_only() {
    print_status "Fetching images for existing farms - MEDIUM SPEED"
    check_api_key
    
    cd "$(dirname "$0")"
    
    # Check if farms.uk.json exists
    if [ ! -f "dist/farms.uk.json" ]; then
        print_error "farms.uk.json not found. Run 'data-only' first."
        exit 1
    fi
    
    python3 src/google_places_fetch.py --images-only
    
    print_success "Images fetch complete! Copying to frontend..."
    cp dist/farms.uk.json ../farm-frontend/public/data/
    print_success "Files copied to frontend"
}

# Function to update existing data
update_data() {
    print_status "Updating existing farm data (address, contact, etc.)"
    check_api_key
    
    cd "$(dirname "$0")"
    
    # Check if farms.uk.json exists
    if [ ! -f "dist/farms.uk.json" ]; then
        print_error "farms.uk.json not found. Run 'data-only' first."
        exit 1
    fi
    
    python3 src/google_places_fetch.py --no-images
    
    print_success "Data update complete! Copying to frontend..."
    cp dist/farms.uk.json ../farm-frontend/public/data/
    cp dist/farms.geo.json ../farm-frontend/public/data/
    print_success "Files copied to frontend"
}

# Main script logic
case "${1:-help}" in
    "data-only")
        fetch_data_only
        ;;
    "data+images")
        fetch_data_with_images
        ;;
    "images-only")
        fetch_images_only
        ;;
    "update-data")
        update_data
        ;;
    "help"|"--help"|"-h")
        show_usage
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac
