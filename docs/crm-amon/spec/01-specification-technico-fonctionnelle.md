# 01 — Spécification technico-fonctionnelle CRM Amon

**Produit :** brique CRM phase amont (acquisition) — SaaS RP  
**Inspiration :** Twenty CRM (GitHub `twentyhq/twenty`)  
**Cible :** Liferay DXP 2026  
**Maquettes :** wireframes ASCII  
**Langues V1 :** français (défaut), anglais  

---

## 0. Glossaire & modèle multi-tenant

### 0.1 Distinction critique (collision de vocabulaire Twenty)

| Terme | Signification dans ce SaaS | Équivalent Twenty | Équivalent Liferay |
|-------|----------------------------|-------------------|--------------------|
| **Account (tenant)** | Client du SaaS : freelance ou agence RP | Workspace | `Account` (Commerce/Accounts) |
| **Bureau** | Site / antenne d’une agence | *(absent)* | Account Organization **ou** Object `CrmOffice` lié à Account |
| **Employé** | Utilisateur rattaché à l’Account (et éventuellement à un bureau) | WorkspaceMember | User + Account User + Account Role |
| **CrmCompany** | Entreprise **prospect / client** suivie en acquisition | Company | Object `C_CrmCompany` (Account Restricted) |
| **CrmPerson** | Contact / lead individuel | Person | Object `C_CrmPerson` |
| **CrmOpportunity** | Affaire / opportunité d’acquisition | Opportunity | Object `C_CrmOpportunity` |
| **CrmTask / CrmNote** | Tâche / note liées à des fiches | Task / Note | Objects + relations cibles |

### 0.2 Types d’Account

| Type Account | `accountType` | Structure |
|--------------|---------------|-----------|
| Freelance | `FREELANCE` | 1 Account, 1 utilisateur principal, **pas de bureau obligatoire** |
| Agence RP | `AGENCY` | 1 Account, N utilisateurs, **N bureaux** (au moins 1), employés rattachés à 1+ bureaux |

### 0.3 Cloisonnement des données

- Tous les Objects CRM portent une relation **obligatoire** vers `Account`.
- **Account Restriction** activée : un utilisateur ne voit / crée / modifie que les entrées de **ses** Accounts.
- Les rôles **Account-scoped** (Account Manager, Sales, Viewer) définissent les permissions CRM.
- Un rôle Regular type `CRM Access` donne uniquement l’accès au panneau / site (sans contourner le cloisonnement Account).
- **Règle :** jamais de rôle Regular avec `View` global sur les Objects CRM en production multi-tenant.

### 0.4 Pipeline acquisition (stages Opportunity) — V1

| Code | Libellé FR | Libellé EN | Ordre |
|------|------------|------------|-------|
| `NEW` | Nouveau | New | 1 |
| `QUALIFYING` | Qualification | Qualifying | 2 |
| `PROPOSAL` | Proposition | Proposal | 3 |
| `NEGOTIATION` | Négociation | Negotiation | 4 |
| `WON` | Gagné | Won | 5 |
| `LOST` | Perdu | Lost | 6 |

---

## 1. Écran — Authentification / Login

### 1.1 Wireframe

```
+----------------------------------------------------------+
|                    [Logo SaaS RP]                        |
|                                                          |
|              Connexion / Sign in                         |
|                                                          |
|   Email        [____________________________]            |
|   Mot de passe [____________________________]            |
|                                                          |
|   [ Se connecter ]                                       |
|                                                          |
|   Mot de passe oublié ?                                  |
|   Langue: [FR v]                                         |
+----------------------------------------------------------+
```

### 1.2 Description

Point d’entrée. Authentification Liferay (écran login ou Client Extension). Après succès : redirection vers le shell CRM Amon du site dédié, dans le contexte du **dernier Account actif** de l’utilisateur (ou sélecteur si plusieurs).

### 1.3 Champs

