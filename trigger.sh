#!/bin/bash
# GitHub Actions workflow_dispatch トリガー
# Usage: ./trigger.sh <workflow_file> [session_name]
# Example: ./trigger.sh portfolio.yml 寄り付き

set -euo pipefail

REPO="soy-tuber/dividend-alert"
WORKFLOW="${1:?Usage: $0 <workflow_file> [session_name]}"
SESSION="${2:-}"

if [ -z "${GITHUB_PAT:-}" ]; then
  echo "Error: GITHUB_PAT is not set" >&2
  exit 1
fi

DATA="{\"ref\":\"main\""
if [ -n "$SESSION" ]; then
  DATA="${DATA},\"inputs\":{\"session\":\"${SESSION}\"}"
fi
DATA="${DATA}}"

curl -s -X POST \
  -H "Authorization: token $GITHUB_PAT" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW}/dispatches" \
  -d "$DATA"
