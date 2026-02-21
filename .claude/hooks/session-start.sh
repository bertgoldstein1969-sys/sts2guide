#!/bin/bash
set -euo pipefail

# Only run in remote (Claude Code on the web) environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Install htmlhint for HTML linting
npm install -g htmlhint --prefer-offline 2>/dev/null || npm install -g htmlhint
