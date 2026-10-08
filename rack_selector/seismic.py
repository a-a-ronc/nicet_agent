"""
Seismic parameters and base-shear per ASCE 7-16 / 7-22 and ANSI-RMI MH16.1 (steel storage
racks). Pure-math functions are kept separate from the network fetch so they can be
unit-tested without internet.

References:
  - ASCE/SEI 7 §11.4 (design parameters), §11.6 (SDC), §12.8 (seismic response coefficient)
  - ASCE/SEI 7-16 §11.4.3/11.4.4 (default Site Class D -> Fa >= 1.2),
    §11.4.8 Exception 2 (Site Class D, S1 >= 0.2: no site-specific study when Cs uses
    Eq. 12.8-2 for T <= 1.5Ts)
  - ANSI/RMI MH16.1 (rack seismic; R, Ip, product reduction factor)
  - USGS building-codes web services:
      https://earthquake.usgs.gov/ws/building-codes/asce7-16/calculate
      https://earthquake.usgs.gov/ws/building-codes/asce7-22/calculate
    (the older /ws/designmaps/asce7-XX.json URLs redirect here)

CAUTION: Cs here uses the short-period (governing-upper) value floored by the code
minimum. The period-based reduction (T, which lowers Cs) is intentionally NOT applied,
so the result is conservative for triage. A licensed PE must run the full analysis.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Optional

USGS_ASCE7_22 = "https://earthquake.usgs.gov/ws/building-codes/asce7-22/calculate"
USGS_ASCE7_16 = "https://earthquake.usgs.gov/ws/building-codes/asce7-16/calculate"

# Map a reference-document key to its USGS endpoint. ASCE 7-16 is what IBC 2018/2021
# (and therefore current Utah/SLC permits) reference; ASCE 7-22 is IBC 2024.
_ENDPOINTS = {"ASCE7-22": USGS_ASCE7_22, "ASCE7-16": USGS_ASCE7_16}

# Site classes each USGS service accepts. ASCE 7-16 has no "Default" class: §11.4.3 says
# use Site Class D when soil properties are unknown (with the §11.4.4 Fa >= 1.2 floor).
# Site Class F always needs a site-specific study, so it is not offered.
SITE_CLASSES = {
    "ASCE7-16": {"A", "B", "C", "D", "E"},
    "ASCE7-22": {"DEFAULT", "A", "B", "BC", "C", "CD", "D", "DE", "E"},
}
DEFAULT_SITE_CLASS_FA_MIN = 1.2  # ASCE 7-16 §11.4.4


def _ref_key(reference_document: str) -> str:
    key = (reference_document or "").upper().replace(" ", "").replace("/", "")
    if key not in _ENDPOINTS:
        raise ValueError(f"Unsupported reference document {reference_document!r}; "
                         f"use one of {sorted(_ENDPOINTS)}")
    return key


def endpoint_for(reference_document: str) -> str:
    """Return the USGS endpoint for a reference document ('ASCE7-22' or 'ASCE7-16')."""
    return _ENDPOINTS[_ref_key(reference_document)]


def resolve_site_class(site_class: Optional[str], reference_document: str) -> tuple[str, bool]:
    """
    Return (site class to send to USGS, used_default_D).

    ASCE 7-22 accepts 'Default'. ASCE 7-16 does not: an unknown/default site becomes
    Site Class D per §11.4.3, and the caller must then apply the §11.4.4 Fa >= 1.2 floor.
    """
    ref = _ref_key(reference_document)
    sc = (site_class or "Default").strip().upper()
    if ref == "ASCE7-16" and sc == "DEFAULT":
        return "D", True
    if sc not in SITE_CLASSES[ref]:
        allowed = ", ".join(sorted(SITE_CLASSES[ref]))
        raise ValueError(f"Site Class {site_class!r} is not valid for {ref}. Use one of: "
                         f"{allowed}" + (" (or Default)" if ref == "ASCE7-16" else "") +
                         ". Site Class F requires a site-specific study.")
    return ("Default" if sc == "DEFAULT" else sc), False


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
    sd1: Optional[float]  # None when USGS defers to a site-specific study (7-16 §11.4.8)
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


def compute_cs(sds: float, sd1: Optional[float], s1: float, r: float, ie: float = 1.0,
               t: Optional[float] = None, tl: float = 8.0) -> float:
    """
    Seismic response coefficient Cs per ASCE 7 §12.8.1.1.

    sds, sd1, s1 : design spectral accelerations (g); sd1 may be None (only needed for T)
    r            : response modification factor
    ie           : importance factor (Ip for racks; 1.0 typ., 1.5 if open to public)
    t            : fundamental period (s); if None, the period cap is not applied
                   (conservative — returns the short-period value, Eq. 12.8-2)
    tl           : long-period transition (s)
    """
    if r <= 0:
        raise ValueError("R must be > 0")
    if ie <= 0:
        raise ValueError("Ie must be > 0")

    cs = sds / (r / ie)  # Eq. 12.8-2 (short-period / governing upper value)

    # Period-based cap (Eq. 12.8-3 / 12.8-4) — only if a period is supplied.
    if t is not None and t > 0:
        if sd1 is None:
            raise ValueError("SD1 is required for a period-based Cs; it is unavailable "
                             "(ASCE 7-16 §11.4.8) — use the short-period Cs or a "
                             "site-specific study.")
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


# --- Seismic Design Category (ASCE 7 §11.6) --------------------------------------------
_SDC_ORDER = "ABCDEF"


def sdc_from_sds(sds: float, risk_category: str = "II") -> str:
    """ASCE 7 Table 11.6-1."""
    iv = risk_category.upper() == "IV"
    if sds < 0.167:
        return "A"
    if sds < 0.33:
        return "C" if iv else "B"
    if sds < 0.50:
        return "D" if iv else "C"
    return "D"


def sdc_from_sd1(sd1: float, risk_category: str = "II") -> str:
    """ASCE 7 Table 11.6-2."""
    iv = risk_category.upper() == "IV"
    if sd1 < 0.067:
        return "A"
    if sd1 < 0.133:
        return "C" if iv else "B"
    if sd1 < 0.20:
        return "D" if iv else "C"
    return "D"


def determine_sdc(sds: float, sd1: Optional[float], s1: float,
                  risk_category: str = "II") -> str:
    """Most severe of Tables 11.6-1 / 11.6-2; S1 >= 0.75 -> E (RC I-III) or F (RC IV)."""
    cands = [sdc_from_sds(sds, risk_category)]
    if sd1 is not None:
        cands.append(sdc_from_sd1(sd1, risk_category))
    if s1 >= 0.75:
        cands.append("F" if risk_category.upper() == "IV" else "E")
    return max(cands, key=_SDC_ORDER.index)


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
    Query the USGS building-codes web service and return a SeismicResult with Cs computed
    for both rack axes. Network call (mocked in the offline tests).

    reference_document: 'ASCE7-22' (IBC 2024) or 'ASCE7-16' (IBC 2018/2021 — current
    Utah/SLC permits). For ASCE 7-16 a 'Default' site class is sent as Site Class D and the
    §11.4.4 Fa >= 1.2 floor is applied to the returned values.
    """
    ref = _ref_key(reference_document)
    usgs_site_class, default_d = resolve_site_class(site_class, ref)
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "riskCategory": risk_category,
        "siteClass": usgs_site_class,
        "title": title,
    }
    url = endpoint_for(ref) + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "nicet_agent/0.2"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (trusted gov host)
        payload = json.loads(resp.read().decode("utf-8"))

    status = payload.get("request", {}).get("status")
    if status != "success":
        detail = payload.get("response")
        detail = detail if isinstance(detail, str) else ""
        raise RuntimeError(f"USGS {ref} request failed: {status}"
                           + (f" — {detail}" if detail else ""))
    data = payload["response"]["data"]
    res = seismic_result_from_usgs(data, latitude, longitude, risk_category,
                                   site_class or "Default", r_down, r_cross, ie,
                                   reference_document=ref, default_site_class=default_d)
    res.source = f"USGS {ref} web service"
    return res