| Champ | Type | Obligatoire | Notes |
|-------|------|-------------|-------|
| email | Text (email) | Oui | Login Liferay |
| password | Password | Oui | |
| locale | Select | Non | `fr_FR`, `en_US` — stocké en préférence utilisateur |

### 1.4 Règles de gestion

- RG-AUTH-01 : credentials invalides → message générique (pas d’énumération d’emails).
- RG-AUTH-02 : utilisateur sans Account → écran « Accès non provisionné ».
- RG-AUTH-03 : utilisateur multi-Account → après login, écran **Sélecteur d’Account** si aucun Account actif en session.
- RG-AUTH-04 : locale choisie appliquée immédiatement (Language Liferay + cookies).

---

## 2. Écran — Sélecteur d’Account (contexte tenant)

### 2.1 Wireframe

```
+----------------------------------------------------------+
|  Choisissez votre espace de travail                      |
|                                                          |
|  +------------------+  +------------------+              |
|  | Agence Oxygen RP |  | Freelance P. Verin|              |
|  | Type: Agence     |  | Type: Freelance  |              |
|  | 3 bureaux        |  |                  |              |
|  | [ Entrer ]       |  | [ Entrer ]       |              |
|  +------------------+  +------------------+              |
+----------------------------------------------------------+
```

### 2.2 Description

Liste les Accounts auxquels l’utilisateur est rattaché. Fixe le **Account courant** en session (cookie / preference) pour toutes les requêtes Objects.

### 2.3 Champs (carte Account)

| Champ | Source |
|-------|--------|
| accountName | Account.name |
| accountType | Custom field Account `accountType` |
| officeCount | Agrégat bureaux (si AGENCY) |

### 2.4 Règles de gestion

- RG-ACC-01 : seuls les Accounts actifs de l’utilisateur sont listés.
- RG-ACC-02 : bascule d’Account purge le cache UI et recharge les listes CRM.
- RG-ACC-03 : toute création d’objet CRM injecte automatiquement l’Account courant (champ non éditable après création — propriétaire Account Restriction).

---

## 3. Écran — Shell applicatif (coque + navigation)

### 3.1 Wireframe

```
+------------------------------------------------------------------+
| SaaS RP | CRM Amon     Account: [Oxygen RP v]  FR|EN  (User v)  |
+----------+-------------------------------------------------------+
| Accueil  |                                                       |
| Entrepr. |              [ zone contenu ]                         |
| Contacts |                                                       |
| Opp.     |                                                       |
| Tâches   |                                                       |
| -------- |                                                       |
| Admin*   |                                                       |
+----------+-------------------------------------------------------+
* Admin visible si Account Role Manager / Admin
```

### 3.2 Description

Layout permanent : nav gauche, barre haute (Account switcher, langue, profil). Zone centrale = routes CRM.

### 3.3 Champs / éléments

| Élément | Comportement |
|---------|--------------|
| Account switcher | Change le tenant courant |
| Language switcher | FR / EN |
| Menu Admin | Visible selon permissions Account Role |

### 3.4 Règles de gestion

- RG-SHELL-01 : navigation hors Account courant interdite (404 / empty state).
- RG-SHELL-02 : labels via Language Keys (`crm-amon.*`).
- RG-SHELL-03 : deep-link conserve Account id dans l’URL ou la session.

---

## 4. Écran — Accueil CRM (tableau de bord léger V1)

### 4.1 Wireframe

```
+------------------------------------------------------------------+
| Accueil — Acquisition                                            |
|                                                                  |
|  Opportunités ouvertes: 12     À qualifier: 4     Tâches du jour: 3|
|                                                                  |
|  Dernières opportunités                                          |
|  +------------------------------------------------------------+  |
|  | Nom            | Entreprise | Stage         | Montant     |  |
|  | Campagne Q2    | MediaCorp  | Proposition   | 12 000 EUR  |  |
|  +------------------------------------------------------------+  |
|                                                                  |
|  [ + Nouvelle opportunité ]  [ + Nouveau contact ]               |
+------------------------------------------------------------------+
```

