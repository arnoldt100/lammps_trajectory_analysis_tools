#!/usr/bin/env bash

# Exit immediately if any command fails
set -e

VERSION_FILE="VERSION"
NEW_VERSION="$1"

# 1. Check if a version argument was provided
if [ -z "$NEW_VERSION" ]; then
    echo "Error: No version provided." >&2
    echo "Usage: $0 <version-number> (e.g., $0 1.4.2)" >&2
    exit 1
fi

# 2. Validate semantic version format (X.Y.Z)
if [[ ! "$NEW_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Version '$NEW_VERSION' must follow X.Y.Z format (e.g., 2.0.1)" >&2
    exit 1
fi

# 3. Read current version for the console summary
CURRENT_VERSION="none"
if [ -f "$VERSION_FILE" ]; then
    CURRENT_VERSION=$(cat "$VERSION_FILE" | tr -d '[:space:]')
fi

# 4. Update the version file
echo "$NEW_VERSION" > "$VERSION_FILE"

# 5. Execute Git operations
git add "$VERSION_FILE"
git commit -m "chore: bump version to $NEW_VERSION"
git tag -a "v$NEW_VERSION" -m "Release v$NEW_VERSION"

# 6. Display confirmation
echo "✅ Version updated from [$CURRENT_VERSION] to [$NEW_VERSION]"
echo "👉 Run: git push origin HEAD --tags"

