#!/usr/bin/env bash
set -euo pipefail
echo "== CRM Amon prerequisites (Mac) =="
command -v java >/dev/null && java -version || { echo "MISSING: Java JDK 17+"; exit 1; }
command -v node >/dev/null && node -v || { echo "MISSING: Node 20+"; exit 1; }
command -v npm >/dev/null && npm -v || { echo "MISSING: npm"; exit 1; }
if [[ -z "${LIFERAY_HOME:-}" ]]; then
  echo "WARN: LIFERAY_HOME not set (example: export LIFERAY_HOME=~/liferay/dxp-2026)"
else
  [[ -d "$LIFERAY_HOME" ]] && echo "LIFERAY_HOME=$LIFERAY_HOME OK" || echo "WARN: LIFERAY_HOME path missing: $LIFERAY_HOME"
fi
echo "Prereq check done."
