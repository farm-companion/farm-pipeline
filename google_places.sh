#!/usr/bin/env bash
set -euo pipefail
export PYTHONUNBUFFERED=1

echo "🔍 Fetching farm shops with images from Google Places API..."
python3 src/google_places_fetch.py

echo "📁 Copying data to frontend..."
cp dist/farms.uk.json ../farm-frontend/public/data/farms.uk.json
cp dist/farms.geo.json ../farm-frontend/public/data/farms.geo.json

echo "✅ Farm shops data updated with images!"
echo "📊 Check the frontend to see the new images in action."
