#!/usr/bin/env bash
# Red Herrings - Linux forensics toolkit setup (Debian/Ubuntu).
# Installs the free tools the Red Herrings cases use.
#   chmod +x setup-linux.sh && ./setup-linux.sh
# Uses apt (needs sudo) for system tools and pip for the Python ones.
# For a fully prepared distro instead, use SANS SIFT Workstation (see tools.html).
set -u

say(){ printf '\033[36m%s\033[0m\n' "$*"; }
ok(){  printf '\033[32m%s\033[0m\n' "$*"; }
warn(){ printf '\033[33m%s\033[0m\n' "$*"; }

say "== Red Herrings toolkit setup (Linux, Debian/Ubuntu) =="

if ! command -v apt-get >/dev/null 2>&1; then
  warn "This script targets Debian/Ubuntu (apt). On other distros install the same tools with your package manager, or use SIFT."
  exit 1
fi

APT_PKGS=(
  sleuthkit          # disk analysis (mmls, fls, icat)
  wireshark tshark   # packet captures
  sqlitebrowser      # mobile/browser SQLite DBs
  thunderbird        # email (mbox / .eml)
  jq                 # JSON: cloud audit logs
  p7zip-full         # archives
  python3-pip python3-venv
)

ok "Installing system tools via apt (you may be prompted for sudo) ..."
sudo apt-get update -y
sudo apt-get install -y "${APT_PKGS[@]}"

ok "Installing Python forensics tools (Volatility 3, ALEAPP) in ~/.local ..."
python3 -m pip install --user --upgrade pip volatility3 aleapp || \
  warn "pip install failed; try:  pipx install volatility3 && pipx install aleapp"

cat <<'NOTE'

== Notes ==
  * Eric Zimmerman's tools (Prefetch/LNK/registry/EVTX/timeline) are .NET and
    run best on Windows; on Linux run them under 'dotnet', or use SIFT.
  * Autopsy on Linux: build from https://www.sleuthkit.org/autopsy/ or use SIFT.
  * Chainsaw (EVTX hunting): https://github.com/WithSecureLabs/chainsaw/releases

Prefer a ready-made distro? SANS SIFT Workstation bundles most of the above:
  https://www.sans.org/tools/sift-workstation/

Tool-to-case mapping: https://redherrings.app/tools.html
NOTE

ok "Done."
