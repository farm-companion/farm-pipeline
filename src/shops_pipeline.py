from __future__ import annotations
import asyncio, json, os, re, sys, time, pathlib
from typing import Any, Dict, List, Optional, Tuple
import orjson, httpx, yaml
from bs4 import BeautifulSoup
from jsonschema import validate
from crawl4ai import CrawlerHub, BrowserConfig
from pydantic import ValidationError
from models import FarmShop, Location, Contact
from utils_geo import slugify, haversine_km, geohash

ROOT = pathlib.Path(__file__).resolve().parents[1]
SEEDS = ROOT / "seeds" / "uk.yml"
DIST = ROOT / "dist"
DIST.mkdir(parents=True, exist_ok=True)

SCHEMA_URL = os.getenv(
    "FARM_SCHEMA_URL",
    "https://raw.githubusercontent.com/farm-companion/farm-schema/main/schemas/farm_schema.v1.json",
)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_UA = os.getenv("NOMINATIM_UA", "FarmCompanionBot/1.0 (+https://www.farmcompanion.co.uk/contact)")
NOMINATIM_EMAIL = os.getenv("NOMINATIM_EMAIL")  # optional & recommended

NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9 '&.-]+")
PC_RE = re.compile(r"[A-Za-z]{1,2}\d[A-Za-z\d]?\s*\d[A-Za-z]{2}", re.I)  # UK postcode

