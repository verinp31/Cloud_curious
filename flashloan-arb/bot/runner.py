"""Continuous loop: detect → filter → dry-run execute."""

from __future__ import annotations

import logging
import signal
import sys
import time

from .config import load_settings
from .detector import scan_pairs
from .executor import Executor
from .prices import PriceFeed

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("arb.runner")

_running = True


def _stop(*_args) -> None:
    global _running
    _running = False
    log.info("Arrêt demandé — fin de boucle…")


def main() -> int:
    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    settings = load_settings()
    feed = PriceFeed(settings)
    executor = Executor(settings)

    log.info(
        "Démarrage bot éducatif mode=%s poll=%.1fs min_profit=$%.2f",
        settings["mode"],
        settings["poll_seconds"],
        settings["min_profit_usd"],
    )
    log.info(
        "Rappel: ce bot ne génère pas de profits garantis. "
        "Dry-run uniquement sauf configuration explicite."
    )

    cycles = 0
    found = 0
    while _running:
        cycles += 1
        try:
            opps = scan_pairs(settings, feed)
            if not opps:
                log.info("cycle=%s aucune opportunité nette", cycles)
            for opp in opps:
                found += 1
                log.info(
                    "OPPORTUNITÉ %s net=$%.2f gross=$%.2f loan=$%.0f | %s",
                    opp.pair,
                    opp.net_profit_usd,
                    opp.gross_profit_usd,
                    opp.loan_usd,
                    opp.direction,
                )
                executor.execute(opp)
        except Exception:
            log.exception("Erreur pendant le cycle %s", cycles)

        # Sleep in small slices so SIGINT stops quickly.
        remaining = float(settings["poll_seconds"])
        while _running and remaining > 0:
            step = min(0.25, remaining)
            time.sleep(step)
            remaining -= step

    log.info("Terminé. cycles=%s opportunités_loggées=%s", cycles, found)
    return 0


if __name__ == "__main__":
    sys.exit(main())
