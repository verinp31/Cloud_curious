# Liferay CRM Amon

Brique CRM **phase amont** (acquisition) pour SaaS RP — inspiration [Twenty](https://github.com/twentyhq/twenty), cible **Liferay DXP 2026**.

## Docs

- [Index livrables](../docs/crm-amon/README.md)
- Spec, plan migration humain, plan Cursor AI dans `docs/crm-amon/`

## Look & feel (Canvas E-002 / E-003)

- **E-002** — sélecteur d’Account (cartes Agence / Freelance + bureaux)
- **E-003** — shell `SaaS RP | CRM Amon` (topbar + nav gauche)

## Déploiement MacBook Pro (Patrice-2019)

Voir [`docs/MACBOOK_DEPLOY.md`](docs/MACBOOK_DEPLOY.md) et scripts `scripts/mac/`.  
**Prérequis :** démarrer un Cursor self-hosted worker sur la Mac pour que l’agent cloud puisse piloter Liferay localement.

## UI (mocks)

```bash
cd client-extensions/crm-amon-ui
npm install
npm run dev
```

`VITE_USE_MOCKS=true` par défaut.

Comptes démo après login :
- **Oxygen RP** (Agence, bureaux Paris/Lyon)
- **Studio Verin** (Freelance)

## Statut phases

| Phase | Statut |
|-------|--------|
| P0 Scaffold | Done |
| P1 Shell / Account / i18n | Done |
| P2 Objects configs + API mock | Done |
| P3 Companies / People | Done |
| P4 Opportunities kanban | Done |
| P5 Tasks / Notes / Home | Done |
| P6 Admin / tenant hardening | Done (mocks) |

## Déploiement DXP

1. Créer picklists + Objects (`configs/objects`) avec Account Restriction
2. Account Roles (`configs/accounts/roles.md`)
3. OAuth2 Headless + `VITE_USE_MOCKS=false`
4. Déployer Client Extension `crm-amon-ui`
