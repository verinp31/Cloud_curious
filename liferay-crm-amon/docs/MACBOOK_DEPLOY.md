# Déploiement CRM Amon — MacBook Pro Patrice-2019

Ce guide suit [`docs/crm-amon/migration/03-plan-migration-cursor-ai.md`](../../docs/crm-amon/migration/03-plan-migration-cursor-ai.md).

## Bloqueur actuel (Cloud Agent)

Aucun **self-hosted worker** Cursor n’est connecté depuis cette session cloud.  
Sans `cursor worker start` sur la MacBook, l’agent **ne peut pas** atteindre l’instance Liferay locale.

### Action requise sur la MacBook Pro i9

```bash
# 1) Installer / démarrer le worker Cursor self-hosted (même user GitHub que verinp@onepm-consulting.com)
cursor worker start

# 2) Vérifier que le worker apparaît dans Cursor Dashboard → Cloud Agents → Self-hosted workers
#    Labels recommandés : liferay, macbook-patrice-2019
```

Ensuite **renvoyer un message** à cet agent (ou relancer) pour qu’il cible le worker et poursuive P2→P6 sur DXP.

---

## Prérequis Liferay sur la MacBook

| Composant | Cible |
|-----------|--------|
| Liferay DXP | 2025.Q / **2026** (Tomcat) |
| Java | JDK 17+ |
| DB | PostgreSQL 15+ (recommandé) ou HSQL pour démo |
| Node | 20+ (build Client Extension) |
| Ports | `8080` (DXP), `3000`/`5173` (UI mocks optionnelle) |

Variables utiles :

```bash
export LIFERAY_HOME=~/liferay/dxp-2026
export CRM_AMON_REPO=~/dev/Cloud_curious   # ou chemin du clone
```

---

## Script one-shot (à lancer sur la Mac)

```bash
cd "$CRM_AMON_REPO"
chmod +x liferay-crm-amon/scripts/mac/*.sh
./liferay-crm-amon/scripts/mac/01-check-prereqs.sh
./liferay-crm-amon/scripts/mac/02-build-ce.sh
./liferay-crm-amon/scripts/mac/03-import-objects-checklist.sh
# Puis déployer le CE dans $LIFERAY_HOME/osgi/client-extensions/
./liferay-crm-amon/scripts/mac/04-deploy-ce.sh
```

---

## Mapping phases Cursor AI → MacBook

| Phase | Sur MacBook |
|-------|-------------|
| P0 | Workspace déjà dans le repo — rebuild CE |
| P1 | UI Account/Shell (look E-002/E-003) — mocks OK |
| P2 | **Import Objects + Account Restriction** dans Control Panel DXP |
| P3–P5 | Brancher `VITE_USE_MOCKS=false` + OAuth Headless |
| P6 | Roles Account + tests tenant H1–H8 |

Configs Objects : `liferay-crm-amon/configs/objects/`  
Roles : `liferay-crm-amon/configs/accounts/roles.md`

---

## OAuth / Headless (P2+)

1. Control Panel → OAuth2 Applications → créer app **CRM Amon UI**
2. Client credentials / Authorization code selon CE
3. `.env` CE :

```bash
VITE_USE_MOCKS=false
VITE_LIFERAY_BASE_URL=http://localhost:8080
VITE_OAUTH_CLIENT_ID=...
VITE_OAUTH_CLIENT_SECRET=...
```

---

## Look & feel E-002 / E-003

Appliqué dans `client-extensions/crm-amon-ui` :

- **E-002** : écran sélecteur Account (cartes Agence / Freelance + compteur bureaux)
- **E-003** : shell topbar `SaaS RP | CRM Amon` + nav gauche + contenu

> Si vos Canvas Cursor `E-002` / `E-003` diffèrent (couleurs, typo), joignez export PNG/SVG ou partagez le canvas dans ce cloud agent pour un recalage pixel-perfect.
