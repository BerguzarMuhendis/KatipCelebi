# Copied from previous src/shared/theme.py, now as core module
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

"""How the app looks, in the light and in the dark.

Every colour the app uses is named here once, and the stylesheet is built from
those names. Nothing outside this file writes a colour down -- not the charts,
not the placeholder covers -- because a colour spelled out anywhere else is a
colour that stays dark when the rest of the window turns light.

The colours themselves are not chosen here either: palette.py works them all
out from the one seed the user picked, by Material Design 3's rules. This file
knows which name goes where; it does not know what purple is.
"""

import logging
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QStyleFactory

logger = logging.getLogger("katipcelebi")

from shared import palette, shape

DARK = "dark"
LIGHT = "light"

# The built-in themes, plus the retained custom QSS override.
# "Default" keeps the app's own stylesheet; "Contrast" keeps the same layout
# but swaps in a stronger light/dark contrast palette. "Custom" loads the
# user's own QSS file from the app data directory.
DEFAULT_LIGHT = "default-light"
DEFAULT_DARK = "default-dark"
# Backwards-compatible aliases for older saved settings and imports.
FLUENT_LIGHT = DEFAULT_LIGHT
FLUENT_DARK = DEFAULT_DARK
CONTRAST_LIGHT = "contrast-light"
CONTRAST_DARK = "contrast-dark"
CUSTOM = "custom"
THEMES = (DEFAULT_LIGHT, DEFAULT_DARK, CONTRAST_LIGHT, CONTRAST_DARK, CUSTOM)
DEFAULT_THEME = DEFAULT_DARK

# GNOME's own chart palette is handled by the palette engine now.

# What the app is showing right now, read by the charts and covers, which paint
# themselves rather than being styled.
_current = DARK
_family = "m3"
_seed = palette.DEFAULT_SEED
_shades = palette.build(_seed, dark=True)

# Captured once, from the app as the desktop handed it over, before any restyle
# of ours: the platform's own widget style (to return to for the M3 themes) and
# its accent colour (which switching styles would otherwise lose).
_platform_style = None
_system_seed = None


def is_dark(name: str) -> bool:
    return name.endswith(DARK)


def family(name: str) -> str:
    if name == CUSTOM:
        return "custom"
    if name.startswith("contrast"):
        return "contrast"
    return "default"


def colours() -> dict:
    """The palette in use."""
    return _shades


def colour(name: str) -> QColor:
    return QColor(_shades[name])


def slice_colours() -> tuple:
    """The wedge colours for a pie, in the palette in use."""
    return palette.slices(_seed, _current == DARK)


def current_mode() -> str:
    return _current


def current_seed() -> str:
    return _seed


# --------------------------------------------------- theme preview swatches ---
# Predefined colour triplets for each theme, used by the combo box to show a
# small swatch so the user can tell themes apart at a glance.  Each tuple is
# (background, accent, text).
_PREVIEW_COLOURS = {
    DEFAULT_LIGHT: ("#f5f5f5", "#0078d4", "#1f1f1f"),
    DEFAULT_DARK: ("#1b1b1b", "#5aa7ff", "#f5f5f5"),
    CONTRAST_LIGHT: ("#ffffff", "#0b57d0", "#000000"),
    CONTRAST_DARK: ("#000000", "#8ab4f8", "#ffffff"),
    CUSTOM: ("#f0f0f0", "#0078d7", "#000000"),
}


