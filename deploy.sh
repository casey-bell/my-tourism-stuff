#!/usr/bin/env sh
# A POSIX-compliant deployment script intended for use in CI.
# - Validates prerequisites and environment
# - Supports a simple GitHub Pages deployment flow
# - Can be extended with additional strategies if needed

set -eu

# ---------------
# Utility helpers
# ---------------

log() {
  # Info log with UTC timestamp
  # shellcheck disable=SC2039
  printf '%s %s\n' "$(date -u '+%Y-%m-%d %H:%M:%S UTC')" "$*"
}

err() {
  # Error log to stderr
  # shellcheck disable=SC2039
  printf 'ERROR: %s\n' "$*" >&2
}

die() {
  err "$@"
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}

# -----------------------
# Configuration and input
# -----------------------

# Required for authenticated operations (e.g. pushing to a remote)
: "${DEPLOY_TOKEN:?DEPLOY_TOKEN environment variable is required but was not provided. Add it as a repository secret and export it in the workflow step.}"

# Optional configuration:
DEPLOY_STRATEGY="${DEPLOY_STRATEGY:-gh-pages}"     # Supported: gh-pages, noop
DEPLOY_SOURCE_DIR="${DEPLOY_SOURCE_DIR:-}"         # If empty, auto-detects: site, dist, build, public
TARGET_BRANCH="${TARGET_BRANCH:-gh-pages}"         # For gh-pages strategy
COMMIT_MESSAGE_PREFIX="${COMMIT_MESSAGE_PREFIX:-Deploy}"

# The repository slug is normally provided by GitHub Actions.
# Fallback attempts to parse the current git remote if missing.
REPO_SLUG="${GITHUB_REPOSITORY:-}"

# --------------------
# Environment checks
# --------------------

require_command git
require_command mktemp
require_command date
require_command sh

# Confirm repository slug
if [ -z "$REPO_SLUG" ]; then
  # Attempt to infer owner/repo from remote.origin.url
  REMOTE_URL="$(git config --get remote.origin.url || true)"
  case "$REMOTE_URL" in
    https://github.com/*/*.git)
      REPO_SLUG="$(printf '%s\n' "$REMOTE_URL" | sed -e 's#https://github.com/##' -e 's#\.git$##')"
      ;;
    git@github.com:*/*.git)
      REPO_SLUG="$(printf '%s\n' "$REMOTE_URL" | sed -e 's#git@github.com:##' -e 's#\.git$##')"
      ;;
    *)
      die "Unable to determine repository slug. Set GITHUB_REPOSITORY or configure a standard GitHub remote."
      ;;
  esac
fi

# Resolve source directory
if [ -z "$DEPLOY_SOURCE_DIR" ]; then
  for d in site dist build public; do
    if [ -d "$d" ]; then
      DEPLOY_SOURCE_DIR="$d"
      break
    fi
  done
fi

[ -n "$DEPLOY_SOURCE_DIR" ] || die "No deployment source directory found. Set DEPLOY_SOURCE_DIR or create one of: site, dist, build, public."
[ -d "$DEPLOY_SOURCE_DIR" ] || die "Deployment source directory does not exist: $DEPLOY_SOURCE_DIR"

log "Initialising deployment"
log "Repository: $REPO_SLUG"
log "Strategy: $DEPLOY_STRATEGY"
log "Source directory: $DEPLOY_SOURCE_DIR"

# ---------------
# Helper routines
# ---------------

deploy_to_gh_pages() {
  # Publishes the contents of DEPLOY_SOURCE_DIR to the TARGET_BRANCH on the same repo.
  require_command git

  WORK_DIR="$(mktemp -d)"
  cleanup() {
    # Best-effort cleanup
    rm -rf "$WORK_DIR" >/dev/null 2>&1 || true
  }
  trap cleanup EXIT INT HUP TERM

  log "Preparing temporary work area at: $WORK_DIR"
  rm -rf "$WORK_DIR"/*
  mkdir -p "$WORK_DIR"

  # Copy artefacts into work area
  # shellcheck disable=SC2039
  cp -R "${DEPLOY_SOURCE_DIR}/." "$WORK_DIR/"

  (
    cd "$WORK_DIR"

    # Initial git setup
    git init
    # Force-create the target branch
    git checkout -B "$TARGET_BRANCH"

    git config user.name "github-actions[bot]"
    git config user.email "github-actions[bot]@users.noreply.github.com"

    # Optional: prevent Jekyll processing if publishing a static site with dotfiles
    if [ ! -e ".nojekyll" ]; then
      : > .nojekyll
    fi

    git add -A

    SHA_SHORT="${GITHUB_SHA:-$(git rev-parse --short HEAD 2>/dev/null || printf 'unknown')}"
    BRANCH_NAME="${GITHUB_REF_NAME:-$(git rev-parse --abbrev-ref HEAD 2>/dev/null || printf 'unknown')}"
    COMMIT_MSG="${COMMIT_MESSAGE_PREFIX}: ${BRANCH_NAME}@${SHA_SHORT}"

    git commit -m "$COMMIT_MSG"

    REMOTE_URL="https://x-access-token:${DEPLOY_TOKEN}@github.com/${REPO_SLUG}.git"
    git remote add origin "$REMOTE_URL"

    log "Pushing to ${REPO_SLUG} branch ${TARGET_BRANCH}"
    # Force push to publish the artefacts as a standalone snapshot
    git push -f origin "$TARGET_BRANCH"
  )

  log "Deployment completed to branch: ${TARGET_BRANCH}"
}

noop_deploy() {
  log "No operation selected. Skipping deployment."
}

# -----------
# Dispatcher
# -----------

case "$DEPLOY_STRATEGY" in
  gh-pages)
    deploy_to_gh_pages
    ;;
  noop)
    noop_deploy
    ;;
  *)
    die "Unknown DEPLOY_STRATEGY: $DEPLOY_STRATEGY"
    ;;
esac

log "All done."
