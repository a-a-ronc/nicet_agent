"""
ZIP / address -> latitude, longitude. Network helpers (stdlib only).

Primary: Zippopotam.us for US ZIP codes (no key). Fallback: US Census geocoder for a
full one-line address. Both are free public services. Not exercised by offline tests.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Optional

ZIPPOPOTAM = "https://api.zippopotam.us/us/"
CENSUS = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"


def zip_to_latlon(zip_code: str, timeout: float = 15.0) -> tuple[float, float, str]:
    """Return (lat, lon, place_label) for a 5-digit US ZIP via Zippopotam.us."""
    zip_code = str(zip_code).strip()[:5]
    url = ZIPPOPOTAM + urllib.parse.quote(zip_code)
    req = urllib.request.Request(url, headers={"User-Agent": "nicet_agent/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
        payload = json.loads(resp.read().decode("utf-8"))
    place = payload["places"][0]
    lat = float(place["latitude"])
    lon = float(place["longitude"])
    label = f"{place['place name']}, {place['state abbreviation']} {zip_code}"
    return lat, lon, label


def address_to_latlon(address: str, timeout: float = 20.0) -> tuple[float, float, str]:
    """Return (lat, lon, matched_address) for a one-line US address via Census geocoder."""
    params = {"address": address, "benchmark": "Public_AR_Current", "format": "json"}
    url = CENSUS + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "nicet_agent/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
        payload = json.loads(resp.read().decode("utf-8"))
    matches = payload.get("result", {}).get("addressMatches", [])
    if not matches:
        raise ValueError(f"No geocode match for address: {address!r}")
    m = matches[0]
    coords = m["coordinates"]
    return float(coords["y"]), float(coords["x"]), m.get("matchedAddress", address)


def resolve_location(zip_code: Optional[str] = None, address: Optional[str] = None,
                     lat: Optional[float] = None, lon: Optional[float] = None
                     ) -> tuple[float, float, str]:
    """Resolve a location from whichever input is provided (lat/long > zip > address)."""
    if lat is not None and lon is not None:
        return float(lat), float(lon), f"{lat:.4f}, {lon:.4f}"
    if zip_code:
        return zip_to_latlon(zip_code)
    if address:
        return address_to_latlon(address)
    raise ValueError("Provide lat/lon, a ZIP, or an address.")
