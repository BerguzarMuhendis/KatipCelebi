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

"""The settings file: small, but it is what remembers where the books are."""

import json
import logging
from pathlib import Path
from typing import Any

from shared.paths import config_path
from shared.storage import backup_file, write_atomically

logger = logging.getLogger("katipcelebi")


def _readable() -> bool:
    """Whether the settings file, if present, is something we can parse."""
    path = config_path()
    if not path.exists():
        return True
    try:
        return isinstance(json.loads(path.read_text(encoding="utf-8")), dict)
    except (json.JSONDecodeError, OSError, ValueError, UnicodeDecodeError):
        return False


def load() -> dict:
    """Every setting. An empty dict when there is nothing readable."""
    path = config_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, ValueError, UnicodeDecodeError):
        logger.warning("Could not read %s", path, exc_info=True)
        return {}
    if not isinstance(data, dict):
        logger.warning("%s is not a JSON object", path)
        return {}
    return data


def update(**values: Any) -> bool:
    """Merge settings in. True when they reached the disk.

    Returns a result rather than swallowing it: the caller that has just moved
    the user's library somewhere needs to know whether the note saying where it
    went was actually saved.
    """
    path = config_path()
    # A file we cannot parse still holds the library's location. load() reads
    # it as {}, so merging into that and writing would replace the lot with
    # just the key being set -- one theme change and the app forgets where the
    # books are. Keep the bytes first.
    if not _readable():
        backup_file(path)
        logger.error("Settings file %s is damaged; kept a copy as .bak", path)

    data = load()
    data.update(values)
    try:
        # Same durable temp-and-rename as the library: a settings file
        # half-written by a power cut is exactly how a damaged one comes about,
        # and losing this one loses where the books are.
        write_atomically(path, json.dumps(data, ensure_ascii=False, indent=2))
        return True
    except OSError:
        logger.warning("Could not write %s", path, exc_info=True)
        return False


# ------------------------------------------------------------------------
# Named settings. One pair per thing we remember, so no caller has to know
# what the key is spelled like.


def library_dir() -> Path | None:
    """Where the user keeps their books.

    None until they have said, and None again if it has gone.
    """
    saved = load().get("library_dir")
    # isinstance, like language() below: the file is one people open and edit,
    # and a "library_dir" that came back as a number or a list would blow up
    # in Path() -- a crash at startup over the one setting whose whole job is
    # to survive a damaged file.
    if isinstance(saved, str) and saved and Path(saved).is_dir():
        return Path(saved)
    return None


def set_library_dir(folder: Path) -> bool:
    return update(library_dir=str(folder))


def theme() -> str:
    """Which of the supported themes the user picked.

    Falls back to the default and maps legacy values onto the current Fluent/
    Contrast set while keeping custom QSS as a valid override.
    """
    from shared.theme import (
        CONTRAST_DARK,
        CONTRAST_LIGHT,
        CUSTOM,
        DEFAULT_THEME,
        FLUENT_DARK,
        FLUENT_LIGHT,
        THEMES,
    )

    data = load()
    saved = data.get("theme")
    legacy_map = {
        "m3-light": FLUENT_LIGHT,
        "m3-dark": FLUENT_DARK,
        "adwaita-light": FLUENT_LIGHT,
        "adwaita-dark": FLUENT_DARK,
        "system": FLUENT_DARK,
        "custom": CUSTOM,
        "contrast-light": CONTRAST_LIGHT,
        "contrast-dark": CONTRAST_DARK,
        "fluent-light": FLUENT_LIGHT,
        "fluent-dark": FLUENT_DARK,
    }
    if saved in THEMES:
        return saved
    if saved in legacy_map:
        return legacy_map[saved]
    old = data.get("theme_mode")
    if old == "system":
        return FLUENT_DARK
    if old == "light":
        return FLUENT_LIGHT
    if old == "dark":
        return FLUENT_DARK
    return DEFAULT_THEME


def set_theme(name: str) -> bool:
    return update(theme=name)


def language() -> str:
    """Which language the user picked. English until they say otherwise.

    Not validated here against what files exist: texts.use() does that, and
    falls back to English for a code with no file -- so a language whose file
    was later removed leaves a readable app rather than a broken setting.
    """
    from shared.texts import BASE

    saved = load().get("language")
    return saved if isinstance(saved, str) and saved else BASE


def set_language(code: str) -> bool:
    return update(language=code)


def setup_done() -> bool:
    return bool(load().get("setup_done", False))


def set_setup_done() -> bool:
    return update(setup_done=True)
