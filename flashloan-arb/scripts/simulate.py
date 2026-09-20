#!/usr/bin/env python3
"""Run a single detection pass and print JSON opportunities."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bot.config import load_settings
from bot.detector import scan_pairs
from bot.prices import PriceFeed


def main() -> int:
    settings = load_settings()
    feed = PriceFeed(settings)
    opps = scan_pairs(settings, feed)
    payload = [o.as_dict() for o in opps]
    print(json.dumps({"mode": settings["mode"], "opportunities": payload}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
