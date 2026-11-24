#!/bin/bash
# install_digger.sh - build "Digger Remastered" (the real 1983 Windmill Software game, remade by
# Andrew Jenner and freely released, SDL port by Maksym Sobolyev: github.com/sobomax/digger)
# and the touch helper that lets Tiago play it on the touchscreen.
#   bash v2/install_digger.sh      (takes ~5-10 minutes on a Pi 3)
set -e
P="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$HOME/digger-src"
echo "== packages"
sudo apt-get install -y git cmake libsdl2-dev zlib1g-dev python3-evdev
echo "== source"
if [ -d "$SRC/.git" ]; then git -C "$SRC" pull --ff-only; else git clone --depth 1 https://github.com/sobomax/digger "$SRC"; fi
echo "== touchscreen tweak: no keyboard needed for high scores (initials are filled in automatically)"
python3 - "$SRC/scores.c" <<'PY'
import sys
p = sys.argv[1]; s = open(p).read()
if "DIGGER_INITIALS" not in s:
    s = s.replace("      getinitials(ddap);",
        '      { const char *ini = getenv("DIGGER_INITIALS"); int k;'
        '        strcpy(scoreinit[0], "...");'
        '        for (k = 0; k < 3 && ini && ini[k]; k++) scoreinit[0][k] = ini[k];'
        '        if (!ini) memcpy(scoreinit[0], "TIA", 3);'
        '        recputinit(scoreinit[0]); }', 1)
    open(p, "w").write(s)
    print("   patched scores.c")
PY
echo "== build (be patient on a Pi 3)"
mkdir -p "$SRC/build" && cd "$SRC/build"
cmake .. -DCMAKE_BUILD_TYPE=Release >/dev/null
make -j2 digger
mkdir -p "$P/v2/bin"
cp digger "$P/v2/bin/digger"
echo "== touch helper permission (it presses arrow keys for the touchscreen)"
echo "$(id -un) ALL=(root) NOPASSWD: /usr/bin/python3 $P/v2/digger_touch.py" | sudo tee /etc/sudoers.d/kidbox-digger >/dev/null
sudo chmod 440 /etc/sudoers.d/kidbox-digger
echo "Done: Digger is in the Games menu (restart the app: sudo systemctl restart kidbox)"
