#!/usr/bin/env bash
set -euo pipefail

git clone https://github.com/farukylmz0550/KatipCelebi.git
cd KatipCelebi
sudo apt update
sudo apt install -y python3 python3-pip python3-venv \
  libgl1-mesa-glx libxkbcommon0 libdbus-1-3 libxcb-cursor0 || true
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt pyinstaller
pyinstaller KatipCelebi.spec
mkdir -p pkg/usr/share/applications pkg/usr/share/icons/hicolor/256x256/apps
cp assets/katipcelebi.png pkg/usr/share/icons/hicolor/256x256/apps/katipcelebi.png
printf '[Desktop Entry]\nType=Application\nName=Katip Celebi\nExec=/opt/katipcelebi/KatipCelebi\nIcon=katipcelebi\nCategories=Office;\n' > pkg/usr/share/applications/katipcelebi.desktop
fpm -s dir -t deb -n katipcelebi -v 1.0 \
  --deb-depends "libgl1-mesa-glx, libxkbcommon0, libdbus-1-3, libxcb-cursor0" \
  -C dist/KatipCelebi usr=/opt/katipcelebi

echo "Build complete: katipcelebi_1.0_amd64.deb"
