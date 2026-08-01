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

"""The app's pictures: its own icon and logo, the button icons, the flags.

The button icons are Material Symbols, shipped in assets/icons (Apache 2.0 --
see the LICENSE beside them). They are single-colour drawings with no colour
of their own, so they are painted in the theme's text colour, which is also
why they have to be repainted when the theme changes: see `redress`.

Deliberately not the platform's own icons. The app follows the system for one
thing only, light or dark; everything else it draws is Material Design 3, and
a Windows floppy disk next to a Material Symbol looks like a mistake.

A missing picture is never an error. An icon is decoration -- an app that will
not start because a picture is missing is worse than an app with no picture.
"""

import logging

from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

from shared.paths import assets_dir
from shared.theme import colour

logger = logging.getLogger("katipcelebi")

APP_ICON = "katipcelebi.ico"
APP_LOGO = "katipcelebi.svg"

ICON_SIZE = 20

# The Qt property a dressed button carries, so the theme can find it again and
# repaint it. On the button rather than in a list of our own: a list would keep
# every button we ever made alive, long after its page had gone.
ICON_KEY = "katipIconKey"

# Which Material Symbol belongs on which button, keyed by the button's text
# key -- so a button and its icon are named the same thing, in one place.
ICONS = {
    "nav_add": "library_add",
    "nav_library": "book_2",
    "nav_people": "group",
    "nav_stats": "bar_chart",
    "nav_settings": "settings",
    "fetch": "search",
    "save": "save",
    "clear": "close",
    "delete_book": "delete",
    "export_button": "download",
    "import_button": "upload",
    "template_button": "description",
    "settings_move": "folder_open",
    "settings_clear_cache": "mop",
    "back": "arrow_back",
}

# Which flag stands for which language. A language is not a country -- the
# mapping is a convention for pointing at a language quickly, not a claim
# about who speaks what.
#
# Emoji, unlike every other picture here: the picker is a combo box, and a
# flag in the text needs no file to find and no size to pick.
# A flag for every language the app is built to speak, not only the ones whose
# words ship today. The picker lists what is on disk, so the extra entries sit
# unused rather than showing a flag beside a language nobody can pick -- and
# the day a translation lands, its flag is already here. The one rule the tests
# hold to is the other way round: a shipped language must have a flag, or it
# would appear in the picker with no mark and read as nameless.
FLAG_FOR_LANGUAGE = {
    "en": "🇬🇧",
    "tr": "🇹🇷",
    "es": "🇪🇸",
    "fr": "🇫🇷",
    "ru": "🇷🇺",
    "zh": "🇨🇳",
}

# (name, colour, size) -> QIcon. Painting an SVG is not free, and the same
# handful of icons is asked for on every page and again on every theme change.
_painted: dict = {}


def icons_dir():
    return assets_dir() / "icons"


def symbol(name: str, ink: str, size: int = ICON_SIZE) -> QIcon:
    """One Material Symbol, painted in `ink`. Empty if it is not there."""
    remembered = _painted.get((name, ink, size))
    if remembered is not None:
        return remembered

    path = icons_dir() / (name + ".svg")
    try:
        drawing = path.read_text(encoding="utf-8")
    except OSError:
        logger.warning("No icon at %s", path)
        return QIcon()

    # The file has no fill of its own, so it would paint black -- invisible on
    # a dark page. The colour goes on the <svg> tag, where every path inherits
    # it.
    drawing = drawing.replace("<svg ", f'<svg fill="{ink}" ', 1)
    renderer = QSvgRenderer(QByteArray(drawing.encode("utf-8")))
    if not renderer.isValid():
        logger.warning("Unreadable icon at %s", path)
        return QIcon()

    picture = QPixmap(size, size)
    picture.fill(Qt.GlobalColor.transparent)
    painter = QPainter(picture)
    renderer.render(painter)
    painter.end()

    icon = QIcon(picture)
    _painted[(name, ink, size)] = icon
    return icon


def button_icon(key: str) -> QIcon:
    """The picture for a button, in the colour the theme is wearing now."""
    name = ICONS.get(key)
    return symbol(name, colour("text_body").name()) if name else QIcon()


def dress(button, key: str):
    """Put a button's icon on it, and remember which one it was.

    Returns the button, so it can be dressed where it is made.
    """
    if key not in ICONS:
        return button
    button.setProperty(ICON_KEY, key)
    button.setIcon(button_icon(key))
    return button


def redress(root) -> int:
    """Repaint every icon under `root` in the theme's colour. Returns how many.

    The stylesheet finds every widget on its own, but an icon is a picture that
    was painted once, in a colour that has just stopped being right.
    """
    from PyQt6.QtWidgets import QAbstractButton

    done = 0
    for button in root.findChildren(QAbstractButton):
        key = button.property(ICON_KEY)
        if key:
            button.setIcon(button_icon(key))
            done += 1
    return done


def app_icon() -> QIcon:
    """The icon for the window and the taskbar. Empty if it is not there."""
    path = assets_dir() / APP_ICON
    if not path.is_file():
        logger.warning("No app icon at %s", path)
        return QIcon()
    return QIcon(str(path))


def logo(size: int) -> QPixmap:
    """The logo, square, at the size asked for. Empty if it is not there."""
    path = assets_dir() / APP_LOGO
    if not path.is_file():
        logger.warning("No logo at %s", path)
        return QPixmap()
    return QIcon(str(path)).pixmap(size, size)


def flag(language: str) -> str:
    """The flag beside a language's name in the picker.

    Empty for a language we have no flag for -- the name alone still picks it.
    """
    return FLAG_FOR_LANGUAGE.get(language, "")


def with_flag(language: str, name: str) -> str:
    """A language's name in the picker, flag first."""
    mark = flag(language)
    return f"{mark}  {name}" if mark else name
