# CRM Amon — Livrables portage Twenty → Liferay DXP 2026

Brique CRM **phase amont** (acquisition) du SaaS RP, inspirée de [Twenty](https://github.com/twentyhq/twenty), à porter sous **Liferay DXP 2026**.

## Livrables

| # | Document | Public | Fichier |
|---|----------|--------|---------|
| 1 | Spécification technico-fonctionnelle (écrans, wireframes, champs, règles) | Métier + tech | [spec/01-specification-technico-fonctionnelle.md](spec/01-specification-technico-fonctionnelle.md) |
| 2 | Plan de migration technologique (humain) | Chef de projet / architecte | [migration/02-plan-migration-technologique.md](migration/02-plan-migration-technologique.md) |
| 3 | Plan de migration Cursor AI (markdown exécutable) | Agent Cursor | [migration/03-plan-migration-cursor-ai.md](migration/03-plan-migration-cursor-ai.md) |

## Périmètre V1 (option A)

Cœur CRM acquisition uniquement :

- Authentification / coque applicative
- Entreprises prospects (`CrmCompany`)
- Contacts (`CrmPerson`)
- Opportunités (liste + kanban)
- Tâches & notes
- Vues / filtres
- Admin tenant (Account, bureaux, rôles)
- Multi-langue

**Hors V1 :** sync email/calendrier, workflows avancés, AI/agents, dashboards analytiques.

## Principes non négociables

1. **Multi-tenant** via Liferay **Accounts** + **Account Restriction** sur tous les Objects CRM.
2. Un Account = **Freelance** (1 personne) **ou** **Agence RP** (plusieurs employés, regroupés par **bureaux**).
3. **Multi-langue** (FR / EN minimum) via Language Keys Liferay + Client Extension i18n.
4. Inspiration Twenty : **modèle de données et parcours**, pas copie du stack NestJS/React.

## Source d’inspiration

- Code : https://github.com/twentyhq/twenty
- Docs : https://docs.twenty.com
- Objets standards Twenty : People, Companies, Opportunities, Tasks, Notes


## Statut implémentation (2026-09-11)

Workspace code : [`liferay-crm-amon/`](../../liferay-crm-amon/README.md)

- SPA React mocks multi-tenant : **opérationnelle** (`npm run build` OK)
- Configs Objects / Account Roles / i18n plateforme : présentes
- Import DXP réel : à faire sur instance Liferay (hors de ce repo de test)
