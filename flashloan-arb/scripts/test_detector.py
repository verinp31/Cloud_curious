#!/usr/bin/env python3
"""Lightweight self-checks for the opportunity math (no network)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bot.detector import evaluate_opportunity
from bot.prices import Quote


def test_profitable_spread() -> None:
    qa = Quote("WETH_USDC", "uni", 3200.0, 0.0)
    qb = Quote("WETH_USDC", "sushi", 3220.0, 0.0)
    opp = evaluate_opportunity(
        qa,
        qb,
        loan_usd=50_000,
        premium_bps=5,
        gas_usd=2.5,
        min_profit_usd=5,
    )
    assert opp is not None, "expected opportunity"
    assert opp.net_profit_usd > 5
    assert opp.buy_dex == "uni"
    assert opp.sell_dex == "sushi"


def test_unprofitable_after_fees() -> None:
    qa = Quote("WETH_USDC", "uni", 3200.0, 0.0)
    qb = Quote("WETH_USDC", "sushi", 3200.5, 0.0)
    opp = evaluate_opportunity(
        qa,
        qb,
        loan_usd=1_000,
        premium_bps=5,
        gas_usd=2.5,
        min_profit_usd=5,
    )
    assert opp is None, "tiny spread should be filtered"


if __name__ == "__main__":
    test_profitable_spread()
    test_unprofitable_after_fees()
    print("ok")