def theme_preview_pixmap(name: str, size: int = 20):
    """A small square pixmap showing a theme's background, accent stripe and
    text colour -- enough to tell light from dark and M3 from Adwaita at a
    glance in a combo box."""
    from PyQt6.QtGui import QIcon, QPainter, QPixmap

    bg, accent, text = _PREVIEW_COLOURS.get(name, ("#808080", "#404040", "#ffffff"))
    pm = QPixmap(size, size)
    pm.fill(QColor(bg))
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    # A vertical accent stripe on the left third.
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(accent))
    painter.drawRoundedRect(0, 0, size // 3, size, 3, 3)
    # A small text-coloured dot in the centre of the accent stripe to show
    # the contrast between accent and text.
    painter.setBrush(QColor(text))
    cx, cy = size // 6, size // 2
    painter.drawEllipse(cx - 2, cy - 2, 4, 4)
    painter.end()
    return QIcon(pm)


def system_prefers_dark(app) -> bool:
    """Whether the desktop is set to a dark theme.

    Qt only learned to answer this in 6.5; anything older gets the dark theme,
    which is what this app looked like before it had a choice.
    """
    try:
        return app.styleHints().colorScheme() == Qt.ColorScheme.Dark
    except AttributeError:
        return True


def apply_theme(app, name: str) -> str:
    """Dress the whole app in one of the supported themes.

    The default and the contrast themes follow the same app stylesheet, with a
    stronger contrast palette for the contrast variants. Custom QSS remains as a
    separate override that can still layer on top of the chosen theme.
    """
    global _current, _family, _shades
    if name not in THEMES:
        name = DEFAULT_THEME
    _capture(app)
    _current = DARK if is_dark(name) else LIGHT
    _family = family(name)
    if _family == "custom":
        _wear_custom(app)
    elif _family == "contrast":
        _wear_contrast(app, _current == DARK)
    else:
        _wear_m3(app, _current == DARK)
    return name


def _wear_contrast(app, dark: bool) -> None:
    """Strong light/dark contrast while keeping the app's own shell."""
    global _seed, _shades
    _restore_platform_style(app)
    _seed = _system_seed or palette.DEFAULT_SEED
    _shades = palette.build(_seed, dark=dark)
    _shades["window"] = "#000000" if dark else "#ffffff"
    _shades["sidebar"] = "#111111" if dark else "#f3f3f3"
    _shades["panel"] = "#121212" if dark else "#fafafa"
    _shades["border"] = "#7a7a7a" if dark else "#d1d1d1"
    _shades["text"] = "#ffffff" if dark else "#1c1c1c"
    _shades["text_body"] = _shades["text"]
    _shades["text_soft"] = "#cfcfcf" if dark else "#525252"
    _shades["accent"] = "#8ab4f8" if dark else "#0b57d0"
    _shades["accent_text"] = "#000000" if dark else "#ffffff"
    _shades["secondary_container"] = "#2d2d2d" if dark else "#eef3ff"
    _shades["on_secondary_container"] = "#ffffff" if dark else "#0b57d0"
    _shades["surface_container"] = "#1a1a1a" if dark else "#f6f6f6"
    _shades["surface_container_high"] = "#202020" if dark else "#ffffff"
    _shades["outline"] = _shades["border"]
    app.setStyleSheet(stylesheet())


# ------------------------------------------------------------ custom QSS ---
def _wear_custom(app) -> None:
    """Apply the user's custom QSS file. Falls back to the Default dark theme
    if the file does not exist or cannot be read."""
    global _seed, _shades
    qss = load_custom_qss()
    if qss:
        _restore_platform_style(app)
        _seed = palette.DEFAULT_SEED
        _shades = palette.build(_seed, dark=True)
        app.setStyleSheet(qss)
    else:
        logger.warning("Custom QSS not found; falling back to Default dark")
        _wear_m3(app, True)


# --------------------------------------------------- custom QSS loading ---
from pathlib import Path as _Path


def _qss_styles_dir() -> _Path:
    """The directory that ships with the app, containing default.qss."""
    bundled = getattr(sys, "_MEIPASS", None)
    if bundled:
        return _Path(bundled) / "assets" / "styles"
    return _Path(__file__).resolve().parent.parent.parent / "assets" / "styles"


def _qss_user_path() -> _Path:
    """The user's custom QSS file in the app data directory."""
    from shared.paths import app_data_dir

    return app_data_dir() / "custom.qss"


def load_custom_qss() -> str:
    """Load the user's custom QSS, falling back to the shipped default.

    Priority:  custom.qss in app data  >  assets/styles/default.qss  >  ""
    The file is read as UTF-8 and a %(key)s substitution is performed so the
    QSS can reference the app's accent colour, background, etc.
    """
    user = _qss_user_path()
    default = _qss_styles_dir() / "default.qss"

    path = user if user.exists() else default
    if not path.exists():
        return ""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    # Substitute %(var)s tokens with live values from the current palette.
    tokens = {
        "accent": _shades.get("accent", "#0078d7"),
        "accent_text": _shades.get("accent_text", "#ffffff"),
        "window": _shades.get("window", "#f0f0f0"),
        "text": _shades.get("text", "#000000"),
        "text_soft": _shades.get("text_soft", "#606060"),
        "border": _shades.get("border", "#c0c0c0"),
        "sidebar": _shades.get("sidebar", "#e8e8e8"),
        "danger": _shades.get("danger", "#c42b1c"),
        "cover": _shades.get("cover", "#ffffff"),
        "star": _shades.get("star", "#e6a800"),
    }
    try:
        return raw % tokens
    except (KeyError, TypeError):
        return raw


def apply_custom_qss(app) -> None:
    """Apply the user's custom QSS on top of the current theme.

We created core.py. Now need __init__.py file to re-export names. Create it. Then run pytest. Let's create __init__.py. !*** Proceed.**