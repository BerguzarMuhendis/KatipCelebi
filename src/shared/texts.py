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

"""Every word the user reads, in the language they chose.

The words live in assets/lang, one JSON file per language. The code never
holds a phrase: it calls text("nav_add"), and this module hands back "Add
Book" or "Kitap Ekle" depending on the language in force.

English is the ground truth. Every other language is read on top of it, so a
key a translator has not got to yet falls back to English rather than showing
its own name -- a screen half in Turkish reads better than one with "nav_add"
on a button.

Adding a language is adding a file. The picker lists whatever is in the
folder; no code here names the languages it will ever have.
"""

import json
import logging

from shared.paths import assets_dir

logger = logging.getLogger("katipcelebi")

# The one language guaranteed to be complete: the app is written in it, and
# every other file is checked against it.
BASE = "en"

_loaded: dict = {}  # code -> {key: phrase}
_current = BASE


def lang_dir():
    return assets_dir() / "lang"


def _read(code: str) -> dict:
    """One language file as a dict, or empty if it cannot be read."""
    path = lang_dir() / (code + ".json")
    if not path.is_file():
        # Not there is not a problem worth a stack trace: it is how "switch to
        # a language we do not ship" is answered.
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        logger.warning("Could not read language file %s", path, exc_info=True)
        return {}
    return data if isinstance(data, dict) else {}


def _english() -> dict:
    if BASE not in _loaded:
        _loaded[BASE] = _read(BASE)
    return _loaded[BASE]


def available() -> list:
    """The languages there are files for, as (code, name), English first.

    Sorted so the list is stable, but with English at the head: it is the one
    that is always complete, and the sensible thing to fall back to by eye.
    """
    found = []
    for path in sorted(lang_dir().glob("*.json")):
        code = path.stem
        data = _read(code)
        if data:
            found.append((code, data.get("_name", code)))
    found.sort(key=lambda pair: (pair[0] != BASE, pair[0]))
    return found


def current() -> str:
    return _current


def use(code: str) -> str:
    """Switch to a language. Returns the one actually in force.

    An unknown code, or one with no file, leaves English in force rather than
    a screen full of untranslated keys.
    """
    global _current
    if code == BASE:
        _current = BASE
        return _current
    if code not in _loaded:
        _loaded[code] = _read(code)
    _current = code if _loaded.get(code) else BASE
    return _current


def text(key: str) -> str:
    """The phrase for a key, in the language in force.

    Falls through to English for a key the current language is missing, and to
    the key itself only when even English has never heard of it -- which is a
    bug in the code, not a gap in a translation, and is caught by the tests.
    """
    if _current != BASE:
        phrase = _loaded.get(_current, {}).get(key)
        if phrase is not None:
            return phrase
    english = _english()
    if key in english:
        return english[key]
    logger.error("No text for %r", key)
    return key


def field_label(field_name: str) -> str:
    """The label for one of Book's fields."""
    return text("field_" + field_name)


# The English dictionary, for the tests and anything that needs the ground
# truth directly. Read from the file, so there is one source and not two.
ENGLISH = {k: v for k, v in _english().items() if not k.startswith("_")}
  01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001

# 01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001
