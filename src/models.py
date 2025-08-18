from __future__ import annotations
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import random, string

def _rand_id() -> str:
    alphabet = 'abcdefghijklmnopqrstuvwxyz0123456789'
    return 'farm_' + ''.join(random.choice(alphabet) for _ in range(10))

class Location(BaseModel):
    lat: Optional[float] = None
    lng: Optional[float] = None
    address: str = ''
    city: str = ''
    county: str = ''
    postcode: str = ''

class Contact(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None

class OpeningHour(BaseModel):
    day: str
    open: Optional[str] = None
    close: Optional[str] = None

class FarmShop(BaseModel):
    id: str = Field(default_factory=_rand_id, pattern=r'^farm_[a-z0-9]{10}$')
    name: str
    slug: str
    location: Location
    contact: Contact = Field(default_factory=Contact)
    offerings: List[str] = Field(default_factory=list)
    hours: List[OpeningHour] = Field(default_factory=list)
    description: Optional[str] = None  # Rich description of the farm shop
    images: List[str] = Field(default_factory=list)  # URLs to shop images
    verified: bool = False
    adsenseEligible: bool = True
    updatedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    # Additional Google Places data
    rating: Optional[float] = None  # Google rating (1-5)
    user_ratings_total: Optional[int] = None  # Number of reviews
    price_level: Optional[int] = None  # Price level (0-4)
    place_id: Optional[str] = None  # Google Places ID
    types: List[str] = Field(default_factory=list)  # Google Places types

    def key_name_postcode(self) -> str:
        pc = (self.location.postcode or '').replace(' ', '').upper()
        nm = ' '.join(self.name.lower().split())
        return f'{nm}::{pc}'
