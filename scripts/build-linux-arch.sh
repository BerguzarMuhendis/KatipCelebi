#!/usr/bin/env bash
set -euo pipefail

git clone https://github.com/farukylmz0550/KatipCelebi.git
cd KatipCelebi
sudo pacman -S --needed python python-pip mesa libxkbcommon dbus xcb-util-cursor \
  adwaita-qt6 || true
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt pyinstaller
pyinstaller KatipCelebi.spec
mkdir -p pkg/usr/bin pkg/usr/share/katipcelebi \
  pkg/usr/share/applications pkg/usr/share/icons/hicolor/256x256/apps
cp -r dist/KatipCelebi/* pkg/usr/share/katipcelebi/
cp assets/katipcelebi.png pkg/usr/share/icons/hicolor/256x256/apps/katipcelebi.png
printf '#!/bin/sh\nexec /opt/katipcelebi/KatipCelebi "$@"\n' > pkg/usr/bin/katipcelebi
chmod +x pkg/usr/bin/katipcelebi
printf '[Desktop Entry]\nType=Application\nName=Katip Celebi\nExec=/opt/katipcelebi/KatipCelebi\nIcon=katipcelebi\nCategories=Office;\n' > pkg/usr/share/applications/katipcelebi.desktop
tar -czf katipcelebi-1.0-1-x86_64.pkg.tar.zst -C pkg .

echo "Build complete: katipcelebi-1.0-1-x86_64.pkg.tar.zst"