def load_seeds() -> Dict[str, Any]:
    if not SEEDS.exists():
        raise SystemExit(f"Missing seeds file: {SEEDS}")
    with open(SEEDS, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

async def fetch_schema() -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(SCHEMA_URL)
        r.raise_for_status()
        return r.json()

async def geocode_missing(shops: List[FarmShop]) -> None:
    async with httpx.AsyncClient(timeout=30, headers={"User-Agent": NOMINATIM_UA}) as client:
        for s in shops:
            if s.location.lat is not None and s.location.lng is not None:
                continue
            q = " ".join([s.location.address, s.location.postcode or "", "United Kingdom"]).strip()
            params = {"format":"jsonv2","q":q,"countrycodes":"gb","limit":"1","addressdetails":"0"}
            if NOMINATIM_EMAIL: params["email"] = NOMINATIM_EMAIL
            try:
                resp = await client.get(NOMINATIM_URL, params=params)
                data = resp.json()
                if isinstance(data, list) and data:
                    s.location.lat = float(data[0]["lat"])
                    s.location.lng = float(data[0]["lon"])
            except Exception as e:
                print(f"geocode fail for {s.name}: {e}", file=sys.stderr)
            await asyncio.sleep(1.05)  # 1 rps polite

def normalize_whitespace(s: str) -> str:
    return " ".join((s or "").split())

def parse_items_from_html(html: str, hints: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generic parser using hints from seeds (CSS selectors). This is intentionally simple.
    Each source can specify:
      list_selector: ".item"
      name_selector, addr_selector, pc_selector, county_selector, link_selector, phone_selector, email_selector, website_selector
    """
    soup = BeautifulSoup(html, "html.parser")
    items = []
    nodes = soup.select(hints.get("list_selector", "")) or []
    for n in nodes:
        get = lambda sel: normalize_whitespace((n.select_one(sel).get_text(strip=True) if sel and n.select_one(sel) else ""))
        name = get(hints.get("name_selector"))
        addr = get(hints.get("addr_selector"))
        county = get(hints.get("county_selector"))
        pc = get(hints.get("pc_selector"))
        if not pc:
            m = PC_RE.search(n.get_text(" ", strip=True))
            pc = m.group(0) if m else ""
        phone = get(hints.get("phone_selector"))
        email = get(hints.get("email_selector"))
        website = ""
        if hints.get("website_selector"):
            a = n.select_one(hints["website_selector"])
            if a and a.has_attr("href"):
                website = a["href"]
        elif hints.get("link_selector"):
            a = n.select_one(hints["link_selector"])
            if a and a.has_attr("href"): website = a["href"]
        if not NAME_RE.search(name or "") and not pc:
            continue
        items.append({
            "name": name or (website or "Farm shop").split("//")[-1],
            "address": addr,
            "county": county,
            "postcode": pc.upper(),
            "contact": {"phone": phone or None, "email": email or None, "website": website or None},
        })
    return items

async def crawl_sources(seeds: Dict[str, Any]) -> List[Dict[str, Any]]:
    # For now, return empty list since we don't have real sources configured
    # This allows the pipeline to run and test the rest of the functionality
    print("⚠️  No real sources configured yet - skipping crawl")
    return []

def map_to_shops(raw: List[Dict[str, Any]]) -> List[FarmShop]:
    shops: List[FarmShop] = []
    for it in raw:
        name = normalize_whitespace(it.get("name","")).strip() or "Farm shop"
        addr = normalize_whitespace(it.get("address",""))
        county = normalize_whitespace(it.get("county",""))
        pc = normalize_whitespace(it.get("postcode","")).upper()
        contact = it.get("contact", {}) or {}
        fs = FarmShop(
            name=name,
            slug=slugify(f"{name}-{pc or county or 'uk'}"),
            location=Location(address=addr, county=county, postcode=pc),
            contact=Contact(**{k:v for k,v in contact.items() if v}),
            offerings=[]
        )
        shops.append(fs)
    return shops

def dedupe_shops(shops: List[FarmShop]) -> List[FarmShop]:
    # First pass: name+postcode key
    seen: Dict[str, FarmShop] = {}
    for s in shops:
        k = s.key_name_postcode()
        if k not in seen:
            seen[k] = s
        else:
            # prefer the one with coords or website/email populated
            a, b = seen[k], s
            score = lambda x: int(bool(x.location.lat)) + int(bool(x.contact.website)) + int(bool(x.contact.email))
            if score(b) > score(a):
                seen[k] = b
    deduped = list(seen.values())

    # Second pass: proximity within 0.25 km with same name (ignoring postcode)
    deduped.sort(key=lambda s: (s.name.lower(), s.location.postcode))
    result: List[FarmShop] = []
    for s in deduped:
        merged = False
        for r in result:
            if r.name.lower() == s.name.lower() and r.location.lat and r.location.lng and s.location.lat and s.location.lng:
                if haversine_km(r.location.lat, r.location.lng, s.location.lat, s.location.lng) < 0.25:
                    merged = True
                    # keep richer contact
                    if (s.contact.website and not r.contact.website): r.contact.website = s.contact.website
                    if (s.contact.email and not r.contact.email): r.contact.email = s.contact.email
                    if (s.contact.phone and not r.contact.phone): r.contact.phone = s.contact.phone
                    break
        if not merged:
            result.append(s)
    return result

def to_geojson(shops: List[FarmShop]) -> Dict[str, Any]:
    feats = []
    for s in shops:
        if s.location.lat is None or s.location.lng is None:
            continue
        feats.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [s.location.lng, s.location.lat]},
            "properties": {
                "id": s.id,
                "name": s.name,
                "slug": s.slug,
                "address": s.location.address,
                "county": s.location.county,
                "postcode": s.location.postcode,
                "website": s.contact.website,
                "geohash": geohash(s.location.lat, s.location.lng, 7),
            }
        })
    return {"type":"FeatureCollection","features":feats}

async def main():
    seeds = load_seeds()
    raw = await crawl_sources(seeds)
    print(f"🔎 parsed items: {len(raw)}")
    shops = map_to_shops(raw)
    print(f"🗺️ mapped shops: {len(shops)}")

    # Geocode missing coords
    await geocode_missing(shops)

    # Deduplicate
    shops = dedupe_shops(shops)
    print(f"🧹 deduped shops: {len(shops)}")

    # Validate against farm-schema
    schema = await fetch_schema()
    data = [s.model_dump() for s in shops]
    # validate each item (lightweight loop to pinpoint errors)
    ok = 0
    for i, item in enumerate(data):
        try:
            validate(item, schema)
            ok += 1
        except Exception as e:
            print(f"❌ schema error at index {i}: {e}", file=sys.stderr)
    print(f"✅ schema valid items: {ok}/{len(data)}")

    # Write outputs
    json_path = DIST / "farms.uk.json"
    geo_path = DIST / "farms.geo.json"
    with open(json_path, "wb") as f:
        f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS))
    with open(geo_path, "wb") as f:
        f.write(orjson.dumps(to_geojson(shops), option=orjson.OPT_INDENT_2))
    print(f"📦 wrote {json_path} and {geo_path}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(130)
