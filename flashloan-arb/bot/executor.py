"""Execution layer: dry-run by default; live path intentionally gated."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .detector import Opportunity

log = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"


class Executor:
    def __init__(self, settings: dict[str, Any]) -> None:
        self.settings = settings
        self.mode = settings.get("mode", "simulate")
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.ledger = LOG_DIR / "opportunities.jsonl"

    def execute(self, opp: Opportunity) -> dict[str, Any]:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "mode": self.mode,
            "status": "dry_run",
            "opportunity": opp.as_dict(),
        }

        if self.mode in {"simulate", "scan"}:
            log.info(
                "DRY-RUN %s net=$%.2f via %s",
                opp.pair,
                opp.net_profit_usd,
                opp.direction,
            )
            self._append(record)
            return record

        if self.mode == "live":
            if not self.settings.get("allow_live"):
                record["status"] = "blocked_live"
                record["reason"] = (
                    "ARB_MODE=live requires ALLOW_LIVE_TRADING=true "
                    "(and a funded key + deployed contract)."
                )
                log.warning(record["reason"])
                self._append(record)
                return record

            # Intentionally not implemented: sending a real flashloan tx needs
            # a deployed contract, correct calldata, and careful risk controls.
            record["status"] = "not_implemented"
            record["reason"] = (
                "Live flashloan submission is left as an exercise — "
                "wire contracts/FlashloanArbitrage.sol + router calldata first."
            )
            log.error(record["reason"])
            self._append(record)
            return record

        record["status"] = "unknown_mode"
        self._append(record)
        return record

    def _append(self, record: dict[str, Any]) -> None:
        with self.ledger.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
