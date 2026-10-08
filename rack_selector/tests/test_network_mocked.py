"""Network code paths (USGS + geocoders) exercised offline with a fake urlopen, plus
opt-in live smoke tests (set NICET_NETWORK=1)."""

import io
import json
import os
import urllib.parse

import pytest

from rack_selector import cli, geocode, seismic
from rack_selector.seismic import SeismicResult, compute_cs


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@pytest.fixture
def fake_urlopen(monkeypatch):
    """Route urlopen to canned payloads keyed by URL substring; record requested URLs."""
    calls, payloads = [], {}

    def _urlopen(req, timeout=None):
        url = req.full_url if hasattr(req, "full_url") else req
        calls.append(url)
        for key, payload in payloads.items():
            if key in url:
                if isinstance(payload, Exception):
                    raise payload
                return FakeResponse(json.dumps(payload).encode())
        raise AssertionError(f"unexpected URL {url}")

    monkeypatch.setattr("urllib.request.urlopen", _urlopen)
    return calls, payloads


USGS_OK = {"request": {"status": "success"},
           "response": {"data": {"sds": 1.0, "sd1": 0.6, "s1": 0.55, "sdc": "D", "ss": 1.5}}}


@pytest.mark.parametrize("ref, endpoint", [("ASCE7-16", "asce7-16.json"),
                                           ("ASCE7-22", "asce7-22.json")])
def test_fetch_seismic_endpoint_params_and_cs(fake_urlopen, ref, endpoint):
    calls, payloads = fake_urlopen
    payloads[endpoint] = USGS_OK
    res = seismic.fetch_seismic(40.8254, -111.9547, "III", "D", reference_document=ref)
    q = urllib.parse.parse_qs(urllib.parse.urlparse(calls[0]).query)
    assert endpoint in calls[0]
    assert q["latitude"] == ["40.8254"] and q["longitude"] == ["-111.9547"]
    assert q["riskCategory"] == ["III"] and q["siteClass"] == ["D"]
    assert res.sdc == "D" and res.cs_down_aisle == pytest.approx(1.0 / 6.0)
    assert ref in res.source


def test_fetch_seismic_error_status(fake_urlopen):
    _, payloads = fake_urlopen
    payloads["asce7-22.json"] = {"request": {"status": "error"}}
    with pytest.raises(RuntimeError):
        seismic.fetch_seismic(40.0, -111.0)


def test_fetch_seismic_rejects_unknown_edition():
    with pytest.raises(ValueError):
        seismic.fetch_seismic(40.0, -111.0, reference_document="ASCE7-10")


def test_zip_to_latlon(fake_urlopen):
    calls, payloads = fake_urlopen
    payloads["zippopotam"] = {"places": [{"latitude": "40.8254", "longitude": "-111.9547",
                                          "place name": "Salt Lake City",
                                          "state abbreviation": "UT"}]}
    lat, lon, label = geocode.zip_to_latlon("84116-1234")
    assert (lat, lon) == (40.8254, -111.9547)
    assert label == "Salt Lake City, UT 84116" and calls[0].endswith("/84116")


def test_address_to_latlon_match_and_no_match(fake_urlopen):
    _, payloads = fake_urlopen
    payloads["geocoding.geo.census.gov"] = {"result": {"addressMatches": [
        {"coordinates": {"x": -111.95, "y": 40.82}, "matchedAddress": "2335 W 2950 N, SLC"}]}}
    assert geocode.address_to_latlon("2335 W 2950 N, SLC UT") == (40.82, -111.95,
                                                                  "2335 W 2950 N, SLC")
    payloads["geocoding.geo.census.gov"] = {"result": {"addressMatches": []}}
    with pytest.raises(ValueError):
        geocode.address_to_latlon("nowhere")


def test_resolve_location_precedence(fake_urlopen):
    calls, payloads = fake_urlopen
    assert geocode.resolve_location(zip_code="84116", lat=1.0, lon=2.0)[:2] == (1.0, 2.0)
    assert calls == []                                        # lat/lon never hits network
    payloads["zippopotam"] = {"places": [{"latitude": "3", "longitude": "4", "place name": "X",
                                          "state abbreviation": "UT"}]}
    assert geocode.resolve_location(zip_code="84116")[:2] == (3.0, 4.0)
    with pytest.raises(ValueError):
        geocode.resolve_location()


def _fake_result(*a, **k):
    r = SeismicResult(40.8, -111.9, "II", "Default", 1.0, 0.6, 0.55, "D")
    r.cs_down_aisle, r.cs_cross_aisle = compute_cs(1.0, 0.6, 0.55, 6), compute_cs(1.0, 0.6, 0.55, 4)
    return r


def test_cli_online_path_passes_code_edition(monkeypatch, capsys):
    seen = {}

    def fake_fetch(lat, lon, **kw):
        seen.update(kw)
        return _fake_result()

    monkeypatch.setattr(cli, "fetch_seismic", fake_fetch)
    base = ["--lat", "40.8", "--lon", "-111.9", "--pallet-weight", "2000",
            "--pallet-height", "48", "--beam-length", "96", "--levels", "3"]
    assert cli.main(base) == 0
    assert seen["reference_document"] == "ASCE7-22"
    assert cli.main(base + ["--code-edition", "asce7-16"]) == 0
    assert seen["reference_document"] == "ASCE7-16"
    assert "RACK SELECTOR" in capsys.readouterr().out


def test_cli_network_failure_returns_2(monkeypatch, capsys):
    def boom(*a, **k):
        raise OSError("Tunnel connection failed: 403")

    monkeypatch.setattr(cli, "fetch_seismic", boom)
    rc = cli.main(["--lat", "40.8", "--lon", "-111.9", "--pallet-weight", "2000",
                   "--pallet-height", "48", "--beam-length", "96", "--levels", "3"])
    assert rc == 2
    assert "--offline" in capsys.readouterr().err


# --- live smoke tests (opt-in) ----------------------------------------------------------
live = pytest.mark.skipif(os.environ.get("NICET_NETWORK") != "1",
                          reason="live network test; set NICET_NETWORK=1")


@pytest.mark.network
@live
@pytest.mark.parametrize("ref", ["ASCE7-16", "ASCE7-22"])
def test_live_usgs_salt_lake_city(ref):
    res = seismic.fetch_seismic(40.8254, -111.9547, "II", "Default", reference_document=ref)
    assert res.sdc in {"D", "E", "F"} and res.sds > 0.5


@pytest.mark.network
@live
def test_live_zip_geocode():
    lat, lon, _ = geocode.zip_to_latlon("84116")
    assert 40 < lat < 42 and -113 < lon < -111
