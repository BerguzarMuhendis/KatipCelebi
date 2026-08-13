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

    Call this after apply_theme().  If custom.qss exists it overrides the
    built-in stylesheet; if not, the base theme's stylesheet stays.
    """
    qss = load_custom_qss()
    if qss:
        # Prepend to any existing stylesheet so Qt properties still work.
        existing = app.styleSheet()
        app.setStyleSheet(qss + "\n" + existing)


def _capture(app) -> None:
    """Remember, once, what the desktop gave us before we restyle anything."""
    global _platform_style, _system_seed
    if _platform_style is None:
        try:
            _platform_style = app.style().name()
        except (
            Exception
        ):  # noqa: BLE001 - pragma: no cover - a Qt without QStyle.name()
            _platform_style = ""
        _system_seed = palette.system_seed(app)


# -------------------------------------------------------------- the M3 two ---
def _wear_m3(app, dark: bool) -> None:
    global _seed, _shades
    _restore_platform_style(app)  # undo any native restyle first
    _seed = _system_seed or palette.DEFAULT_SEED
    _shades = palette.build(_seed, dark=dark)

    if dark:
        _shades["window"] = "#1b1a19"
        _shades["sidebar"] = "#1f1f1f"
        _shades["panel"] = "#2b2b2b"
        _shades["border"] = "#3a3a3a"
        _shades["text"] = "#f3f2f1"
        _shades["text_body"] = "#f3f2f1"
        _shades["text_soft"] = "#d1d1d1"
        _shades["accent"] = "#60a5fa"
        _shades["accent_text"] = "#08131d"
        _shades["secondary_container"] = "#2d2d2d"
        _shades["on_secondary_container"] = "#f3f2f1"
        _shades["surface_container"] = "#1f1f1f"
        _shades["surface_container_high"] = "#2b2b2b"
        _shades["outline"] = "#4b4b4b"
    else:
        _shades["window"] = "#f3f2f1"
        _shades["sidebar"] = "#f5f5f5"
        _shades["panel"] = "#ffffff"
        _shades["border"] = "#d1d1d1"
        _shades["text"] = "#201f1e"
        _shades["text_body"] = "#201f1e"
        _shades["text_soft"] = "#5c5c5c"
        _shades["accent"] = "#0078d4"
        _shades["accent_text"] = "#ffffff"
        _shades["secondary_container"] = "#eef5ff"
        _shades["on_secondary_container"] = "#004578"
        _shades["surface_container"] = "#ffffff"
        _shades["surface_container_high"] = "#f5f5f5"
        _shades["outline"] = "#d1d1d1"

    app.setStyleSheet(stylesheet())


def _restore_platform_style(app) -> None:
    style = QStyleFactory.create(_platform_style) if _platform_style else None
    if style is not None:
        app.setStyle(style)


def _shades_from_palette(pal: QPalette, dark: bool) -> dict:
    """Fill every name the charts, covers and icons read from the live palette,
    so the self-painted parts match whatever the native style is wearing."""
    role = QPalette.ColorRole

    def c(r):
        return pal.color(r).name()

    window, base, alt = c(role.Window), c(role.Base), c(role.AlternateBase)
    text, dim, border = (
        c(role.WindowText),
        c(role.PlaceholderText),
        c(role.Mid),
    )
    accent, on_accent = c(role.Highlight), c(role.HighlightedText)
    button = c(role.Button)
    return {
        "window": window,
        "sidebar": alt,
        "panel": base,
        "panel_hover": alt,
        "border": border,
        "text": text,
        "text_body": text,
        "text_soft": dim,
        "accent": accent,
        "accent_text": on_accent,
        "heading": accent,
        "danger": "#ff938c" if dark else "#c01c28",
        "cover": alt,
        "cover_edge": border,
        "star_empty": border,
        "star": "#f5c211" if dark else "#e5a50a",
        "primary_container": alt,
        "on_primary_container": text,
        "secondary_container": alt,
        "on_secondary_container": text,
        "surface_container": alt,
        "surface_container_high": button,
        "surface_container_highest": alt,
        "outline": border,
    }


def _mix(base_hex: str, over_hex: str, alpha: float) -> str:
    """`over` laid on `base` at `alpha` opacity, as an opaque hex colour.

    Material's state layers are a translucent film of the "on" colour over a
    container -- 8% on hover, 11% on press. Qt's stylesheet cannot stack a
    translucent layer on a widget the way the spec draws it, so the film is
    flattened into one solid colour here, which comes out the same to the eye.
    """
    base, over = QColor(base_hex), QColor(over_hex)
    return QColor(
        round(base.red() * (1 - alpha) + over.red() * alpha),
        round(base.green() * (1 - alpha) + over.green() * alpha),
        round(base.blue() * (1 - alpha) + over.blue() * alpha),
    ).name()


# The two state-layer opacities M3 uses, named so the intent is legible.
HOVER = 0.08
PRESS = 0.11

# The blanks the stylesheet asks for that are neither a palette colour nor a
# shape metric: the state-layer shades and the chevron picture, all worked out
# in _tokens(). Named here so the palette test can prove every blank in the
# template is answered without standing up a QApplication to paint the arrow.
_DERIVED_NAMES = frozenset(
    {
        "tonal_hover",
        "tonal_press",
        "filled_hover",
        "filled_press",
        "nav_hover",
        "card_hover",
        "danger_hover",
        "scroll_handle",
        "scroll_handle_hover",
        "chevron",
    }
)


def _chevron(colour_hex: str) -> str:
    """A small downward chevron, painted in `colour_hex`, as a file URL.

    A combo box's arrow is a picture, not a colour a stylesheet can set, so
    Qt's own arrow cannot follow the theme. This draws M3's chevron in the
    right colour and hands back a path the stylesheet can point at; it is
    redrawn whenever the theme is, next to the settings file.
    """
    from PyQt6.QtCore import QPointF
    from PyQt6.QtGui import QPainter, QPen, QPixmap

    from shared.paths import app_data_dir

    pm = QPixmap(24, 24)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(colour_hex))
    pen.setWidth(2)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.drawLine(QPointF(7, 10), QPointF(12, 15))
    painter.drawLine(QPointF(12, 15), QPointF(17, 10))
    painter.end()
    path = app_data_dir() / "chevron.png"
    pm.save(str(path), "PNG")
    return str(path).replace("\\", "/")


def _tokens() -> dict:
    """Every blank the stylesheet has: the palette, the shape and type scale,
    the state-layer shades worked out from them, and the arrow picture."""
    s = _shades
    derived = {
        # Tonal (filled-tonal) button: a secondary container, filmed over.
        "tonal_hover": _mix(
            s["secondary_container"], s["on_secondary_container"], HOVER
        ),
        "tonal_press": _mix(
            s["secondary_container"], s["on_secondary_container"], PRESS
        ),
        # Filled (primary) button.
        "filled_hover": _mix(s["accent"], s["accent_text"], HOVER),
        "filled_press": _mix(s["accent"], s["accent_text"], PRESS),
        # An unselected sidebar item, hovered, over the sidebar's own surface.
        "nav_hover": _mix(s["sidebar"], s["text"], HOVER),
        # A book card lifting under the pointer, over the page.
        "card_hover": _mix(s["window"], s["text"], 0.05),
        # The text-style delete button: only a film of its own error colour.
        "danger_hover": _mix(s["window"], s["danger"], HOVER),
        # A scrollbar handle: the "on" colour, faint, over the page.
        "scroll_handle": _mix(s["window"], s["text"], 0.22),
        "scroll_handle_hover": _mix(s["window"], s["text"], 0.38),
        "chevron": _chevron(s["text_soft"]),
    }
    return {**s, **shape.METRICS, **derived}


def stylesheet() -> str:
    """The whole look: M3's colours for this seed, and M3's shape and type.

    One dict, because a stylesheet with two kinds of blank in it is a
    stylesheet that fails on whichever one somebody forgets.
    """
    return _TEMPLATE % _tokens()


_TEMPLATE = """
QWidget {
    background: %(window)s;
    color: %(text_body)s;
    font-family: "Segoe UI Variable", "Segoe UI", sans-serif;
    font-size: 14px;
    selection-background-color: %(accent)s;
    selection-color: %(accent_text)s;
}
QLabel { background: transparent; }

