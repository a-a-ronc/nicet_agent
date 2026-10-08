"""CLI behaviour: JSON outputs, error exits, and true end-to-end runs in a subprocess
(`python -m ...`) the way a user runs them — including Windows-safe output encoding."""

import json
import os
import subprocess
import sys

import pytest

from rack_selector import cli, fire_check, levels

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NB = os.path.join(ROOT, "projects", "25-1642_new_balance_slc.json")
OFFLINE = ["--offline", "--sds", "0.95", "--sd1", "0.42", "--s1", "0.40", "--sdc", "D"]


# --- JSON outputs ---------------------------------------------------------------------------
def test_fire_check_json(capsys):
    assert fire_check.main(["--project", NB, "--deck-open", "60", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["in_rack_status"] == "LIKELY"
    assert data["editions"]["nfpa13"] == "2019"


def test_levels_json(capsys):
    assert levels.main(["--load-height", "31.5", "--beams", "3.5,5", "--max-top-beam-ft",
                        "26.5", "--json"]) == 0
    rows = json.loads(capsys.readouterr().out)
    assert len(rows) == 4 and {r["beam_height_in"] for r in rows} == {3.5, 5.0}


def test_rack_selector_json(capsys):
    assert cli.main(["--project", NB, *OFFLINE, "--levels", "6", "--shelf-load", "1800",
                     "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["recommended_beam"]["dealer"] == "Interlake Mecalux"
    assert data["layout"]["num_beam_levels"] == 6
    assert data["seismic"]["SDC"] == "D"


# --- error exits -------------------------------------------------------------------------------
def test_fire_check_missing_inputs_exits():
    with pytest.raises(SystemExit):
        fire_check.main(["--commodity", "Class IV"])


def test_fire_check_bad_commodity_returns_2(capsys):
    rc = fire_check.main(["--commodity", "shoes", "--storage-height", "20",
                          "--ceiling-height", "30", "--aisle", "6"])
    assert rc == 2 and "Unrecognized commodity" in capsys.readouterr().err


@pytest.mark.parametrize("argv", [
    ["--beams", "5", "--max-top-beam-ft", "20"],                 # no load height
    ["--load-height", "31.5", "--beams", "5"],                   # no height limit
])
def test_levels_error_exits(argv):
    assert levels.main(argv) == 2


def test_rack_selector_missing_inputs_returns_2(capsys):
    assert cli.main(["--lat", "40", "--lon", "-111", *OFFLINE]) == 2
    assert "missing" in capsys.readouterr().err


def test_rack_selector_offline_requires_values():
    with pytest.raises(SystemExit):
        cli.main(["--lat", "40", "--lon", "-111", "--offline", "--pallet-weight", "1000",
                  "--pallet-height", "48", "--beam-length", "96", "--levels", "2"])


# --- subprocess end-to-end ---------------------------------------------------------------
def _run(*args, encoding="utf-8", env_extra=None):
    env = dict(os.environ)
    env.pop("PYTHONIOENCODING", None)
    env.update(env_extra or {})
    return subprocess.run([sys.executable, "-m", *args], cwd=ROOT, capture_output=True,
                          env=env, timeout=120)


@pytest.mark.parametrize("args, expect", [
    (("rack_selector.ask", "ESFR clearance to top of storage"), b"nfpa13.md"),
    (("rack_selector.fire_check", "--project", NB), b"IN-RACK:"),
    (("rack_selector.levels", "--project", NB, "--hole-pitch", "2"), b"LEVEL FIT"),
    (("rack_selector", "--project", NB, *OFFLINE, "--levels", "6", "--shelf-load", "1800"),
     b"RACK SELECTOR"),
])
def test_module_runs_end_to_end(args, expect):
    r = _run(*args)
    assert r.returncode == 0, r.stderr.decode(errors="replace")
    assert expect in r.stdout


def test_output_survives_a_cp1252_console():
    """Piped output on Windows uses cp1252; KB text with → ≥ ² must not crash."""
    r = _run("rack_selector.ask", "open rack definition 50 percent open wire deck",
             env_extra={"PYTHONIOENCODING": "cp1252"})
    assert r.returncode == 0, r.stderr.decode(errors="replace")
    assert b"nfpa13.md" in r.stdout