def _num(v) -> Optional[float]:
    return None if v is None else float(v)


def seismic_result_from_usgs(data: dict, latitude: float, longitude: float,
                             risk_category: str, site_class: str,
                             r_down: float = R_DOWN_AISLE,
                             r_cross: float = R_CROSS_AISLE,
                             ie: float = 1.0, reference_document: str = "ASCE7-22",
                             default_site_class: bool = False) -> SeismicResult:
    """
    Build a SeismicResult from a parsed USGS 'data' object (testable, no network).

    Handles the ASCE 7-16 cases that USGS leaves to the engineer:
      * default Site Class D -> enforce Fa >= 1.2 (§11.4.4) and recompute SMS/SDS;
      * SD1 / Fv / SDC returned as null (§11.4.8, Site Class D with S1 >= 0.2) -> keep SD1
        as None, derive the SDC from SDS (Table 11.6-1) and S1, and note Exception 2.
    """
    ref = _ref_key(reference_document)
    notes: list = []
    sds, sd1 = _num(data.get("sds")), _num(data.get("sd1"))
    s1, ss = _num(data.get("s1")), _num(data.get("ss"))
    if sds is None or s1 is None:
        raise RuntimeError("USGS response is missing SDS or S1 — cannot compute Cs.")
    sdc = data.get("sdc")
    recompute_sdc = sdc is None

    if ref == "ASCE7-16" and default_site_class and ss is not None:
        fa = _num(data.get("fa"))
        if fa is None or fa < DEFAULT_SITE_CLASS_FA_MIN:
            new_sds = 2.0 / 3.0 * DEFAULT_SITE_CLASS_FA_MIN * ss
            if new_sds > sds:
                notes.append(
                    f"ASCE 7-16 §11.4.4: Site Class D used as the DEFAULT (no soils report) "
                    f"-> Fa >= 1.2 applied (USGS Fa for Site Class D = {fa}). SDS raised from "
                    f"{sds:.3f} g to {new_sds:.3f} g. A geotechnical report establishing the "
                    f"actual site class removes this floor.")
                sds = new_sds
                recompute_sdc = True
        else:
            notes.append("ASCE 7-16 §11.4.4: default Site Class D, Fa >= 1.2 already satisfied.")

    if sd1 is None:
        notes.append(
            "SD1 not provided by USGS (ASCE 7-16 §11.4.8: Site Class D with S1 >= 0.2 calls for "
            "a site-specific ground-motion study). Exception 2 waives it when Cs uses "
            "Eq. 12.8-2 for T <= 1.5Ts (as this tool does) and 1.5 x Eq. 12.8-3 above that — "
            "PE to confirm. SDC taken from SDS and S1.")

    if recompute_sdc:
        derived = determine_sdc(sds, sd1, s1, risk_category)
        usgs_sdc = sdc or data.get("sdcs")
        sdc = (max([derived, usgs_sdc], key=_SDC_ORDER.index)
               if usgs_sdc in tuple(_SDC_ORDER) else derived)

    res = SeismicResult(
        latitude=latitude, longitude=longitude, risk_category=risk_category,
        site_class=("D (default)" if default_site_class else site_class),
        sds=sds, sd1=sd1, s1=s1, sdc=str(sdc), ss=ss, ie=ie, notes=notes,
    )
    res.cs_down_aisle = compute_cs(sds, sd1, s1, r_down, ie)
    res.cs_cross_aisle = compute_cs(sds, sd1, s1, r_cross, ie)
    res.notes.append(
        f"Cs computed at short-period value (conservative; period reduction not applied). "
        f"R down-aisle={r_down}, R cross-aisle={r_cross}, Ie/Ip={ie}."
    )
    return res
