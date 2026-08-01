> [!WARNING]
> This project was entirely developed using **Vibe Coding**.

# Katip Celebi

A desktop book library manager built with PyQt6. Track your books, lending history, reading goals, and statistics — all in a clean, modern interface with Material 3 and Adwaita theme support.

## Features

- **Library management** — add, edit, and organise books with ISBN lookup via Open Library
- **ISBN list import** — paste ISBNs into a `.xlsx` template and add them in bulk (files up to 20 MiB)
- **Lending tracker** — record who borrowed which book and when
- **Reading statistics** — charts and goals to track your reading habits
- **Multiple themes** — Material 3 (light/dark), Adwaita (light/dark), system preference, and custom QSS
- **Multi-language** — English, Turkish, Russian, Chinese, Spanish, French
- **Excel export** — export your library to `.xlsx`, safe from formula injection
- **Cross-platform** — runs on Windows and Linux

## Quick Install

Install Katip Celebi on Windows using WinGet, or build a native package for your Linux distribution using the one-liners below.

Linux build commands use the bundled `KatipCelebi.spec` — no need to pass `--add-data`, `--name`, `--windowed`, or `--icon` flags.

## Windows (Powershell / CMD)
```powershell

winget install farukylmz0550.katipcelebi
```

### Ubuntu / Debian (apt)

```bash
git clone https://github.com/farukylmz0550/KatipCelebi.git && cd KatipCelebi && \
sudo apt update && sudo apt install -y python3 python3-pip python3-venv \
libgl1-mesa-glx libxkbcommon0 libdbus-1-3 libxcb-cursor0 \
adwaita-qt6 || true && \
python3 -m venv .venv && . .venv/bin/activate && \
pip install -r requirements.txt pyinstaller && \
pyinstaller KatipCelebi.spec && \
mkdir -p pkg/usr/share/applications pkg/usr/share/icons/hicolor/256x256/apps && \
cp assets/katipcelebi.png pkg/usr/share/icons/hicolor/256x256/apps/katipcelebi.png && \
printf '[Desktop Entry]\nType=Application\nName=Katip Celebi\nExec=/opt/katipcelebi/KatipCelebi\nIcon=katipcelebi\nCategories=Office;\n' > pkg/usr/share/applications/katipcelebi.desktop && \
fpm -s dir -t deb -n katipcelebi -v 1.0 \
  --deb-depends "libgl1-mesa-glx, libxkbcommon0, libdbus-1-3, libxcb-cursor0" \
  -C dist/KatipCelebi usr=/opt/katipcelebi && \
echo "Build complete: katipcelebi_1.0_amd64.deb"
```

### Fedora (dnf)

```bash
git clone https://github.com/farukylmz0550/KatipCelebi.git && cd KatipCelebi && \
sudo dnf install -y python3 python3-pip mesa-libGL libxkbcommon dbus-libs \
xcb-util-cursor adwaita-qt6 || true && \
python3 -m venv .venv && . .venv/bin/activate && \
pip install -r requirements.txt pyinstaller && \
pyinstaller KatipCelebi.spec && \
mkdir -p pkg/usr/share/applications pkg/usr/share/icons/hicolor/256x256/apps && \
cp assets/katipcelebi.png pkg/usr/share/icons/hicolor/256x256/apps/katipcelebi.png && \
printf '[Desktop Entry]\nType=Application\nName=Katip Celebi\nExec=/opt/katipcelebi/KatipCelebi\nIcon=katipcelebi\nCategories=Office;\n' > pkg/usr/share/applications/katipcelebi.desktop && \
fpm -s dir -t rpm -n katipcelebi -v 1.0 \
  --rpm-depends "mesa-libGL, libxkbcommon, dbus-libs, xcb-util-cursor" \
  -C dist/KatipCelebi usr=/opt/katipcelebi && \
echo "Build complete: katipcelebi-1.0-1.x86_64.rpm"
```

### Arch Linux (pacman)

```bash
git clone https://github.com/farukylmz0550/KatipCelebi.git && cd KatipCelebi && \
sudo pacman -S --needed python python-pip mesa libxkbcommon dbus xcb-util-cursor \
adwaita-qt6 || true && \
python3 -m venv .venv && . .venv/bin/activate && \
pip install -r requirements.txt pyinstaller && \
pyinstaller KatipCelebi.spec && \
mkdir -p pkg/usr/bin pkg/usr/share/katipcelebi \
  pkg/usr/share/applications pkg/usr/share/icons/hicolor/256x256/apps && \
cp -r dist/KatipCelebi/* pkg/usr/share/katipcelebi/ && \
cp assets/katipcelebi.png pkg/usr/share/icons/hicolor/256x256/apps/katipcelebi.png && \
printf '#!/bin/sh\nexec /opt/katipcelebi/KatipCelebi "$@"\n' > pkg/usr/bin/katipcelebi && \
chmod +x pkg/usr/bin/katipcelebi && \
printf '[Desktop Entry]\nType=Application\nName=Katip Celebi\nExec=/opt/katipcelebi/KatipCelebi\nIcon=katipcelebi\nCategories=Office;\n' > pkg/usr/share/applications/katipcelebi.desktop && \
tar -czf katipcelebi-1.0-1-x86_64.pkg.tar.zst -C pkg . && \
echo "Build complete: katipcelebi-1.0-1-x86_64.pkg.tar.zst"
```

## Development

```bash
git clone https://github.com/farukylmz0550/KatipCelebi.git && cd KatipCelebi
python3 -m venv .venv && . .venv/bin/activate   # Linux
python -m venv .venv; .\.venv\Scripts\Activate   # Windows
pip install -r requirements.txt
python src/app.py             # launch the app
```

## Project Structure

```
KatipCelebi/
├── src/
│   ├── app.py              # entry point, main window
│   ├── books/              # library, cards, covers, lending
│   ├── people/             # borrower management
│   ├── settings/           # settings page, relocation
│   ├── stats/              # charts, goals, statistics
│   └── shared/             # theme, palette, icons, config
├── assets/
│   ├── icons/              # SVG icons
│   ├── lang/               # en, tr, ru, zh, es, fr
│   └── styles/             # default.qss (custom theme template)
├── KatipCelebi.spec        # PyInstaller build spec
├── requirements.txt
├── LICENSE-GPLV3           # Source code license (GPLv3)
├── LICENSE-APACHE          # Asset license (Apache 2.0)
└── CONTRIBUTING.md         # Contributing rules file
```

## Custom Themes

Place a `custom.qss` file in the app data directory to create your own look. Select **Custom** from the theme picker, or edit via Settings → Custom Style → Edit.

## Adding a Language

1. Copy `assets/lang/en.json` to `assets/lang/xx.json` (where `xx` is the language code)
2. Set the `_name` field to the language's native name (e.g. `"Deutsch"`)
3. Translate all values — keys ending with `_(n)` or `{...}` must keep the same placeholders
4. Add the flag emoji to `FLAG_FOR_LANGUAGE` in `src/shared/icons.py`
5. That's it — the language appears in the picker automatically

## License

This project uses mixed licensing to separate source code from design assets:

*   **Source Code:** All code in this repository is licensed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.txt).
*   **Visual Assets:** All graphics, logos, and images are licensed under the [APACHE 2.0](https://www.apache.org/licenses/LICENSE-2.0.txt)

Copyright (C) 2026 farukylmz0550
