#!/usr/bin/env bash
# Run this on a machine that already has git auth for DRwillychiu/TXF1-Strategy-Lab.
# Sandbox had no credentials, so the automated push was skipped this run.
set -euo pipefail

REPO_URL="git@github.com:DRwillychiu/TXF1-Strategy-Lab.git"   # or https://...
BATCH="batch01"
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"          # this batch01 folder
MD_FILE="${SRC_DIR}/../TXF1_Strategies_Batch01.md"

WORK=$(mktemp -d)
git clone "${REPO_URL}" "${WORK}/repo"
mkdir -p "${WORK}/repo/strategies/${BATCH}"
cp -r "${SRC_DIR}/pl_code" "${WORK}/repo/strategies/${BATCH}/"
cp "${SRC_DIR}/backtest.py" "${WORK}/repo/strategies/${BATCH}/"
cp "${SRC_DIR}/results.json" "${WORK}/repo/strategies/${BATCH}/"
cp "${MD_FILE}"              "${WORK}/repo/strategies/${BATCH}/TXF1_Strategies_Batch01.md"

cd "${WORK}/repo"
git add strategies/${BATCH}
git commit -m "feat: Batch01 - 5 TXF1 strategies with backtest results"
git push origin HEAD
echo "Pushed."
