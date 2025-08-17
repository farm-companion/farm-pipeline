#!/usr/bin/env bash
set -euo pipefail
export PYTHONUNBUFFERED=1

echo "🖼️  Fetching images for existing farm shops..."
python3 fetch_images_only.py

echo "📁 Images have been added to the farm data!"
echo "🌐 Check the frontend to see the new images in action."
