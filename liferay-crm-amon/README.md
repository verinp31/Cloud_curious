# Liferay CRM Amon

Brique CRM **phase amont** (acquisition) pour SaaS RP — inspiration [Twenty](https://github.com/twentyhq/twenty), cible **Liferay DXP 2026**.

## Docs

- [Index livrables](../docs/crm-amon/README.md)
- Spec, plan migration humain, plan Cursor AI dans `docs/crm-amon/`

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