QLineEdit, QTextEdit, QComboBox, QSpinBox {
    background: %(window)s;
    border: 1px solid %(outline)s;
    color: %(text_body)s;
    selection-background-color: %(accent)s;
    selection-color: %(accent_text)s;
}
QLineEdit, QComboBox {
    border-radius: 8px;
    min-height: 32px;
    padding: 7px 12px;
}
QLineEdit:focus, QComboBox:focus, QComboBox:on {
    border: 1px solid %(accent)s;
    padding: 7px 12px;
}
QSpinBox {
    border-radius: 8px;
    min-height: 32px;
    padding: 7px 10px;
}
QTextEdit {
    border-radius: 10px;
    padding: 8px 12px;
}
QSpinBox:focus { border: 1px solid %(accent)s; padding: 7px 10px; }
QTextEdit:focus { border: 1px solid %(accent)s; padding: 7px 11px; }
QComboBox::drop-down {
    border: none;
    width: 22px;
    subcontrol-origin: padding;
    subcontrol-position: center right;
}
QComboBox::down-arrow { image: url(%(chevron)s); width: 16px; height: 16px; }
QComboBox QAbstractItemView {
    background: %(surface_container_high)s;
    border: 1px solid %(outline)s;
    border-radius: 8px;
    color: %(text_body)s;
    outline: none;
    padding: 4px;
    selection-background-color: %(secondary_container)s;
    selection-color: %(on_secondary_container)s;
}
QSpinBox::up-button, QSpinBox::down-button {
    border: none;
    background: transparent;
    width: 20px;
}