### 4.2 Description

Vue synthèse **scopée Account**. Pas de BI complexe en V1 : compteurs + 5 dernières opportunités ouvertes + raccourcis création.

### 4.3 Champs affichés

| Widget | Données |
|--------|---------|
| Compteur ouvertes | Opportunities où stage ∉ {WON, LOST} |
| Compteur à qualifier | stage = QUALIFYING |
| Tâches du jour | Tasks dues aujourd’hui, status ≠ DONE |
| Liste récente | name, companyName, stage, amount |

### 4.4 Règles de gestion

- RG-HOME-01 : agrégats filtrés Account Restriction + soft-delete exclus.
- RG-HOME-02 : clic ligne → fiche Opportunity.
- RG-HOME-03 : compteurs en devise Account (défaut EUR).

---

## 5. Écran — Liste Entreprises (CrmCompany)

### 5.1 Wireframe

```
+------------------------------------------------------------------+
| Entreprises                          [ Recherche... ] [ + Ajouter]|
| Vues: ( Toutes | ICP | Sans owner )           Affichage: Table   |
|                                                                  |
| | Nom           | Domaine      | Owner   | Employés | Ville    | |
| |--------------+--------------+---------+----------+-----------| |
| | MediaCorp    | mediacorp.fr | Alice   | 120      | Paris     | |
| | StartupX     | startupx.io  | —       | 8        | Lyon      | |
|                                                                  |
| < 1 2 3 >                                                        |
+------------------------------------------------------------------+
```

### 5.2 Description

Équivalent Twenty **Companies** en vue table. Recherche, vues sauvegardées, pagination, création.

### 5.3 Champs

| Champ | Type | Obligatoire | Mapping Twenty |
|-------|------|-------------|----------------|
| name | Text | Oui | name |
| domainName | Text (URL/domaine) | Non | domainName.primaryLinkUrl |
| linkedinUrl | Text (URL) | Non | linkedinLink |
| employees | Integer | Non | employees |
| addressStreet | Text | Non | address.street1 |
| addressCity | Text | Non | address.city |
| addressCountry | Text | Non | address.country |
| idealCustomerProfile | Boolean | Non | idealCustomerProfile |
| accountOwnerId | Relation → User (Account) | Non | accountOwnerId |
| rAccount | Relation → Account | Oui (auto) | *(tenant)* |
| officeId | Relation → CrmOffice | Non | *(extension RP — filtrage agence)* |
| createdAt / updatedAt | DateTime | Système | createdAt / updatedAt |

### 5.4 Règles de gestion

- RG-CO-01 : `name` unique **par Account** (pas global instance).
- RG-CO-02 : suppression = soft-delete ; masquée des listes par défaut.
- RG-CO-03 : si Account = AGENCY et user rattaché à un bureau, filtre optionnel « Mon bureau ».
- RG-CO-04 : `accountOwnerId` doit être membre de l’Account courant.
- RG-CO-05 : import CSV V1 hors scope (prévu V1.1).

---

## 6. Écran — Fiche / Création / Édition Entreprise

### 6.1 Wireframe

```
+------------------------------------------------------------------+
| <- Entreprises / MediaCorp                    [ Éditer ] [ ... ] |
|                                                                  |
|  Onglets: [ Détails | Contacts | Opportunités | Notes | Tâches ] |
|                                                                  |
|  Nom*            [ MediaCorp______________ ]                     |
|  Domaine         [ mediacorp.fr___________ ]                     |
|  LinkedIn        [ https://linkedin.com/... ]                    |
|  Employés        [ 120 ]     ICP [x]                             |
|  Owner           [ Alice Dupont v ]                              |
|  Bureau          [ Paris v ]   (si AGENCY)                       |
|  Adresse         [ 10 rue X, Paris, FR ]                         |
|                                                                  |
|  Contacts liés (3)          Opportunités ouvertes (2)            |
+------------------------------------------------------------------+
```

