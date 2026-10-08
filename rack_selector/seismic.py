"""
Seismic parameters and base-shear per ASCE 7-22 / ANSI-RMI MH16.1-2023 (steel storage
racks). Pure-math functions are kept separate from the network fetch so they can be
unit-tested without internet.

References:
  - ASCE/SEI 7-22 §11.4 (design parameters), §12.8 (seismic response coefficient Cs)
  - ANSI/RMI MH16.1-2023 (rack seismic; R, Ip, product reduction factor)
  - USGS ASCE7-22 web service: https://earthquake.usgs.gov/ws/designmaps/asce7-22.html

CAUTION: Cs here uses the short-period (governing-upper) value floored by the code
minimum. The period-based reduction (T, which lowers Cs) is intentionally NOT applied,
so the result is conservative for triage. A licensed PE must run the full analysis.
"""

from __future__ import annotations

import json
import math
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Optional

USGS_ASCE7_22 = "https://earthquake.usgs.gov/ws/designmaps/asce7-22.json"
USGS_ASCE7_16 = "https://earthquake.usgs.gov/ws/designmaps/asce7-16.json"

# Map a reference-document key to its USGS endpoint. ASCE 7-16 is what IBC 2018/2021
# (and therefore current Utah/SLC permits) reference; ASCE 7-22 is IBC 2024.
_ENDPOINTS = {"ASCE7-22": USGS_ASCE7_22, "ASCE7-16": USGS_ASCE7_16}


def endpoint_for(reference_document: str) -> str:
    """Return the USGS endpoint for a reference document ('ASCE7-22' or 'ASCE7-16')."""
    key = (reference_document or "").upper().replace(" ", "").replace("/", "")
    if key not in _ENDPOINTS:
        raise ValueError(f"Unsupported reference document {reference_document!r}; "
                         f"use one of {sorted(_ENDPOINTS)}")
    return _ENDPOINTS[key]

# RMI / ASCE 7 default response-modification factors for steel storage racks.
R_DOWN_AISLE = 6.0   # down-aisle: typ. steel ordinary moment frame
R_CROSS_AISLE = 4.0  # cross-aisle: typ. steel ordinary concentrically braced frame
DEFAULT_PRF = 0.67   # product reduction factor (fraction of product weight as seismic mass)


@dataclass
class SeismicResult:
    """Seismic design parameters and computed rack base-shear coefficients."""
    latitude: float
    longitude: float
    risk_category: str
    site_class: str
    sds: float
    sd1: float
    s1: float
    sdc: str
    ss: Optional[float] = None
    ie: float = 1.0
    cs_down_aisle: Optional[float] = None
    cs_cross_aisle: Optional[float] = None
    source: str = "USGS ASCE7-22 web service"
    notes: list = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "risk_category": self.risk_category,
            "site_class": self.site_class,
            "SDS": self.sds,
            "SD1": self.sd1,
            "S1": self.s1,
            "SS": self.ss,
            "SDC": self.sdc,
            "Ie/Ip": self.ie,
            "Cs_down_aisle": self.cs_down_aisle,
            "Cs_cross_aisle": self.cs_cross_aisle,
            "source": self.source,
            "notes": self.notes,
        }


def compute_cs(sds: float, sd1: float, s1: float, r: float, ie: float = 1.0,
               t: Optional[float] = None, tl: float = 8.0) -> float:
    """
    Seismic response coefficient Cs per ASCE 7-22 §12.8.1.1.

    sds, sd1, s1 : design spectral accelerations (g)
    r            : response modification factor
    ie           : importance factor (Ip for racks; 1.0 typ., 1.5 if open to public)
    t            : fundamental period (s); if None, the period cap is not applied
                   (conservative — returns the short-period value)
    tl           : long-period transition (s)
    """
    if r <= 0:
        raise ValueError("R must be > 0")
    if ie <= 0:
        raise ValueError("Ie must be > 0")

    cs = sds / (r / ie)  # Eq. 12.8-2 (short-period / governing upper value)

    # Period-based cap (Eq. 12.8-3 / 12.8-4) — only if a period is supplied.
    if t is not None and t > 0:
        if t <= tl:
            cs_cap = sd1 / (t * (r / ie))
        else:
            cs_cap = (sd1 * tl) / (t * t * (r / ie))
        cs = min(cs, cs_cap)

    # Minimum (Eq. 12.8-5 and, for high S1, Eq. 12.8-6).
    cs_min = max(0.044 * sds * ie, 0.01)
    if s1 >= 0.6:
        cs_min = max(cs_min, 0.5 * s1 / (r / ie))

    return max(cs, cs_min)


