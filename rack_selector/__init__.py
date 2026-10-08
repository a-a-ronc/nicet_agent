"""
rack_selector — OneRack-style seismic rack-selection triage tool for nicet_agent.

Given a site (ZIP or lat/long), a commodity/product, and a rack configuration, this
package:
  1. fetches ASCE 7-22 seismic design parameters (USGS web service),
  2. computes the seismic base-shear coefficient per ANSI/RMI MH16.1-2023 / ASCE 7-22,
  3. lays out beam elevations using the Intralog 6in / 12in clearance convention,
  4. recommends frames and beams from the dealer catalog (Interlake Mecalux > SpaceRAK
     > Hannibal/Nucor), and
  5. flags NFPA/IFC clearance and the human (PE/FPE) review requirement.

TRIAGE TOOL ONLY — not a stamped engineering deliverable. All output must be confirmed
against manufacturer load tables and reviewed by a licensed PE.
"""

from .seismic import compute_cs, seismic_weight, base_shear, sdc_requirements, SeismicResult
from .clearance import beam_layout, BeamLayout
from .selector import recommend, RackRecommendation

__all__ = [
    "compute_cs",
    "seismic_weight",
    "base_shear",
    "sdc_requirements",
    "SeismicResult",
    "beam_layout",
    "BeamLayout",
    "recommend",
    "RackRecommendation",
]

__version__ = "0.1.0"
