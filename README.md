> [!WARNING]
> This project was entirely developed using **Vibe Coding**.

<h1 align="center">
  <span>Katip Celebi</span>
  <img src="assets/katipcelebi.png" alt="Katip Celebi logo" width="48" />
</h1>


A desktop book library manager built with PyQt6. Track your books, lending history, reading goals, and statistics in a clean, modern interface.

## App preview

<p align="center">
  <img src="assets\screenshots/1.png" alt="Katip Celebi application preview" width="900" />
</p>

## Overview

Katip Celebi helps you keep a personal library organized, manage borrowers, and track what you have read without leaving the desktop app.

- Track books, authors, editions, and reading status
- Search and filter your library quickly
- Manage borrowing and returns
- Follow reading progress and goals
- Export data to Excel
- Switch themes and language preferences

## Features

- **Library management** — add, edit, and organize books with ISBN lookup
- **ISBN list import** — bulk-import books from a spreadsheet
- **Lending tracker** — record who borrowed what and when
- **Reading statistics** — charts, summaries, and reading goals
- **Theme support** — Default and contrast styles with light/dark modes
- **Multi-language** — English, Turkish, Russian, Chinese, Spanish, French
- **Cross-platform** — works on Windows and Linux

## Quick start

```bash
git clone https://github.com/farukylmz0550/KatipCelebi.git
cd KatipCelebi
python -m venv .venv

# Windows
.\.venv\Scripts\Activate

# Linux / macOS
# source .venv/bin/activate

pip install -r requirements.txt
python src/app.py
```

## Run tests

Run the unit and integration tests locally with:

```bash
.\.venv\Scripts\activate     # Windows
# or: source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
```

Project version is maintained in the `VERSION` file at the repository root.

## Development

```bash
git clone https://github.com/farukylmz0550/KatipCelebi.git
cd KatipCelebi
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/app.py
```

## Linux build scripts

Use the helper scripts in the `scripts/` folder for distro-specific package builds:

```bash
bash scripts/build-linux-deb.sh
bash scripts/build-linux-rpm.sh
bash scripts/build-linux-arch.sh
```

## Project structure

```text
KatipCelebi/
├── src/
│   ├── app.py
│   ├── books/
│   ├── people/
│   ├── settings/
│   ├── stats/
│   └── shared/
├── assets/
│   ├── lang/
│   └── styles/
├── scripts/
│   ├── build-linux-deb.sh
│   ├── build-linux-rpm.sh
│   └── build-linux-arch.sh
├── KatipCelebi.spec
├── requirements.txt
├── LICENSE
├── README.md
├── CONTRIBUTING.md
└── .gitignore
```

## License

This project is licensed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.txt).

Copyright (C) 2026 farukylmz0550

01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001  01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001

<!-- 01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001 -->
