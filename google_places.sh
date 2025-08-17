#!/usr/bin/env bash
set -euo pipefail
export PYTHONUNBUFFERED=1
python3 src/google_places_fetch.py
