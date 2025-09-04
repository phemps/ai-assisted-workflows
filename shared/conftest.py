#!/usr/bin/env python3
"""Global pytest configuration for the shared package.

Ensures the `shared` package root is on `sys.path` so absolute imports like
`from core...` and `from setup...` work from any test location.
"""

import sys
from pathlib import Path

_shared_dir = Path(__file__).resolve().parent
if str(_shared_dir) not in sys.path:
    sys.path.insert(0, str(_shared_dir))
