"""Make the ``voluptuous`` package importable without an install.

Tries, in order: this workdir's ``voluptuous-src`` checkout and the
repo root layout (the layout the PR targets).
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_CANDIDATES = (
    os.path.join(_HERE, "..", "voluptuous-src"),
    os.path.join(_HERE, "..", ".."),
)
for _candidate in _CANDIDATES:
    if os.path.isdir(os.path.join(_candidate, "voluptuous")):
        sys.path.insert(0, os.path.normpath(_candidate))
