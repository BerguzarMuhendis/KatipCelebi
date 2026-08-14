#!/usr/bin/env bash
set -euo pipefail

git clone https://github.com/farukylmz0550/KatipCelebi.git
cd KatipCelebi
sudo dnf install -y python3 python3-pip mesa-libGL libxkbcommon dbus-libs \
  xcb-util-cursor || true
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt pyinstaller
pyinstaller KatipCelebi.spec
mkdir -p pkg/usr/share/applications pkg/usr/share/icons/hicolor/256x256/apps
cp assets/katipcelebi.png pkg/usr/share/icons/hicolor/256x256/apps/katipcelebi.png
printf '[Desktop Entry]\nType=Application\nName=Katip Celebi\nExec=/opt/katipcelebi/KatipCelebi\nIcon=katipcelebi\nCategories=Office;\n' > pkg/usr/share/applications/katipcelebi.desktop
fpm -s dir -t rpm -n katipcelebi -v 1.0 \
  --rpm-depends "mesa-libGL, libxkbcommon, dbus-libs, xcb-util-cursor" \
  -C dist/KatipCelebi usr=/opt/katipcelebi

echo "Build complete: katipcelebi-1.0-1.x86_64.rpm"
  01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001

# 01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001