### 6.2 Description

Fiche 360 légère : identité entreprise + listes liées (People, Opportunities, Notes, Tasks).

### 6.3 Champs

Même liste que §5.3 + onglets relationnels en lecture.

### 6.4 Règles de gestion

- RG-CO-10 : après création, `rAccount` non modifiable.
- RG-CO-11 : suppression bloquée s’il existe des Opportunities ouvertes (stage non terminal) — confirmation soft-delete sinon.
- RG-CO-12 : onglet Contacts = People avec `companyId` = cette entreprise.
- RG-CO-13 : création Contact depuis la fiche préremplit `companyId`.

---

## 7. Écran — Liste Contacts (CrmPerson)

### 7.1 Wireframe

```
+------------------------------------------------------------------+
| Contacts                             [ Recherche... ] [ + Ajouter]|
| Vues: ( Tous | Sans entreprise | Leads )                         |
|                                                                  |
| | Nom              | Email            | Entreprise | Titre     | |
| |-----------------+------------------+------------+------------| |
| | Jean Martin     | j.m@mediacorp.fr | MediaCorp  | Dircom    | |
| | Sophie Bernard  | s@startupx.io    | StartupX   | CEO       | |
+------------------------------------------------------------------+
```

### 7.2 Description

Équivalent Twenty **People**. Contacts / leads individuels rattachés éventuellement à une CrmCompany.

### 7.3 Champs

| Champ | Type | Obligatoire | Mapping Twenty |
|-------|------|-------------|----------------|
| firstName | Text | Oui | name.firstName |
| lastName | Text | Oui | name.lastName |
| jobTitle | Text | Non | jobTitle |
| primaryEmail | Text (email) | Conditionnel* | emails.primaryEmail |
| additionalEmails | Text (multi) | Non | emails.additionalEmails |
| phoneNumber | Text | Non | phones.primaryPhoneNumber |
| phoneCallingCode | Text | Non | phones.primaryPhoneCallingCode |
| linkedinUrl | Text | Non | linkedinLink |
| city | Text | Non | city |
| companyId | Relation → CrmCompany | Non | companyId |
| personType | Select | Non | *(extension)* Prospect / Partner / Media |
| rAccount | Relation → Account | Oui (auto) | tenant |
| officeId | Relation → CrmOffice | Non | extension RP |

\* Au moins un identifiant de contact : email **ou** téléphone.

### 7.4 Règles de gestion

- RG-PE-01 : unicité `primaryEmail` **par Account** si renseigné.
- RG-PE-02 : `companyId` doit appartenir au même Account.
- RG-PE-03 : soft-delete ; restauration Admin uniquement.
- RG-PE-04 : `personType=Media` utile métier RP (journalistes) — n’impacte pas les permissions.

---

## 8. Écran — Fiche Contact

### 8.1 Wireframe

```
+------------------------------------------------------------------+
| <- Contacts / Jean Martin                     [ Éditer ]         |
| Onglets: [ Détails | Opportunités | Notes | Tâches ]             |
|                                                                  |
|  Jean Martin — Dircom @ MediaCorp                                |
|  Email: j.m@mediacorp.fr     Tél: +33 6 …                        |
|  Type: Prospect                                                  |
|                                                                  |
|  Opportunités où point de contact:                               |
|   - Campagne Q2 (Proposition)                                    |
+------------------------------------------------------------------+
```

### 8.2 Description

Fiche Person Twenty : identité + relations (company, opportunities en `pointOfContact`, notes, tasks).

### 8.3 / 8.4 Champs & règles

Voir §7.3 ; RG-PE-10 : depuis Opportunity, le point de contact doit être lié à la même company (warning si différent, blocage soft configurable).

---

## 9. Écran — Liste Opportunités

### 9.1 Wireframe

