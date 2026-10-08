"""Console safety for the CLIs.

On Windows, piped or redirected output uses the locale code page (often cp1252), which
cannot encode characters that appear in the KB (→, ≥, ², §). Instead of crashing with
UnicodeEncodeError, replace anything the stream can't encode.
"""

import sys


def safe_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):  # non-reconfigurable stream (e.g. pytest capture)
            pass
