from __future__ import annotations
import math, pygeohash as pgh
from slugify import slugify as _slugify

def slugify(s: str) -> str:
    return _slugify(s or '', lowercase=True)

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0088
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))

def geohash(lat: float, lng: float, precision: int = 7) -> str:
    return pgh.encode(lat, lng, precision=precision)