```
+------------------------------------------------------------------+
| Opportunités          [Table|Kanban]  [ Recherche ] [ + Ajouter] |
| Filtre stage: [ Tous v ]  Owner: [ Tous v ]                      |
|                                                                  |
| | Nom          | Entreprise | Stage        | Montant  | Close  | |
| |--------------+------------+--------------+----------+--------| |
| | Campagne Q2  | MediaCorp  | Proposition  | 12 000€  | 30/06  | |
| | Audit digital| StartupX   | Qualification| 4 500€   | —      | |
+------------------------------------------------------------------+
```

### 9.2 Description

Vue table des deals. Bascule vers kanban (§10).

### 9.3 Champs

| Champ | Type | Obligatoire | Mapping Twenty |
|-------|------|-------------|----------------|
| name | Text | Oui | name |
| stage | Select (pipeline) | Oui | stage |
| amount | Decimal | Non | amount (micros→decimal) |
| currencyCode | Select | Oui si amount | currencyCode (défaut EUR) |
| closeDate | Date | Non | closeDate |
| companyId | Relation → CrmCompany | Oui | companyId |
| pointOfContactId | Relation → CrmPerson | Non | pointOfContactId |
| ownerId | Relation → User | Non | *(owner commercial)* |
| probability | Integer 0–100 | Non | *(extension)* |
| lostReason | Text | Si LOST | *(extension)* |
| rAccount | Relation → Account | Oui (auto) | tenant |
| officeId | Relation → CrmOffice | Non | extension |
| position | Integer | Non | position (ordre kanban) |

### 9.4 Règles de gestion

- RG-OP-01 : `companyId` obligatoire et même Account.
- RG-OP-02 : stage défaut à la création = `NEW`.
- RG-OP-03 : montant stocké en décimal (EUR) — **pas** en micros Twenty côté Liferay.
- RG-OP-04 : `pointOfContactId.companyId` devrait = `companyId` (warning).

---

## 10. Écran — Pipeline Kanban Opportunités

### 10.1 Wireframe

```
+------------------------------------------------------------------+
| Opportunités [Table|Kanban*]                                     |
|                                                                  |
| NEW      QUALIFY   PROPOSAL   NEGO      WON        LOST          |
| ------   -------   --------   -------   --------   --------      |
| |Audit|  |Camp.Q2| |Deal Z |           |Win A  |   |Old X |      |
| |4.5k |  |12k    | |8k     |           |20k    |   |3k    |      |
| ------   -------   --------                                      |
|                                                                  |
| (drag & drop carte → change stage)                               |
+------------------------------------------------------------------+
```

### 10.2 Description

Équivalent Twenty pipeline board. Colonnes = stages. Drag & drop met à jour `stage` + `position`.

### 10.3 Champs carte

| Affiché | Source |
|---------|--------|
| Titre | name |
| Entreprise | companyId.name |
| Montant | amount + currency |
| Owner avatar | ownerId |

### 10.4 Règles de gestion

- RG-KB-01 : drop sur WON → closeDate = aujourd’hui si vide.
- RG-KB-02 : drop sur LOST → modal `lostReason` obligatoire.
- RG-KB-03 : drag refusé si user sans permission Update sur Opportunity.
- RG-KB-04 : colonnes ordonnées selon table §0.4 ; non réordonnables en V1.
- RG-KB-05 : totaux colonne optionnels (somme amount) — affichage V1.

---

## 11. Écran — Fiche Opportunité

### 11.1 Wireframe

```
+------------------------------------------------------------------+
| <- Opportunités / Campagne Q2                 Stage: [Proposition]|
|                                                                  |
|  Montant   [ 12000 ] [EUR v]     Close [ 2026-06-30 ]            |
|  Entreprise [ MediaCorp v ]      Contact [ Jean Martin v ]       |
|  Owner      [ Alice v ]          Bureau  [ Paris v ]             |
|  Probabilité [ 60 ] %                                            |
|                                                                  |
|  Onglets: [ Notes | Tâches | Activité ]                          |
|  + Ajouter une note                                              |
|  + Créer une tâche                                               |
+------------------------------------------------------------------+
```