QPushButton {
    background: %(surface_container)s;
    border: 1px solid %(outline)s;
    border-radius: 8px;
    color: %(text_body)s;
    font-weight: 600;
    min-height: 32px;
    padding: 7px 16px;
}
QPushButton:hover {
    background: %(secondary_container)s;
    border-color: %(accent)s;
}
QPushButton:pressed {
    background: %(surface_container_high)s;
    border-color: %(accent)s;
}
QPushButton:disabled {
    background: %(surface_container)s;
    color: %(text_soft)s;
}
#primaryButton, QPushButton:default {
    background: %(accent)s;
    border: 1px solid %(accent)s;
    color: %(accent_text)s;
}
#primaryButton:hover, QPushButton:default:hover {
    background: #0f6cbd;
}
#primaryButton:pressed, QPushButton:default:pressed {
    background: #0b5ea8;
}
#dangerButton {
    background: transparent;
    border-color: %(danger)s;
    color: %(danger)s;
}
#dangerButton:hover { background: %(danger_hover)s; }

/* An M3 search bar: filled, fully round, no outline -- it reads as a place to
   type rather than a field to fill. */
#searchField {
    background: %(surface_container_high)s;
    border: none;
    border-radius: %(r_pill)dpx;
    min-height: 20px;
    padding: 10px 18px;
}
#searchField:focus { border: none; padding: 10px 18px; }

QCheckBox { color: %(text_body)s; }
QScrollArea { border: none; background: transparent; }

/* ------------------------------------------------------------ scrollbars ---
   Thin, rounded, no end arrows: a quiet handle that appears where the content
   overflows and says nothing otherwise. */
QScrollBar:vertical {
    background: transparent;
    width: 14px;
    margin: 0;
    border: none;
}
QScrollBar::handle:vertical {
    background: %(scroll_handle)s;
    border-radius: 4px;
    min-height: 40px;
    margin: 3px;
}
QScrollBar::handle:vertical:hover { background: %(scroll_handle_hover)s; }
QScrollBar:horizontal {
    background: transparent;
    height: 14px;
    margin: 0;
    border: none;
}
QScrollBar::handle:horizontal {
    background: %(scroll_handle)s;
    border-radius: 4px;
    min-width: 40px;
    margin: 3px;
}
QScrollBar::handle:horizontal:hover { background: %(scroll_handle_hover)s; }
QScrollBar::add-line, QScrollBar::sub-line {
    height: 0;
    width: 0;
    border: none;
}
QScrollBar::add-page, QScrollBar::sub-page { background: none; }

