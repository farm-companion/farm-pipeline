"""
Minimal boot test for Crawl4AI in farm-pipeline.
- Loads seeds/uk.yml
- Spins up Crawl4AI once
- Just prints the number of seeds and exits
Next step will implement real crawling + extraction + mapping to your FarmShop schema.
"""
from __future__ import annotations
import sys, json, pathlib
from typing import List, Dict, Any

import yaml  # provided by crawl4ai
from crawl4ai import AsyncWebCrawler, BrowserConfig

ROOT = pathlib.Path(__file__).resolve().parents[1]
SEEDS_FILE = ROOT / "seeds" / "uk.yml"

def load_seeds() -> Dict[str, Any]:
    if not SEEDS_FILE.exists():
        raise SystemExit(f"Missing seeds file: {SEEDS_FILE}")
    with open(SEEDS_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

async def boot_test():
    seeds = load_seeds()
    sources: List[Dict[str, Any]] = seeds.get("sources", []) or []
    print(f"🧪 Seeds loaded: {len(sources)} item(s)")

    # Boot Crawl4AI (no navigation yet)
    try:
        async with AsyncWebCrawler() as crawler:
            print("✅ Crawl4AI boot OK (AsyncWebCrawler available)")
    except Exception as e:
        print(f"❌ Crawl4AI boot failed: {e}")
        return

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(boot_test())
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        sys.exit(130)
