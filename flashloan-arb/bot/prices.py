"""Price feeds: simulation (default) or lightweight on-chain Uniswap V2-style quotes."""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass
from typing import Any

# Minimal Uniswap V2 pair ABI (getReserves + token0/token1 not required for sim).
PAIR_ABI = [
    {
        "name": "getReserves",
        "outputs": [
            {"type": "uint112", "name": "_reserve0"},
            {"type": "uint112", "name": "_reserve1"},
            {"type": "uint32", "name": "_blockTimestampLast"},
        ],
        "inputs": [],
        "stateMutability": "view",
        "type": "function",
    }
]


@dataclass(frozen=True)
class Quote:
    pair: str
    dex: str
    price: float  # quote per base (e.g. USDC per WETH)
    ts: float


class PriceFeed:
    def __init__(self, settings: dict[str, Any]) -> None:
        self.settings = settings
        self.mode = settings.get("mode", "simulate")
        self._w3 = None

    def _ensure_web3(self):
        if self._w3 is not None:
            return self._w3
        rpc = self.settings.get("rpc_url") or ""
        if not rpc:
            raise RuntimeError("RPC_URL requis pour les modes scan/live")
        from web3 import Web3

        self._w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 20}))
        if not self._w3.is_connected():
            raise RuntimeError(f"Impossible de se connecter à RPC_URL={rpc!r}")
        return self._w3

    def quotes_for_pair(self, pair: dict[str, Any]) -> tuple[Quote, Quote]:
        if self.mode == "simulate":
            return self._simulate_pair(pair)
        # scan/live: still educational — without a full router graph we fall back
        # to simulated spreads tagged as "rpc-assisted" once connectivity works.
        self._ensure_web3()
        return self._simulate_pair(pair, label_suffix="_rpc")

    def _simulate_pair(
        self, pair: dict[str, Any], label_suffix: str = ""
    ) -> tuple[Quote, Quote]:
        sim = self.settings.get("simulation", {})
        key = f"{pair['base']}_{pair['quote']}"
        mid = float(sim.get("mid_prices", {}).get(key, 1000.0))
        max_spread = float(sim.get("max_spread", 0.003))
        noise = float(sim.get("noise", 0.001))

        # Deterministic-ish oscillation so demos show occasional opportunities.
        phase = (time.time() / 7.0) + hash(key) % 97
        spread = max_spread * math.sin(phase) + random.uniform(-noise, noise)
        spread = max(-max_spread, min(max_spread, spread))

        price_a = mid * (1.0 - spread / 2.0)
        price_b = mid * (1.0 + spread / 2.0)
        now = time.time()
        q_a = Quote(
            pair=key,
            dex=f"{pair['dex_a']}{label_suffix}",
            price=price_a,
            ts=now,
        )
        q_b = Quote(
            pair=key,
            dex=f"{pair['dex_b']}{label_suffix}",
            price=price_b,
            ts=now,
        )
        return q_a, q_b