### 11.2 Description

Fiche deal complète + notes/tâches liées (équivalent Twenty record show page).

### 11.3 / 11.4

Champs §9.3.  
RG-OP-10 : changement stage via select = mêmes règles que kanban.  
RG-OP-11 : WON/LOST = stages terminaux ; réouverture autorisée Manager uniquement.

---

## 12. Écran — Tâches (liste + création)

### 12.1 Wireframe

```
+------------------------------------------------------------------+
| Tâches                    Filtre: [ Ouvertes v ] [ + Nouvelle ]  |
|                                                                  |
| | Titre              | Statut      | Échéance | Assigné | Lié à ||
| |-------------------+-------------+----------+---------+-------||
| | Relancer Jean     | TODO        | 12/09    | Alice   | Opp Q2||
| | Envoyer proposition| IN_PROGRESS| 15/09    | Bob     | Media ||
+------------------------------------------------------------------+
| Modal Nouvelle tâche                                             |
| Titre* [____________] Statut [TODO] Échéance [____] Assigné [v]  |
| Lié à: (o) Opp ( ) Contact ( ) Entreprise   Record [____v]       |
| Corps  [ markdown / rich text ____________________________ ]     |
+------------------------------------------------------------------+
```

### 12.2 Description

Équivalent Twenty Tasks + TaskTargets (liaison polymorphe simplifiée en V1 : une cible principale).

### 12.3 Champs

| Champ | Type | Obligatoire | Mapping Twenty |
|-------|------|-------------|----------------|
| title | Text | Oui | title |
| body | RichText / Markdown | Non | bodyV2.markdown |
| status | Select TODO / IN_PROGRESS / DONE | Oui | status |
| dueAt | DateTime | Non | dueAt |
| assigneeId | Relation → User | Non | assigneeId |
| targetType | Select Opportunity/Person/Company | Non | taskTargets |
| targetId | Relation dynamique | Si targetType | taskTargets |
| rAccount | Account | Oui (auto) | tenant |

### 12.4 Règles de gestion

- RG-TK-01 : `assigneeId` membre de l’Account.
- RG-TK-02 : cible doit appartenir au même Account.
- RG-TK-03 : passage DONE n’efface pas `dueAt`.
- RG-TK-04 : V1 = **une** cible principale (multi-targets Twenty → V1.1).

---

## 13. Écran — Notes (création sur fiche)

### 13.1 Wireframe

```
+------------------------------------------------------------------+
| Notes — MediaCorp                                                |
|                                                                  |
| +--------------------------------------------------------------+ |
| | Titre: Compte-rendu call 10/09                               | |
| | Corps: Besoin d'un dispositif RP product launch...           | |
| | Par Alice — 10/09/2026                                       | |
| +--------------------------------------------------------------+ |
|                                                                  |
| [ + Ajouter une note ]                                           |
|   Titre [________]                                               |
|   Corps [______________________________________________]         |
|   [ Enregistrer ]                                                |
+------------------------------------------------------------------+
```

### 13.2 Description

Notes attachées à Company / Person / Opportunity (Note + NoteTarget Twenty).

### 13.3 Champs

| Champ | Type | Obligatoire |
|-------|------|-------------|
| title | Text | Oui |
| body | RichText | Non |
| targetType / targetId | Relation | Oui |
| rAccount | Account | Auto |
| createdBy | User | Auto |

### 13.4 Règles de gestion

- RG-NT-01 : note toujours liée à exactement 1 cible en V1.
- RG-NT-02 : édition limitée à auteur ou Manager.
- RG-NT-03 : soft-delete.

---

## 14. Écran — Vues & filtres

### 14.1 Wireframe

