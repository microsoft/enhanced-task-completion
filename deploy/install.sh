#!/usr/bin/env bash
#
# install.sh — no-clone bootstrap for the BlastBox Omega sample.
#
# Downloads the deploy assets straight from GitHub and runs the guided
# deploy (deploy/deploy.mjs). Nothing is left behind except the solutions
# and connectors it imports into your Power Platform environment.
#
#   curl -fsSL https://raw.githubusercontent.com/microsoft/new-copilot-studio-tech-guide/main/deploy/install.sh | bash
#
# Set BLASTBOX_REF to deploy from a specific branch or tag (default: main).
#
set -euo pipefail

REPO="microsoft/new-copilot-studio-tech-guide"
REF="${BLASTBOX_REF:-main}"

say()  { printf '==> %s\n' "$*"; }
warn() { printf 'WARNING: %s\n' "$*" >&2; }
die()  { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

# --- preflight ---------------------------------------------------------------
command -v node >/dev/null 2>&1 || die "Node.js 18+ is required but was not found. Install it from https://nodejs.org and re-run."
NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0)"
[ "${NODE_MAJOR:-0}" -ge 18 ] || die "Node.js 18+ is required (found $(node -v 2>/dev/null || echo 'unknown'))."
command -v curl >/dev/null 2>&1 || die "curl is required but was not found."
command -v tar  >/dev/null 2>&1 || die "tar is required but was not found."
command -v pac  >/dev/null 2>&1 || warn "pac CLI not found on PATH. The deploy needs it signed in (pac auth create). See deploy/README.md."
command -v az   >/dev/null 2>&1 || warn "az CLI not found on PATH. The deploy uses it for the connection REST calls. See deploy/README.md."

# --- download ----------------------------------------------------------------
TMP="$(mktemp -d 2>/dev/null || mktemp -d -t blastbox)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

say "Downloading the sample (${REPO}@${REF})..."
curl -fsSL "https://codeload.github.com/${REPO}/tar.gz/refs/heads/${REF}" -o "$TMP/src.tgz" \
  || die "Download failed. Check your network, or set BLASTBOX_REF to a valid branch or tag."

say "Extracting the deploy assets..."
tar -xzf "$TMP/src.tgz" -C "$TMP" --strip-components=1 \
  "new-copilot-studio-tech-guide-${REF}/deploy" \
  "new-copilot-studio-tech-guide-${REF}/sample/solution" \
  || die "Extract failed."

[ -f "$TMP/deploy/deploy.mjs" ] || die "deploy/deploy.mjs is missing after extract."

# --- run ---------------------------------------------------------------------
# deploy.mjs is interactive. When this script is piped to bash (curl | bash),
# stdin is the script itself, so restore the terminal on /dev/tty for the
# prompts — but only when /dev/tty is actually readable. In CI/headless shells
# it may exist yet be unusable ("Device not configured"), and with --yes the
# prompts never fire anyway, so fall back to the inherited stdin.
cd "$TMP"
say "Starting the guided deploy..."
if [ -e /dev/tty ] && (: < /dev/tty) 2>/dev/null; then
  node deploy/deploy.mjs "$@" < /dev/tty
else
  node deploy/deploy.mjs "$@"
fi
