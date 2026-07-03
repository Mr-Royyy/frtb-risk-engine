#!/usr/bin/env bash
set -euo pipefail

# Initialize a local Git repository and make the first commit.
# Optional: pass your desired GitHub repo name as the first argument.
#
# Usage:
#   bash scripts/init_repo.sh frtb-lite-risk-engine
#
# If GitHub CLI is installed and authenticated, this script can also create the
# remote GitHub repo. If not, it will still create the local Git repo.

REPO_NAME="${1:-frtb-lite-risk-engine}"

git init
git add .
git commit -m "Initial FRTB-lite market risk engine scaffold"

if command -v gh >/dev/null 2>&1; then
  gh repo create "$REPO_NAME" --public --source=. --remote=origin --push
else
  echo "GitHub CLI not found. Local Git repo created."
  echo "Create an empty GitHub repo, then run:"
  echo "git branch -M main"
  echo "git remote add origin https://github.com/YOUR_USERNAME/$REPO_NAME.git"
  echo "git push -u origin main"
fi