```
+------------------------------------------------------------------+
| Entreprises                                                      |
| Vues: ( Toutes* | Mes ICP | Sans owner )  [ + Enregistrer vue ]  |
| Filtres actifs: ICP = true   Owner = Alice                       |
| Colonnes visibles: Nom, Domaine, Owner, Ville                    |
+------------------------------------------------------------------+
```

### 14.2 Description

Équivalent simplifié des **Views** Twenty : filtres + colonnes + nom de vue, **scopés Account**.

### 14.3 Champs (métadonnée CrmView)

| Champ | Type |
|-------|------|
| name | Text |
| objectType | Select Company/Person/Opportunity/Task |
| filtersJson | JSON |
| columnsJson | JSON |
| isShared | Boolean (Account-wide vs personnel) |
| rAccount | Account |

### 14.4 Règles de gestion

- RG-VW-01 : vues personnelles visibles créateur ; vues shared = Account.
- RG-VW-02 : JSON validé côté API (allowlist champs filtrables).
- RG-VW-03 : kanban Opportunity = vue spéciale `display=KANBAN`.

---

## 15. Écran — Admin Account (Freelance / Agence)

### 15.1 Wireframe

```
+------------------------------------------------------------------+
| Administration / Account                                         |
|                                                                  |
|  Nom Account     [ Oxygen RP______________ ]                     |
|  Type*           ( ) Freelance   (•) Agence RP                   |
|  Langue défaut   [ Français v ]                                  |
|  Devise défaut   [ EUR v ]                                       |
|                                                                  |
|  [ Enregistrer ]                                                 |
|  Attention: passage Agence → Freelance interdit si >1 user       |
+------------------------------------------------------------------+
```

### 15.2 Description

Paramètres du tenant SaaS. Détermine si la gestion des bureaux est active.

### 15.3 Champs (custom fields Account)

| Champ | Type | Obligatoire |
|-------|------|-------------|
| accountType | Select FREELANCE / AGENCY | Oui |
| defaultLanguage | Select | Oui |
| defaultCurrency | Select | Oui |

### 15.4 Règles de gestion

- RG-ADM-01 : seul Account Admin / Manager modifie.
- RG-ADM-02 : `AGENCY → FREELANCE` interdit si users > 1 ou bureaux > 0.
- RG-ADM-03 : `FREELANCE → AGENCY` autorisé ; crée un bureau « Principal » automatiquement.
- RG-ADM-04 : Freelance : menu Bureaux masqué.

---

## 16. Écran — Admin Bureaux (CrmOffice)

### 16.1 Wireframe

```
+------------------------------------------------------------------+
| Administration / Bureaux                    [ + Ajouter bureau ] |
|                                                                  |
| | Nom     | Ville  | Responsable | Employés | Actif |            |
| |---------+--------+-------------+----------+-------|            |
| | Paris   | Paris  | Alice       | 8        | Oui   |            |
| | Lyon    | Lyon   | Bob         | 3        | Oui   |            |
+------------------------------------------------------------------+
```

### 16.2 Description

Uniquement si `accountType=AGENCY`. Regroupe les employés et optionnellement les données CRM (`officeId`).

### 16.3 Champs CrmOffice

| Champ | Type | Obligatoire |
|-------|------|-------------|
| name | Text | Oui |
| city | Text | Non |
| country | Text | Non |
| managerUserId | Relation User | Non |
| active | Boolean | Oui (défaut true) |
| rAccount | Account | Auto |

### 16.4 Règles de gestion

- RG-OF-01 : au moins 1 bureau actif pour AGENCY.
- RG-OF-02 : désactivation bureau interdite s’il reste des users rattachés (réaffectation obligatoire).
- RG-OF-03 : nom unique par Account.
- RG-OF-04 : données CRM avec `officeId` restent visibles Account-wide (filtre UI, pas cloisonnement strict V1 — cloisonnement strict = Account Restriction uniquement).

---

## 17. Écran — Admin Utilisateurs & rôles

### 17.1 Wireframe

