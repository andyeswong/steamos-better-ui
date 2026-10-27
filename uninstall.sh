#!/usr/bin/env bash
# Remove SteamOS Better UI: stop the service, strip the styles from the running
# Steam UI and delete the installed files.
# Steam's CEF remote debugging flag is removed only if install.sh created it.
set -euo pipefail

DEST="$HOME/.local/share/steamos-better-ui"
UNIT="$HOME/.config/systemd/user/steamos-better-ui.service"
DEBUG_FLAG="$HOME/.steam/steam/.cef-enable-remote-debugging"

systemctl --user disable --now steamos-better-ui.service 2>/dev/null || true
rm -f "$UNIT"
systemctl --user daemon-reload

if [ -f "$DEST/injector/sbu_injector.py" ]; then
  python3 "$DEST/injector/sbu_injector.py" --theme "$DEST/theme" --remove || true
fi
if [ -f "$DEST/.created-debug-flag" ]; then
  rm -f "$DEBUG_FLAG"
  echo "Removed Steam CEF remote debugging flag (applies after Steam restarts)"
fi
rm -rf "$DEST"
echo "SteamOS Better UI removed."
