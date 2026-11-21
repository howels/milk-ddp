#!/usr/bin/env bash
# Cut a tagged GitHub release for milk-ddp.
#
#   scripts/release.sh v0.1.2
#   make release VERSION=v0.1.2
#   REPUBLISH=1 scripts/release.sh v0.1.2
#
# Steps:
#   1. Require a clean working tree on main (or RELEASE_ALLOW_DIRTY=1).
#   2. Optionally run make validate (SKIP_VALIDATE=1 to skip).
#   3. Align CMake project() VERSION with the tag (patch CMakeLists.txt if needed).
#   4. Commit that bump when it changed (unless already committed).
#   5. Create an annotated tag and push branch + tag to origin.
#      With REPUBLISH=1, delete and recreate an existing tag, then force-push it.
#   6. Watch .github/workflows/release.yml until it finishes.
#
# The workflow builds amd64/arm64 host binary tarballs, pushes Alpine/Debian
# multi-arch images to ghcr.io/howels/milk-ddp, attaches only the host tarballs
# to the GitHub Release, and links the GHCR pulls in the release notes.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

usage() {
  cat <<'EOF'
Usage: scripts/release.sh vX.Y.Z

Environment:
  SKIP_VALIDATE=1       Skip make validate before tagging
  RELEASE_ALLOW_DIRTY=1 Allow a dirty working tree (not recommended)
  REPUBLISH=1           Delete and recreate an existing tag, then force-push it
  FORCE=1               Alias for REPUBLISH=1
  REMOTE=origin         Git remote to push (default origin)
  BRANCH=main           Branch that must be checked out (default main)
  WATCH=0               Push the tag but do not wait for Actions
EOF
}

TAG="${1:-}"
if [[ -z "${TAG}" || "${TAG}" == "-h" || "${TAG}" == "--help" ]]; then
  usage
  exit $([[ -z "${TAG}" ]] && echo 1 || echo 0)
fi

if [[ ! "${TAG}" =~ ^v[0-9]+\.[0-9]+\.[0-9]+([.-].*)?$ ]]; then
  echo "error: tag must look like v0.1.2 (got: ${TAG})" >&2
  exit 1
fi

VERSION="${TAG#v}"
REMOTE="${REMOTE:-origin}"
BRANCH="${BRANCH:-main}"
WATCH="${WATCH:-1}"
REPUBLISH="${REPUBLISH:-${FORCE:-0}}"

current_branch="$(git rev-parse --abbrev-ref HEAD)"
if [[ "${current_branch}" != "${BRANCH}" ]]; then
  echo "error: checkout ${BRANCH} first (on ${current_branch})" >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" && "${RELEASE_ALLOW_DIRTY:-0}" != "1" ]]; then
  echo "error: working tree is dirty; commit or stash first (or RELEASE_ALLOW_DIRTY=1)" >&2
  git status --short >&2
  exit 1
fi

LOCAL_TAG=0
REMOTE_TAG=0
if git rev-parse -q --verify "refs/tags/${TAG}" >/dev/null; then
  LOCAL_TAG=1
fi
if git ls-remote --tags "${REMOTE}" "refs/tags/${TAG}" | grep -q .; then
  REMOTE_TAG=1
fi

if [[ "${LOCAL_TAG}" -eq 1 || "${REMOTE_TAG}" -eq 1 ]]; then
  if [[ "${REPUBLISH}" != "1" ]]; then
    echo "error: tag ${TAG} already exists (local=${LOCAL_TAG} remote=${REMOTE_TAG}); use REPUBLISH=1 to recreate" >&2
    exit 1
  fi
  echo "==> REPUBLISH=1: removing existing tag ${TAG}"
  if [[ "${LOCAL_TAG}" -eq 1 ]]; then
    git tag -d "${TAG}"
  fi
  if [[ "${REMOTE_TAG}" -eq 1 ]]; then
    git push "${REMOTE}" ":refs/tags/${TAG}"
  fi
fi

if [[ "${SKIP_VALIDATE:-0}" != "1" ]]; then
  echo "==> make validate"
  make validate
fi

# Keep CMake project VERSION in sync with the release tag.
CMAKE_VERSION="$(sed -n 's/^project(milk-ddp VERSION \([0-9.]*\).*/\1/p' CMakeLists.txt | head -1)"
if [[ -z "${CMAKE_VERSION}" ]]; then
  echo "error: could not read project(milk-ddp VERSION …) from CMakeLists.txt" >&2
  exit 1
fi
if [[ "${CMAKE_VERSION}" != "${VERSION}" ]]; then
  echo "==> bump CMake project VERSION ${CMAKE_VERSION} → ${VERSION}"
  sed -i "s/^project(milk-ddp VERSION ${CMAKE_VERSION}/project(milk-ddp VERSION ${VERSION}/" CMakeLists.txt
  if [[ -n "$(git status --porcelain CMakeLists.txt)" ]]; then
    git add CMakeLists.txt
    git commit -m "Bump version to ${VERSION} for ${TAG}."
  fi
fi

echo "==> push ${BRANCH} to ${REMOTE}"
git push "${REMOTE}" "HEAD:refs/heads/${BRANCH}"

echo "==> tag ${TAG}"
git tag -a "${TAG}" -m "${TAG}"

PUSHED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "==> push ${TAG}"
if [[ "${REPUBLISH}" == "1" ]]; then
  git push --force "${REMOTE}" "refs/tags/${TAG}"
else
  git push "${REMOTE}" "${TAG}"
fi

echo "==> release workflow will build host + container assets and publish"
echo "    GHCR: ghcr.io/howels/milk-ddp:${TAG} (Alpine preferred) / ${TAG}-debian"
echo "    https://github.com/howels/milk-ddp/releases/tag/${TAG}"

if [[ "${WATCH}" == "1" ]]; then
  if ! command -v gh >/dev/null 2>&1; then
    echo "warning: gh not installed; not watching the workflow" >&2
    exit 0
  fi
  echo "==> waiting for Release workflow on ${TAG} (created at/after ${PUSHED_AT})"
  RUN_ID=""
  for _ in $(seq 1 40); do
    RUN_ID="$(gh run list --workflow=release.yml --branch "${TAG}" --limit 10 \
      --json databaseId,createdAt \
      | jq -r --arg since "${PUSHED_AT}" \
        '[.[] | select(.createdAt >= $since)] | .[0].databaseId // empty')"
    if [[ -n "${RUN_ID}" ]]; then
      break
    fi
    sleep 3
  done
  if [[ -z "${RUN_ID}" ]]; then
    echo "warning: no new release run found yet; check Actions manually" >&2
    exit 0
  fi
  echo "==> watching run ${RUN_ID}"
  gh run watch "${RUN_ID}" --exit-status
  echo "==> publishing release notes page"
  gh release view "${TAG}" --web 2>/dev/null || gh release view "${TAG}"
fi
