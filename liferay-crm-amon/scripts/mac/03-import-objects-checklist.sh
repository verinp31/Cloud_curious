#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
echo "== Manual DXP checklist (Control Panel) =="
echo "1. Create picklists from: $ROOT/configs/objects/picklists.json"
echo "2. Create Objects C_CrmOffice, C_CrmCompany, C_CrmPerson, C_CrmOpportunity, C_CrmTask, C_CrmNote, C_CrmView"
echo "3. Enable Account Restriction on each Object (r_account relationship)"
echo "4. Publish Objects + generate Headless APIs"
echo "5. Create Account Roles per $ROOT/configs/accounts/roles.md"
echo "6. Seed 1 AGENCY + 1 FREELANCE Account for smoke tests"
echo "See also: $ROOT/configs/objects/README.md"
