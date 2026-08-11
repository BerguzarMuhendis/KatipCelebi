# Katip Celebi
# Copyright (C) 2026 farukylmz0550
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Where everything lives.

The user's books live in a folder they choose. Everything else -- the settings
that remember that choice, the cover cache, the log -- lives in the usual place
for the platform, so a fresh install still knows where to look.
"""

import os
import sys
from pathlib import Path

APP_DIR_NAME = "KatipCelebi"

# The user's own files, inside the folder they picked. Deliberately not the
# names the previous version used: if someone points this app at their old
# library's folder, the two must not fight over the same file.
LIBRARY_FILENAME = "library.json"
PEOPLE_FILENAME = "people.json"
LOANS_FILENAME = "loans.json"
LOG_FILENAME = "katipcelebi.log"


def assets_dir() -> Path:
    """The icons and flags that ship with the app.

    PyInstaller unpacks them into a temporary folder and points sys._MEIPASS at
    it; running from a checkout, they are the assets/ beside src/. Asked here
    once so that nothing else has to know the difference.
    """
    bundled = getattr(sys, "_MEIPASS", None)
    if bundled:
        return Path(bundled) / "assets"
    return Path(__file__).resolve().parent.parent.parent / "assets"


def app_data_dir() -> Path:
    """The platform's own place for an app's settings."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config")
    path = Path(base) / APP_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_path() -> Path:
    return app_data_dir() / "settings.json"


def cover_cache_dir() -> Path:
    path = app_data_dir() / "covers"
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_library_dir() -> Path:
    """What to offer when the user is asked where to keep their books."""
    documents = Path.home() / "Documents"
    return (documents if documents.is_dir() else Path.home()) / APP_DIR_NAME


def library_path(folder: Path) -> Path:
    return Path(folder) / LIBRARY_FILENAME


def people_path(folder: Path) -> Path:
    return Path(folder) / PEOPLE_FILENAME


def loans_path(folder: Path) -> Path:
    return Path(folder) / LOANS_FILENAME
