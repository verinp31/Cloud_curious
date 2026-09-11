# Checklist cloisonnement multi-tenant (mocks)

Exécutée contre le store mock local (`localStorage` / `crmApi`) — à rejouer sur DXP Headless après import Objects.

| # | Test | Résultat |
|---|------|----------|
| H1 | User A liste Companies | PASS — filtrées par `accountId` |
| H2 | User A GET Company Account B | PASS — `NOT_FOUND` / forbidden |
| H3 | Création forcée Account B | PASS — `accountId` session imposé par API |
| H4 | Viewer PATCH | PASS — `FORBIDDEN` |
| H5 | Switch Account UI | PASS — listes rechargées via `bump` / context |
| H6 | Freelance sans menu Bureaux | PASS — Admin masque offices |
| H7 | Agence crée bureau | PASS |
| H8 | Locale EN | PASS — switch FR/EN |

Date : 2026-09-11
