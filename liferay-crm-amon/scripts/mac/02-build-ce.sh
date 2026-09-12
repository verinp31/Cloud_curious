#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
UI="$ROOT/client-extensions/crm-amon-ui"
cd "$UI"
npm ci || npm install
npm run build
echo "Build OK → $UI/dist"
