# 03 — Plan de migration Cursor AI (exécutable)

> **Audience :** agent Cursor AI  
> **Objectif :** porter le cœur CRM Twenty (périmètre A — acquisition) vers **Liferay DXP 2026** sous la brique **CRM Amon**, multi-tenant Account Restrictions, Freelance/Agence+bureaux, multi-langue FR/EN.  
> **Références obligatoires :**  
> - [../spec/01-specification-technico-fonctionnelle.md](../spec/01-specification-technico-fonctionnelle.md)  
> - [02-plan-migration-technologique.md](02-plan-migration-technologique.md)  
> - Code inspiration (lecture seule) : https://github.com/twentyhq/twenty  

---

## A. Règles absolues pour l’agent

1. **Ne pas** cloner Twenty dans le runtime Liferay comme dépendance. S’en inspirer (champs, UX, stages).
2. **Ne pas** implémenter email sync, workflows, AI, dashboards (hors V1).
3. **Toujours** activer **Account Restriction** sur chaque Object CRM avant de coder l’UI.
4. **Toujours** externaliser les libellés (FR + EN) — zéro string utilisateur en dur.
5. **Naming :** préfixe `Crm` pour les objets métier ; ne jamais nommer l’Object prospect `Account`.
6. Travailler en **commits atomiques** par phase (P0…P6) ; pousser la branche ; mettre à jour la PR.
7. Avant de marquer une phase DONE : exécuter la **checklist de cloisonnement** (section H).
8. Si le repo courant n’est pas un Liferay Workspace : créer l’arborescence `liferay-crm-amon/` (workspace + client-extension) sans casser d’autres contenus.
9. En cas d’ambiguïté métier : appliquer la spec §0–§21 ; ne pas élargir le scope.
10. Montants : **decimal** + `currencyCode` (pas `amountMicros`).

---

## B. Arborescence cible à créer

```text
liferay-crm-amon/
  README.md
  configs/
    objects/           # JSON export/import Objects (+ picklists)
    accounts/          # roles, custom fields Account
    i18n/              # Language_fr.properties, Language_en.properties
  client-extensions/
    crm-amon-ui/       # React SPA (Vite)
      src/
        app/
        features/
          companies/
          people/
          opportunities/
          tasks/
          notes/
          admin/
          shell/
        i18n/
        api/             # clients Headless Objects
        session/         # account context
  modules/               # uniquement si nécessaire (custom REST)
  rest-client/             # collections Bruno/Postman tests tenant
```

Docs déjà présentes : `docs/crm-amon/**` — **ne pas les supprimer** ; les mettre à jour si l’implémentation diverge (avec justification).

---

## C. Mapping d’implémentation Objects (à créer tel quel)

### C.1 Picklists

| Picklist | Valeurs |
|----------|---------|
| `CRM_ACCOUNT_TYPE` | FREELANCE, AGENCY |
| `CRM_OPPORTUNITY_STAGE` | NEW, QUALIFYING, PROPOSAL, NEGOTIATION, WON, LOST |
| `CRM_TASK_STATUS` | TODO, IN_PROGRESS, DONE |
| `CRM_PERSON_TYPE` | PROSPECT, PARTNER, MEDIA |
| `CRM_TARGET_TYPE` | COMPANY, PERSON, OPPORTUNITY |
| `CRM_CURRENCY` | EUR, USD, GBP |

Localiser labels FR/EN pour chaque valeur.

### C.2 Custom fields Account (système)

| Field | Type | Notes |
|-------|------|-------|
| `accountType` | Picklist CRM_ACCOUNT_TYPE | obligatoire |
| `defaultLanguage` | Text ou Picklist | fr_FR / en_US |
| `defaultCurrency` | Picklist CRM_CURRENCY | défaut EUR |

### C.3 Object `C_CrmOffice`

| Field | Type | Required | Account Restriction |
|-------|------|----------|---------------------|
| `name` | Text | Oui | Oui (via r_account) |
| `city` | Text | Non | |
| `country` | Text | Non | |
| `managerUserId` | Relationship → User | Non | |
| `active` | Boolean | Oui | défaut true |
| `r_account` | Relationship → Account | Oui | **restriction field** |

Unicité : `name` unique par Account (validation CE + unique composite si dispo).

### C.4 Object `C_CrmCompany`

Champs selon spec §5.3. `r_account` = restriction. Relations : `accountOwnerId`→User, `officeId`→CrmOffice.

### C.5 Object `C_CrmPerson`

Champs spec §7.3. Relation `companyId`→CrmCompany (même Account — valider en CE).

### C.6 Object `C_CrmOpportunity`

Champs spec §9.3. Picklist stage. Decimal amount. Relations company, pointOfContact, owner, office.

### C.7 Object `C_CrmTask`