```
+------------------------------------------------------------------+
| Administration / Utilisateurs               [ + Inviter ]        |
|                                                                  |
| | Nom           | Email           | Rôle Account | Bureau(x) |   |
| |---------------+-----------------+--------------+-----------|   |
| | Alice Dupont  | a@oxygen.fr     | Manager      | Paris     |   |
| | Bob Martin    | b@oxygen.fr     | Sales        | Lyon      |   |
| | Carla Vue     | c@oxygen.fr     | Viewer       | Paris     |   |
+------------------------------------------------------------------+
```

### 17.2 Description

Gestion Account Users + Account Roles + rattachement bureaux.

### 17.3 Rôles Account V1

| Rôle | Droits CRM |
|------|------------|
| Account Admin | Tout + admin Account/bureaux/users |
| Manager | CRUD Objects CRM + vues shared |
| Sales | CRUD sur ses records + lecture Account |
| Viewer | Lecture seule |

### 17.4 Règles de gestion

- RG-USR-01 : invitation email crée / lie un User Liferay à l’Account.
- RG-USR-02 : Freelance : max 1 user actif (configurable plus tard).
- RG-USR-03 : Agence : user doit avoir ≥ 1 bureau.
- RG-USR-04 : retrait du dernier Admin interdit.
- RG-USR-05 : permissions Objects via Account Roles (pas Regular Roles sur data).

---

## 18. Écran — Préférences utilisateur / langue

### 18.1 Wireframe

```
+------------------------------------------------------------------+
| Profil / Préférences                                             |
|  Langue UI     [ Français v ]                                    |
|  Fuseau        [ Europe/Paris v ]                                |
|  Account défaut[ Oxygen RP v ]                                   |
|  [ Enregistrer ]                                                 |
+------------------------------------------------------------------+
```

### 18.2 Description

Préférences personnelles (locale, timezone, Account par défaut).

### 18.3 / 18.4

RG-PREF-01 : changement langue recharge les Language Keys.  
RG-PREF-02 : dates affichées dans le fuseau utilisateur (stockage UTC).

---

## 19. Matrice écrans → composants Liferay

| Écran | Implémentation cible |
|-------|----------------------|
| Login | Liferay Login + i18n |
| Sélecteur Account | Client Extension React |
| Shell + listes + fiches + kanban | Client Extension React (SPA) |
| Objects data | Liferay Objects + Headless |
| Account Restriction | Config Objects |
| Admin Account/Users | Liferay Accounts UI + CE custom bureaux |
| i18n | Language Override + bundles CE |

---

## 20. Exigences transverses

| ID | Exigence |
|----|----------|
| XF-01 | Multi-tenant strict Account Restriction |
| XF-02 | Multi-langue FR/EN (clés, pas de texte en dur) |
| XF-03 | Accessibilité clavier basique listes/modales |
| XF-04 | Responsive : table → cards sur mobile ; kanban scroll horizontal |
| XF-05 | Audit : createdBy / modifiedBy sur Objects |
| XF-06 | Soft-delete sur Objects métier |
| XF-07 | API Headless consommable par le reste du SaaS RP |

---

## 21. Traçabilité Twenty → Amon

| Twenty | Amon / Liferay | Porté V1 |
|--------|----------------|----------|
| Workspace | Account | Oui |
| WorkspaceMember | Account User | Oui |
| Company | CrmCompany | Oui |
| Person | CrmPerson | Oui |
| Opportunity + stages | CrmOpportunity | Oui |
| Task / TaskTarget | CrmTask (+ cible unique) | Oui (simplifié) |
| Note / NoteTarget | CrmNote (+ cible unique) | Oui (simplifié) |
| Views | CrmView | Oui (simplifié) |
| Email/Calendar sync | — | Non |
| Workflows / AI / Dashboards | — | Non |
| *(nouveau)* Offices | CrmOffice | Oui (RP) |
| *(nouveau)* accountType | Custom field Account | Oui (RP) |

---

*Fin de la spécification technico-fonctionnelle V1.*