/* --------------------------------------------------------------- sidebar ---
   The navigation. Its selected item is a secondary-container pill: the single
   most recognisable thing about a Material app, and what the old solid-accent
   highlight was standing in for. */
#sidebar {
    background: %(sidebar)s;
    border: 1px solid %(outline)s;
    border-left: none;
}
#brandLabel {
    color: %(text)s;
    font-size: 18px;
    font-weight: 600;
}
#navButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    color: %(text_soft)s;
    font-weight: 600;
    min-height: 20px;
    padding: 10px 14px;
    text-align: left;
}
#navButton:hover {
    background: rgba(0, 120, 212, 0.08);
    color: %(text)s;
}
#navButton:checked {
    background: rgba(0, 120, 212, 0.12);
    color: %(text)s;
    font-weight: 700;
    border: 1px solid rgba(0, 120, 212, 0.22);
}

/* ------------------------------------------------------------------ pages ---
*/
#pageTitle {
    color: %(text)s;
    font-size: %(t_headline)dpx;
    font-weight: %(w_bold)d;
}
#welcomeTitle {
    color: %(text)s;
    font-size: %(t_display)dpx;
    font-weight: %(w_bold)d;
}
#pageSubtitle, #statusLabel {
    color: %(text_soft)s;
    font-size: %(t_body_md)dpx;
}
#detailFieldLabel {
    color: %(heading)s;
    font-size: %(t_label_lg)dpx;
    font-weight: %(w_bold)d;
    padding-top: 8px;
}

/* ----------------------------------------------------------------- cards ---
   A filled card: a raised surface container, no outline. Depth in M3 is a
   tone, not a line -- the card is a shade further from the background than the
   page it sits on. */
#bookCard {
    background: transparent;
    border-radius: %(r_md)dpx;
}
#bookCard:hover { background: %(card_hover)s; }
#cardName {
    color: %(text_body)s;
    font-size: %(t_label_lg)dpx;
}
#cardStars {
    color: %(star)s;
    font-size: %(t_body_md)dpx;
}
#cardBadge {
    color: %(accent)s;
    font-size: %(t_label_sm)dpx;
}
#metricCard {
    background: %(surface_container_high)s;
    border: none;
    border-radius: %(r_lg)dpx;
}
#metricValue {
    color: %(text)s;
    font-size: %(t_headline)dpx;
    font-weight: %(w_bold)d;
}
#metricCaption {
    color: %(text_soft)s;
    font-size: %(t_label_lg)dpx;
}

/* ----------------------------------------------------------------- tables ---
*/
QTableWidget, QTableView {
    background: %(surface_container)s;
    alternate-background-color: %(surface_container_high)s;
    border: none;
    border-radius: %(r_md)dpx;
    color: %(text_body)s;
    gridline-color: %(border)s;
}
QTableWidget::item, QTableView::item { padding: 6px 8px; }
/* Without this the selected row keeps the palette's own highlight, and its
   text came out unreadable -- the numbers on the person you had just clicked
   were the ones you could not read. */
QTableWidget::item:selected, QTableView::item:selected {
    background: %(secondary_container)s;
    color: %(on_secondary_container)s;
}
QHeaderView::section {
    background: %(surface_container_high)s;
    border: none;
    color: %(text_soft)s;
    font-weight: %(w_bold)d;
    padding: 10px 8px;
}
QTableCornerButton::section {
    background: %(surface_container_high)s;
    border: none;
}

/* ------------------------------------------------------------- progress ---
   A rounded track with a rounded fill, in the primary colour: M3's linear
   progress, carrying the "n of m" the goals need on top of it. */
QProgressBar {
    background: %(surface_container_highest)s;
    border: none;
    border-radius: %(r_sm)dpx;
    color: %(text_body)s;
    text-align: center;
    min-height: 22px;
}
QProgressBar::chunk {
    background: %(accent)s;
    border-radius: %(r_sm)dpx;
}
#emptyLabel {
    color: %(text_soft)s;
    font-size: %(t_body_lg)dpx;
    padding: 60px 0;
}
"""


# Adwaita/native GNOME theme support removed: application uses M3/default
# themes and Contrast; native GNOME fallbacks were unreachable and are
# intentionally removed to reduce maintenance surface.