Champs spec §12.3. `targetType` + `targetEntryId` (Long / text ERC) **ou** 3 relations nullable exclusives — **retenir :** trois relations nullable `r_company`, `r_person`, `r_opportunity` avec contrainte CE « exactement une non null si liée ».

### C.8 Object `C_CrmNote`

Idem pattern Task (spec §13).

### C.9 Object `C_CrmView`

Champs spec §14.3. JSON strings pour filters/columns.

---

## D. Phases d’exécution (checklist agent)

### Phase P0 — Socle workspace

**Actions :**

1. Vérifier Java/Node disponibles.
2. Créer `liferay-crm-amon/` + README pointant vers `docs/crm-amon`.
3. Initialiser `client-extensions/crm-amon-ui` (Vite + React + TypeScript).
4. Ajouter scripts `npm run dev` / `build`.
5. Créer fichiers i18n vides `fr.json` / `en.json` avec clés shell minimales.
6. Documenter dans README les prérequis DXP (Objects, Accounts, OAuth CE).

**Done when :** `npm run build` OK sur le CE ; structure dossiers complète.

**Commit message :** `chore(crm-amon): scaffold Liferay CE workspace for Amon CRM`

---

### Phase P1 — Session Account & shell

**Actions :**

1. Implémenter `AccountContext` (React) : `currentAccountId`, `accountType`, `locale`, `switchAccount()`.
2. Écrans : Login redirect placeholder, **Sélecteur Account** (spec §2), **Shell** (spec §3).
3. Language switcher FR/EN branché sur i18n.
4. Mock API optionnelle **uniquement** si DXP absent — derrière interface `CrmApi` ; flag `VITE_USE_MOCKS=true`.
5. Si DXP disponible : OAuth2 headless + appel Accounts de l’utilisateur.

**Done when :** bascule Account + langue visibles ; navigation routes vides OK.

**Commit :** `feat(crm-amon): account context shell and i18n switcher`

---

### Phase P2 — Objects configs + API client

**Actions :**

1. Produire les JSON / instructions d’import Objects dans `configs/objects/` (un fichier par Object + picklists).
2. Produire `configs/accounts/roles.md` listant permissions Account Roles (spec §17.3).
3. Implémenter `src/api/objectsClient.ts` : CRUD générique `/o/c/<object>/` avec header/session Account.
4. Ajouter collection Bruno/Postman `rest-client/` avec 2 jeux : AccountA / AccountB.

**Done when :** configs complètes ; client TypeScript typé pour Company/Person/Opportunity/Task/Note/Office/View.

**Commit :** `feat(crm-amon): object configs and headless API client`

**Validation manuelle DXP (humain ou agent avec instance) :** publier Objects + Account Restriction **avant** P3.

---

### Phase P3 — Companies & People UI

**Actions :**

1. Feature `companies` : liste (spec §5), fiche/create/edit (spec §6).
2. Feature `people` : liste (spec §7), fiche (spec §8).
3. Appliquer toutes les RG-CO-* et RG-PE-* côté UI + messages d’erreur i18n.
4. Filtre bureau si `accountType===AGENCY`.
5. Tests unitaires légers sur validation email unique (mock).

**Done when :** parcours create company → create person linked → view on company tab.

**Commit :** `feat(crm-amon): companies and people screens`

---

### Phase P4 — Opportunities table + kanban

**Actions :**

1. Liste table (spec §9).
2. Kanban (spec §10) avec drag & drop (`@dnd-kit` ou équivalent léger).
3. Modale `lostReason` sur drop LOST.
4. Auto `closeDate` sur WON.
5. Fiche Opportunity (spec §11) + onglets Notes/Tasks.

**Done when :** drag stage persiste via PATCH ; règles WON/LOST OK.

**Commit :** `feat(crm-amon): opportunities table and kanban pipeline`

---

### Phase P5 — Tasks, Notes, Home, Views

**Actions :**

1. Tasks liste + modal (spec §12) — une cible.
2. Notes sur fiches (spec §13).
3. Accueil compteurs (spec §4).
4. Vues sauvegardées basiques (spec §14) — au minimum créer/appliquer filtre ICP.

**Done when :** tâche liée à une opportunity visible sur fiche et liste globale.

**Commit :** `feat(crm-amon): tasks notes home and saved views`

---

### Phase P6 — Admin tenant + durcissement

**Actions :**

1. Admin Account type Freelance/Agence (spec §15) + RG-ADM-*.
2. Admin Bureaux (spec §16) — masqué si FREELANCE.
3. Admin Users UI minimale (spec §17) — si APIs Accounts limitées, documenter les étapes Console Liferay + CE read-only list.
4. Préférences user (spec §18).
5. Exécuter checklist section H ; corriger fuites.
6. Mettre à jour `docs/crm-amon/README.md` avec statut d’avancement.
7. Ajouter guide `liferay-crm-amon/README.md` : déploiement CE, import Objects, seed.

