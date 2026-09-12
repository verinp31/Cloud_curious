#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
UI="$ROOT/client-extensions/crm-amon-ui"
: "${LIFERAY_HOME:?Set LIFERAY_HOME to your DXP home}"
DEST="$LIFERAY_HOME/osgi/client-extensions/crm-amon-ui"
mkdir -p "$DEST"
# Prefer Liferay Workspace client-extension deploy if blade/gradle available;
# fallback: copy built assets + client-extension.yaml
cp -R "$UI/dist/." "$DEST/"
cp "$UI/client-extension.yaml" "$DEST/" 2>/dev/null || true
echo "Copied CE artifacts to $DEST"
echo "Restart DXP or wait for OSGi to pick up the client extension."
