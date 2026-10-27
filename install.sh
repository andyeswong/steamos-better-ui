#!/usr/bin/env bash
# Install SteamOS Better UI for the current user (Steam Deck / SteamOS, Bazzite, ROG Ally...).
#
# - Copies the theme and the injector to ~/.local/share/steamos-better-ui
# - Enables Steam's CEF remote debugging (local only, 127.0.0.1:8080)
# - Installs and starts a systemd user service that keeps the styles injected
#
# No root needed, nothing outside your home directory is touched.
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
DEST="$HOME/.local/share/steamos-better-ui"
UNIT_DIR="$HOME/.config/systemd/user"
DEBUG_FLAG="$HOME/.steam/steam/.cef-enable-remote-debugging"

command -v python3 >/dev/null || { echo "python3 not found" >&2; exit 1; }
[ -d "$HOME/.steam/steam" ] || { echo "Steam not found in ~/.steam/steam" >&2; exit 1; }

echo "Installing to $DEST"
mkdir -p "$DEST"
rm -rf "$DEST/theme" "$DEST/injector"   # keep .created-debug-flag across reinstalls
cp -r "$SRC/theme" "$SRC/injector" "$DEST/"

restart_needed=0
if [ ! -f "$DEBUG_FLAG" ]; then
  touch "$DEBUG_FLAG"
  touch "$DEST/.created-debug-flag"   # so uninstall only removes what we added
  restart_needed=1
  echo "Enabled Steam CEF remote debugging ($DEBUG_FLAG)"
fi

mkdir -p "$UNIT_DIR"
cat > "$UNIT_DIR/steamos-better-ui.service" <<EOF
[Unit]
Description=SteamOS Better UI style injector
After=graphical-session.target

[Service]
ExecStart=/usr/bin/env python3 $DEST/injector/sbu_injector.py --theme $DEST/theme
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now steamos-better-ui.service
systemctl --user restart steamos-better-ui.service
echo "Service running: systemctl --user status steamos-better-ui"

if [ "$restart_needed" = 1 ]; then
  echo
  echo "Steam has to restart once to open the debugger port."
  echo "Restart Steam (or reboot) and the theme applies by itself."
fi