**Done when :** scénario Agence (2 bureaux, 2 users) + scénario Freelance validés (mock ou DXP).

**Commit :** `feat(crm-amon): admin offices roles and tenant hardening`

---

## E. Contrats API (Headless) — conventions agent

```http
GET /o/c/crmcompanies/?page=1&pageSize=20&filter=...
Authorization: Bearer <token>
```

- Toujours filtrer / contextualiser par Account Restriction (le backend Liferay applique ; le CE envoie quand même l’Account choisi pour les champs à la création).
- Création : body JSON inclut `r_accountId` (ou nom de champ relation exact après publication Object).
- Erreurs : mapper 400/403 vers toasts i18n (`errors.forbidden`, `errors.validation`).
- Ne jamais logger de tokens.

Types TypeScript à maintenir synchrones avec `configs/objects`.

---

## F. i18n — clés minimales à créer dès P1

```text
crm-amon.shell.nav.home
crm-amon.shell.nav.companies
crm-amon.shell.nav.people
crm-amon.shell.nav.opportunities
crm-amon.shell.nav.tasks
crm-amon.shell.nav.admin
crm-amon.account.selector.title
crm-amon.account.type.freelance
crm-amon.account.type.agency
crm-amon.opportunity.stage.NEW
crm-amon.opportunity.stage.QUALIFYING
crm-amon.opportunity.stage.PROPOSAL
crm-amon.opportunity.stage.NEGOTIATION
crm-amon.opportunity.stage.WON
crm-amon.opportunity.stage.LOST
crm-amon.common.save
crm-amon.common.cancel
crm-amon.common.search
crm-amon.errors.forbidden
crm-amon.errors.validation
```

Toute nouvelle string UI → ajouter FR **et** EN dans le même commit.

---

## G. Inspiration Twenty — fichiers utiles (lecture)

Lors de l’analyse, prioriser (upstream GitHub `twentyhq/twenty`) :

- Modèle standard objects / fields metadata (packages server workspace-manager / metadata)
- UI pipeline / record index / record show (packages front)
- Docs : https://docs.twenty.com/user-guide/data-model/overview.md

**Interdit :** copier-coller large de code Twenty sous licence sans vérification ; réécrire proprement pour Liferay CE.

---

## H. Checklist cloisonnement multi-tenant (obligatoire)

Exécuter après P2 (API) et après P6 (UI) :

| # | Test | Résultat attendu |
|---|------|------------------|
| H1 | User A liste Companies | Uniquement Account A |
| H2 | User A GET Company id Account B | 403 ou 404 |
| H3 | User A crée Company avec Account B dans le body | Rejet / forcé Account A |
| H4 | Viewer ne peut pas PATCH | 403 |
| H5 | Switch Account en UI | Aucune donnée précédente résiduelle |
| H6 | Freelance n’affiche pas menu Bureaux | OK |
| H7 | Agence sans bureau actif | Bloquer invitation user (RG-OF/USR) |
| H8 | Locale EN | Aucun label FR résiduel dans shell |

Consigner les résultats dans `liferay-crm-amon/rest-client/TENANT_TEST_RESULTS.md`.

---

## I. Ordre des commits attendu (résumé)

1. `chore(crm-amon): scaffold…`
2. `feat(crm-amon): account context shell…`
3. `feat(crm-amon): object configs and headless…`
4. `feat(crm-amon): companies and people…`
5. `feat(crm-amon): opportunities…`
6. `feat(crm-amon): tasks notes home…`
7. `feat(crm-amon): admin… hardening`

Après chaque commit : `git push -u origin <branch>` et mise à jour PR.

---

## J. Definition of Done globale V1

- [ ] Spec écrans §1–§18 couverts fonctionnellement (mocks acceptables si DXP absent, interfaces prêtes DXP)
- [ ] Objects configs complets + Account Restriction documentée
- [ ] Kanban + règles WON/LOST
- [ ] Admin Freelance/Agence/Bureaux
- [ ] FR + EN
- [ ] Checklist H exécutée et tracée
- [ ] README déploiement
- [ ] Aucune feature hors périmètre A

---

## K. Prompt de démarrage (à coller pour un nouvel agent)

```text
Tu es chargé d’implémenter CRM Amon (portage Twenty → Liferay DXP 2026).
Lis et obéis STRICTEMENT à :
- docs/crm-amon/spec/01-specification-technico-fonctionnelle.md
- docs/crm-amon/migration/02-plan-migration-technologique.md
- docs/crm-amon/migration/03-plan-migration-cursor-ai.md
Commence par la Phase P0, puis P1… sans sauter de checklist.
Périmètre A uniquement. Multi-tenant Account Restriction obligatoire.
Multi-langue FR/EN. Account = Freelance ou Agence avec bureaux.
```

---

*Fin du plan Cursor AI.*
