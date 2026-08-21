#!/bin/bash
# Install the repo's git hooks. .git/hooks is NOT tracked by git, so a hook left
# only there is invisible to review, absent after a clone, and silently lost.
set -eu
cd "$(dirname "$0")/../.." || exit 1
for h in scripts/hooks/post-commit; do
  n="$(basename "$h")"
  cp "$h" ".git/hooks/$n"
  chmod +x ".git/hooks/$n"
  echo "installed .git/hooks/$n"
done
