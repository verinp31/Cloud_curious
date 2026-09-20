# Flashloan Arbitrage Demo (éducatif)

Système de **démonstration** pour comprendre le flux :

1. Surveiller des prix entre DEXs (simulés ou RPC public)
2. Détecter un écart d’arbitrage potentiel après frais / gas
3. Illustrer un flashloan (emprunt → trade → remboursement dans la même tx)
4. Tourner en boucle en mode **dry-run** (aucune exécution mainnet par défaut)

## Ce que ce projet n’est pas

- **Pas** une machine à profits. L’arbitrage flashloan rentable est dominé par des bots MEV (latence microseconde, builders privés, capital + infra dédiée).
- **Pas** un conseil financier. Risque de perte totale (gas, bugs, slippage, liquidations de protocole).
- **Pas** un outil d’attaque de protocoles. Uniquement l’arbitrage de prix légitime entre venues.

## Architecture

```
config/settings.yaml     # paires, seuils, mode dry-run
bot/
  prices.py              # sources de prix (simu / Uniswap-style quotes)
  detector.py            # filtre opportunités nettes
  executor.py            # dry-run ou envoi tx (désactivé par défaut)
  runner.py              # boucle permanente
contracts/
  FlashloanArbitrage.sol # exemple Aave V3 flashloan + swaps
scripts/
  simulate.py            # une passe de détection
```

## Démarrage rapide

```bash
cd flashloan-arb
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m bot.runner
```

Mode simulation pure (aucun réseau) :

```bash
ARB_MODE=simulate python -m bot.runner
```

Une seule passe :

```bash
python scripts/simulate.py
```

## Variables d’environnement (optionnel)

| Variable | Rôle |
|---|---|
| `ARB_MODE` | `simulate` (défaut) \| `scan` \| `live` |
| `RPC_URL` | Endpoint JSON-RPC (requis pour `scan` / `live`) |
| `PRIVATE_KEY` | Uniquement si `ARB_MODE=live` — **ne jamais committer** |
| `MIN_PROFIT_USD` | Seuil de profit net minimum (défaut: 5) |
| `POLL_SECONDS` | Intervalle de scan (défaut: 3) |

`live` reste volontairement **bloqué** tant que `ALLOW_LIVE_TRADING=true` n’est pas défini, pour éviter un déploiement accidentel.

## Flux flashloan (concept)

```
1. Emprunter token A via Aave (flashloan, 0 collatéral)
2. Swap A → B sur DEX1 (prix bas)
3. Swap B → A sur DEX2 (prix haut)
4. Rembourser A + premium
5. Garder le reste = profit (ou revert si non rentable)
```

Si l’étape 4 échoue, **toute la transaction revert** : pas de dette, mais le gas est perdu.

## Licence

MIT — usage éducatif. Vous êtes responsable de toute exécution on-chain.
