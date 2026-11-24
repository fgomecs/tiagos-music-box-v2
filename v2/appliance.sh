#!/bin/bash
# appliance.sh - run the kids app WITHOUT the desktop (boots straight into the app).
#
#   bash v2/appliance.sh on    # no desktop: console boot + kidbox as a system service
#   bash v2/appliance.sh off   # back to the normal desktop (app via desktop autostart)
#
# Parents still have: the web portal (:8080), SSH, and Pi Connect's remote shell.
# Hidden parent menu on the screen: hold the top-left corner for 5 seconds.
set -e
P="$(cd "$(dirname "$0")/.." && pwd)"
ME="$(id -un)"
SVC=/etc/systemd/system/kidbox.service
AUTO="$HOME/.config/autostart/kidbox.desktop"

case "$1" in
on)
  echo "== kidbox service (starts at boot, restarts if it ever crashes)"
  sudo tee "$SVC" >/dev/null <<UNIT
[Unit]
Description=Tiago's Music Box V2 (kids app, no desktop)
After=systemd-user-sessions.service sound.target network.target
Conflicts=getty@tty1.service

[Service]
User=$ME
Group=$ME
SupplementaryGroups=video input audio render
WorkingDirectory=$P
Environment=SDL_VIDEODRIVER=kmsdrm
Environment=PYTHONUNBUFFERED=1
ExecStart=/usr/bin/python3 $P/v2/kidbox.py
StandardOutput=append:$P/v2/kidbox.log
StandardError=append:$P/v2/kidbox.log
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
UNIT
  rm -f "$AUTO"
  echo "== boot to console (no desktop)"
  sudo raspi-config nonint do_boot_behaviour B1
  echo "== keep Pi Connect running without anyone logged in"
  sudo loginctl enable-linger "$ME" || true
  sudo systemctl daemon-reload
  sudo systemctl enable kidbox.service
  echo "Done. Reboot: sudo reboot"
  ;;
off)
  echo "== back to the desktop"
  sudo systemctl disable --now kidbox.service 2>/dev/null || true
  sudo rm -f "$SVC"
  sudo systemctl daemon-reload
  mkdir -p "$(dirname "$AUTO")"
  cat > "$AUTO" <<DESK
[Desktop Entry]
Type=Application
Name=KidBox
Exec=/bin/bash -c "sleep 3; /usr/bin/python3 $P/v2/kidbox.py >> $P/v2/kidbox.log 2>&1"
X-GNOME-Autostart-enabled=true
DESK
  sudo raspi-config nonint do_boot_behaviour B4
  echo "Done. Reboot: sudo reboot"
  ;;
*)
  echo "usage: bash v2/appliance.sh on|off"; exit 1 ;;
esac
