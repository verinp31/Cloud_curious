"""Shared config loading for the flashloan arb demo."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "settings.yaml"


def load_settings(path: Path | None = None) -> dict[str, Any]:
    cfg_path = path or DEFAULT_CONFIG
    with cfg_path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}

    mode = os.getenv("ARB_MODE", data.get("mode", "simulate")).lower()
    data["mode"] = mode
    data["poll_seconds"] = float(os.getenv("POLL_SECONDS", data.get("poll_seconds", 3)))
    data["min_profit_usd"] = float(os.getenv("MIN_PROFIT_USD", data.get("min_profit_usd", 5)))
    data["rpc_url"] = os.getenv("RPC_URL", "")
    data["private_key"] = os.getenv("PRIVATE_KEY", "")
    data["allow_live"] = os.getenv("ALLOW_LIVE_TRADING", "").lower() in {"1", "true", "yes"}
    return data