def seismic_weight(dead_load_lb: float, product_load_lb: float,
                   prf: float = DEFAULT_PRF) -> float:
    """
    Effective seismic weight Ws = dead load + PRF x product load (ANSI/RMI MH16.1).
    PRF (product reduction factor) defaults to 0.67.
    """
    if not 0 < prf <= 1.0:
        raise ValueError("PRF must be in (0, 1]")
    return dead_load_lb + prf * product_load_lb


def base_shear(cs: float, ws_lb: float) -> float:
    """Seismic base shear V = Cs x Ws (lb). Ie/Ip is already inside Cs."""
    return cs * ws_lb


def sdc_requirements(sdc: str) -> list[str]:
    """Plain-language design implications that follow from the Seismic Design Category."""
    sdc = (sdc or "").upper().strip()
    base = [
        "Confirm frame/beam adequacy against the manufacturer's SEISMIC load tables at "
        "the computed Cs (gravity tables alone are not sufficient in seismic regions).",
    ]
    if sdc in ("A", "B"):
        return ["Low seismic. Standard anchorage; minimal special detailing."] + base
    if sdc == "C":
        return [
            "Moderate seismic. Base plates + anchors required; check overturning.",
        ] + base
    if sdc == "D":
        return [
            "High seismic (typical CA/UT/WA). Base-plate & ANCHOR design with seismic "
            "OVERSTRENGTH (Omega-0) required per MH16.1-2023; verify slab/anchor capacity.",
            "Consider base-fixity and frame-bracing test values (MH16.1-2023 additions).",
            "Special inspection of anchors typically required.",
        ] + base
    if sdc in ("E", "F"):
        return [
            "Very high seismic (near major faults). Overstrength anchorage mandatory; "
            "height/configuration may be restricted. Engage the PE early.",
            "Special inspection and possibly site-specific ground motion required.",
        ] + base
    return ["Seismic Design Category unknown — establish before proceeding."] + base


def fetch_seismic(latitude: float, longitude: float, risk_category: str = "II",
                  site_class: str = "Default", title: str = "nicet_agent",
                  timeout: float = 20.0,
                  r_down: float = R_DOWN_AISLE, r_cross: float = R_CROSS_AISLE,
                  ie: float = 1.0, reference_document: str = "ASCE7-22") -> SeismicResult:
    """
    Query the USGS design-maps web service and return a SeismicResult with Cs computed for
    both rack axes. Network call — not exercised by the offline unit tests.

    reference_document: 'ASCE7-22' (IBC 2024) or 'ASCE7-16' (IBC 2018/2021 — current
    Utah/SLC permits). The Cs equations (ASCE 7 §12.8) are identical between editions; the
    site parameters returned by USGS differ.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "riskCategory": risk_category,
        "siteClass": site_class,
        "title": title,
    }
    url = endpoint_for(reference_document) + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "nicet_agent/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (trusted gov host)
        payload = json.loads(resp.read().decode("utf-8"))

    if payload.get("request", {}).get("status") != "success":
        raise RuntimeError(f"USGS request failed: {payload.get('request', {}).get('status')}")
    data = payload["response"]["data"]
    res = seismic_result_from_usgs(data, latitude, longitude, risk_category,
                                   site_class, r_down, r_cross, ie)
    res.source = f"USGS {reference_document} web service"
    return res


def seismic_result_from_usgs(data: dict, latitude: float, longitude: float,
                             risk_category: str, site_class: str,
                             r_down: float = R_DOWN_AISLE,
                             r_cross: float = R_CROSS_AISLE,
                             ie: float = 1.0) -> SeismicResult:
    """Build a SeismicResult from a parsed USGS 'data' object (testable, no network)."""
    sds = float(data["sds"])
    sd1 = float(data["sd1"])
    s1 = float(data["s1"])
    sdc = str(data["sdc"])
    ss = float(data.get("ss")) if data.get("ss") is not None else None

    res = SeismicResult(
        latitude=latitude, longitude=longitude, risk_category=risk_category,
        site_class=site_class, sds=sds, sd1=sd1, s1=s1, sdc=sdc, ss=ss, ie=ie,
    )
    res.cs_down_aisle = compute_cs(sds, sd1, s1, r_down, ie)
    res.cs_cross_aisle = compute_cs(sds, sd1, s1, r_cross, ie)
    res.notes.append(
        f"Cs computed at short-period value (conservative; period reduction not applied). "
        f"R down-aisle={r_down}, R cross-aisle={r_cross}, Ie/Ip={ie}."
    )
    return res

# Reference editions: ASCE 7-22 (IBC 2024) and ASCE 7-16 (IBC 2018/2021, Utah/SLC).
