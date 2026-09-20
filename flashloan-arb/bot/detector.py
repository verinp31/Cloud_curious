"""Detect net-positive triangular/two-leg DEX arbitrage after fees + gas."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .prices import Quote


@dataclass(frozen=True)
class Opportunity:
    pair: str
    buy_dex: str
    sell_dex: str
    buy_price: float
    sell_price: float
    loan_usd: float
    gross_profit_usd: float
    premium_usd: float
    gas_usd: float
    net_profit_usd: float
    direction: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "pair": self.pair,
            "buy_dex": self.buy_dex,
            "sell_dex": self.sell_dex,
            "buy_price": round(self.buy_price, 6),
            "sell_price": round(self.sell_price, 6),
            "loan_usd": round(self.loan_usd, 2),
            "gross_profit_usd": round(self.gross_profit_usd, 4),
            "premium_usd": round(self.premium_usd, 4),
            "gas_usd": round(self.gas_usd, 4),
            "net_profit_usd": round(self.net_profit_usd, 4),
            "direction": self.direction,
        }


def evaluate_opportunity(
    quote_a: Quote,
    quote_b: Quote,
    *,
    loan_usd: float,
    premium_bps: float,
    gas_usd: float,
    min_profit_usd: float,
) -> Opportunity | None:
    """Buy on the cheaper DEX, sell on the richer one (quote per base)."""
    if quote_a.price <= 0 or quote_b.price <= 0:
        return None

    if quote_a.price < quote_b.price:
        buy, sell = quote_a, quote_b
        direction = f"buy@{quote_a.dex} → sell@{quote_b.dex}"
    else:
        buy, sell = quote_b, quote_a
        direction = f"buy@{quote_b.dex} → sell@{quote_a.dex}"

    # Idealized constant-size arb ignoring depth/slippage (educational).
    rel = (sell.price - buy.price) / buy.price
    if rel <= 0:
        return None

    gross = loan_usd * rel
    premium = loan_usd * (premium_bps / 10_000.0)
    net = gross - premium - gas_usd
    if net < min_profit_usd:
        return None

    return Opportunity(
        pair=quote_a.pair,
        buy_dex=buy.dex,
        sell_dex=sell.dex,
        buy_price=buy.price,
        sell_price=sell.price,
        loan_usd=loan_usd,
        gross_profit_usd=gross,
        premium_usd=premium,
        gas_usd=gas_usd,
        net_profit_usd=net,
        direction=direction,
    )


def scan_pairs(settings: dict[str, Any], feed) -> list[Opportunity]:
    opportunities: list[Opportunity] = []
    loan = float(settings.get("max_loan_usd", 10_000))
    premium_bps = float(settings.get("flashloan_premium_bps", 5))
    gas = float(settings.get("estimated_gas_usd", 2.5))
    min_profit = float(settings.get("min_profit_usd", 5))

    for pair in settings.get("pairs", []):
        qa, qb = feed.quotes_for_pair(pair)
        opp = evaluate_opportunity(
            qa,
            qb,
            loan_usd=loan,
            premium_bps=premium_bps,
            gas_usd=gas,
            min_profit_usd=min_profit,
        )
        if opp:
            opportunities.append(opp)
    return opportunities
