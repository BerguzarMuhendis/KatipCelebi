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

# The six themes, and the family each belongs to. The two M3 themes are the
# app's own Material look: our stylesheet, built from the desktop's accent. The
# two Adwaita themes use adwaita-qt to draw native GNOME widgets -- our
# stylesheet is taken off and the platform's own widget style is left to draw,
# so on a GNOME desktop the app looks like a GNOME app rather than like itself.
# The "system" theme follows the desktop's light/dark preference using the
# native style -- per GNOME HIG, apps should offer light, dark, and
# follow-system as the three standard options.  "Custom" loads the user's own
# QSS file from the app data directory.
M3_LIGHT = "m3-light"
M3_DARK = "m3-dark"
ADWAITA_LIGHT = "adwaita-light"
ADWAITA_DARK = "adwaita-dark"
SYSTEM = "system"
CUSTOM = "custom"
THEMES = (M3_LIGHT, M3_DARK, ADWAITA_LIGHT, ADWAITA_DARK, SYSTEM, CUSTOM)
DEFAULT_THEME = M3_DARK

# GNOME's own chart palette, for the pie wedges when a native theme is on: five
# hues from the standard GNOME colour palette, a touch lighter in the dark.
_GNOME_SLICES_LIGHT = ("#3584e4", "#2ec27e", "#f5c211", "#ff7800", "#9141ac")
_GNOME_SLICES_DARK = ("#62a0ea", "#57e389", "#f8e45c", "#ffa348", "#dc8add")
_ADWAITA_ACCENT = "#3584e4"  # GNOME blue, when there is no desktop accent

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
    if name.startswith("adwaita") or name == SYSTEM:
        return "adwaita"
    return "m3"


def colours() -> dict:
    """The palette in use."""
    return _shades


def colour(name: str) -> QColor:
    return QColor(_shades[name])


def slice_colours() -> tuple:
    """The wedge colours for a pie, in the palette in use."""
    if _family == "adwaita":
        return _GNOME_SLICES_DARK if _current == DARK else _GNOME_SLICES_LIGHT
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
    M3_LIGHT: ("#fef7ff", "#6750a4", "#1d1b20"),
    M3_DARK: ("#141218", "#d0bcff", "#e6e0e9"),
    ADWAITA_LIGHT: ("#ffffff", "#3584e4", "#000000"),
    ADWAITA_DARK: ("#241f31", "#62a0ea", "#ffffff"),
    SYSTEM: ("#241f31", "#3584e4", "#ffffff"),
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
    """Dress the whole app in one of the five themes. Returns the name used.

    M3 is our stylesheet over the platform's widget style. Adwaita is the
    opposite: the stylesheet comes off and the platform style draws, so on
    GNOME the app looks like a GNOME app. The "system" theme follows the
    desktop's own light/dark preference using the native style, per GNOME HIG
    guidelines. Either way the charts and covers -- which paint themselves --
    are handed the colours that ended up in force, so nothing is left the wrong
    colour.
    """
    global _current, _family, _shades
    if name not in THEMES:
        name = DEFAULT_THEME
    _capture(app)
    if name == SYSTEM:
        _current = DARK if system_prefers_dark(app) else LIGHT
    elif name == CUSTOM:
        _current = DARK if is_dark(name) else LIGHT
    else:
        _current = DARK if is_dark(name) else LIGHT
    _family = family(name)
    if _family == "custom":
        _wear_custom(app)
    elif _family == "adwaita":
        _shades = _wear_native(app, _current == DARK)
    else:
        _wear_m3(app, _current == DARK)
    return name


# ------------------------------------------------------------ custom QSS ---
def _wear_custom(app) -> None:
    """Apply the user's custom QSS file.  Falls back to M3 dark if the file
    does not exist or cannot be read."""
    global _seed, _shades
    qss = load_custom_qss()
    if qss:
        _restore_platform_style(app)
        _seed = palette.DEFAULT_SEED
        _shades = palette.build(_seed, dark=True)
        app.setStyleSheet(qss)
    else:
        logger.warning("Custom QSS not found; falling back to M3 dark")
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
        except Exception:  # noqa: BLE001 - pragma: no cover - a Qt without QStyle.name()
            _platform_style = ""
        _system_seed = palette.system_seed(app)


# -------------------------------------------------------------- the M3 two ---
def _wear_m3(app, dark: bool) -> None:
    global _seed, _shades
    _restore_platform_style(app)  # undo any native restyle first
    _seed = _system_seed or palette.DEFAULT_SEED
    _shades = palette.build(_seed, dark=dark)
    app.setStyleSheet(stylesheet())


def _restore_platform_style(app) -> None:
    style = QStyleFactory.create(_platform_style) if _platform_style else None
    if style is not None:
        app.setStyle(style)


# --------------------------------------------------------- the native two ---
def _wear_native(app, dark: bool) -> dict:
    """Take our stylesheet off and let adwaita-qt draw. If adwaita-qt is not
    installed, renders libadwaita's look with an own stylesheet instead."""
    global _seed, _shades
    keys = {k.lower(): k for k in QStyleFactory}
    want = "adwaita-dark" if dark else "adwaita"
    if want not in keys:
        # adwaita-qt is not installed -- render libadwaita's look ourselves.
        _restore_platform_style(app)
        _seed = _ADWAITA_ACCENT
        _shades = _adwaita_shades(dark)
        app.setStyleSheet(adwaita_stylesheet())
        return _shades
    app.setStyleSheet("")
    app.setStyle(QStyleFactory.create(keys[want]))
    _seed = (
        _system_seed
        if _system_seed and _system_seed != palette.DEFAULT_SEED
        else _ADWAITA_ACCENT
    )
    # The Adwaita style ships its own light and dark palette; trust it.
    pal = app.style().standardPalette()
    app.setPalette(pal)
    return _shades_from_palette(pal, dark)


def _adwaita_shades(dark: bool) -> dict:
    """Map the Adwaita fallback palette into the names charts/covers use."""
    p = _AWAITA_PALETTE_DARK if dark else _AWAITA_PALETTE_LIGHT
    return {
        "window": p["window"],
        "sidebar": p["sidebar_bg"],
        "panel": p["view_bg"],
        "panel_hover": p["card_bg"],
        "border": p["border"],
        "text": p["text"],
        "text_body": p["text"],
        "text_soft": p["text_dim"],
        "accent": p["accent"],
        "accent_text": p["accent_text"],
        "heading": p["accent"],
        "danger": p["danger"],
        "cover": p["card_bg"],
        "cover_edge": p["border"],
        "star_empty": p["star_empty"],
        "star": p["star"],
        "primary_container": p["accent"],
        "on_primary_container": p["accent_text"],
        "secondary_container": p["button_bg"],
        "on_secondary_container": p["button_text"],
        "surface_container": p["card_bg"],
        "surface_container_high": p["header_bg"],
        "surface_container_highest": p["view_bg"],
        "outline": p["border"],
    }


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
    font-size: %(t_body_lg)dpx;
}
/* A label paints no background of its own: it shows whatever it sits on. The
   base rule above would otherwise have every label paint the window colour,
   which on a card -- a surface a shade lighter -- left the number and its
   caption on a mismatched panel the shape of the text. */
QLabel { background: transparent; }

/* ---------------------------------------------------------------- fields ---
   M3 outlined text field: a one-pixel outline that thickens to two in the
   primary colour when it has focus, on a corner softer than a box but far
   short of the pill the buttons wear. */
QLineEdit, QTextEdit, QComboBox, QSpinBox {
    background: %(window)s;
    border: 1px solid %(outline)s;
    color: %(text_body)s;
    selection-background-color: %(accent)s;
    selection-color: %(accent_text)s;
}
/* Single-line controls wear the same pill as the buttons, at the same 40px
   height: a dropdown sitting in a row of buttons should read as one family,
   not a box left over from before. */
QLineEdit, QComboBox {
    border-radius: %(r_pill)dpx;
    min-height: 22px;
    padding: 9px 18px;
}
QLineEdit:focus, QComboBox:focus, QComboBox:on {
    border: 2px solid %(accent)s;
    padding: 8px 17px;   /* the extra border pixel, taken from the padding */
}
/* The two a pill would spoil: a spin box keeps its up/down arrows in the very
   corners a pill would round away, and the notes box is many lines tall. Both
   take the largest rounded rectangle instead, which still belongs to the same
   family. */
QSpinBox {
    border-radius: %(r_lg)dpx;
    min-height: 22px;
    padding: 9px 12px;
}
QTextEdit {
    border-radius: %(r_lg)dpx;
    padding: 8px 12px;
}
QSpinBox:focus { border: 2px solid %(accent)s; padding: 8px 11px; }
QTextEdit:focus { border: 2px solid %(accent)s; padding: 7px 11px; }
QComboBox::drop-down {
    border: none;
    width: 28px;
    subcontrol-origin: padding;
    subcontrol-position: center right;
}
QComboBox::down-arrow { image: url(%(chevron)s); width: 20px; height: 20px; }
QComboBox QAbstractItemView {
    background: %(surface_container_high)s;
    border: none;
    border-radius: %(r_sm)dpx;
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

/* --------------------------------------------------------------- buttons ---
   Every ordinary button is a filled-tonal pill -- M3's calm, in-family fill.
   The one main action per screen is filled in the primary colour instead, and
   the delete button is text only: an action that undoes nothing should be
   findable, not inviting. */
QPushButton {
    background: %(secondary_container)s;
    border: none;
    border-radius: %(r_pill)dpx;
    color: %(on_secondary_container)s;
    font-weight: %(w_medium)d;
    min-height: 22px;   /* 22 + 2*9 padding = 40px, met by the 20px radius */
    padding: 9px 22px;
}
QPushButton:hover { background: %(tonal_hover)s; }
QPushButton:pressed { background: %(tonal_press)s; }
QPushButton:disabled {
    background: %(surface_container)s;
    color: %(text_soft)s;
}
#primaryButton, QPushButton:default {
    background: %(accent)s;
    color: %(accent_text)s;
}
#primaryButton:hover, QPushButton:default:hover {
    background: %(filled_hover)s;
}
#primaryButton:pressed, QPushButton:default:pressed {
    background: %(filled_press)s;
}
#dangerButton {
    background: transparent;
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
    border: none;
}
#brandLabel {
    color: %(text)s;
    font-size: %(t_title_lg)dpx;
    font-weight: %(w_bold)d;
}
#navButton {
    background: transparent;
    border: none;
    border-radius: %(r_pill)dpx;
    color: %(text_soft)s;
    font-weight: %(w_medium)d;
    min-height: 20px;
    padding: 10px 18px;
    text-align: left;
}
#navButton:hover { background: %(nav_hover)s; color: %(text)s; }
#navButton:checked {
    background: %(secondary_container)s;
    color: %(on_secondary_container)s;
    font-weight: %(w_bold)d;
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


# ------------------------------------------------ adwaita fallback (no adwaita-qt) ---
# When adwaita-qt is not installed we render libadwaita's own look with a
# stylesheet, so the Adwaita themes still look like a GNOME app rather than
# falling back to M3.  The colours are from the official GNOME HIG palette and
# the libadwaita CSS definitions.

_AWAITA_PALETTE_LIGHT = {
    "window": "#ffffff",
    "window_bg": "#ffffff",
    "view_bg": "#ffffff",
    "header_bg": "#ebebed",
    "sidebar_bg": "#ebebed",
    "card_bg": "#ffffff",
    "text": "#2e2e2e",
    "text_dim": "#77767b",
    "text_link": "#1c71d8",
    "accent": "#3584e4",
    "accent_text": "#ffffff",
    "danger": "#e01b24",
    "border": "#deddda",
    "border_focus": "#3584e4",
    "button_bg": "#ebebed",
    "button_text": "#2e2e2e",
    "button_hover": "#d5d5d5",
    "button_border": "#c0bfbc",
    "suggested_bg": "#3584e4",
    "suggested_text": "#ffffff",
    "suggested_hover": "#2c71c7",
    "nav_selected": "#d5d5d5",
    "nav_hover": "#d9d9d9",
    "scrollbar_handle": "#c0bfbc",
    "scrollbar_hover": "#a0a0a0",
    "star": "#e5a50a",
    "star_empty": "#deddda",
    "table_header": "#f6f5f4",
    "table_alt": "#f6f5f4",
    "table_select_bg": "#3584e4",
    "table_select_text": "#ffffff",
    "badge_bg": "#3584e4",
    "badge_text": "#ffffff",
    "card_hover": "rgba(0,0,0,0.06)",
}

_AWAITA_PALETTE_DARK = {
    "window": "#242424",
    "window_bg": "#242424",
    "view_bg": "#1e1e1e",
    "header_bg": "#303030",
    "sidebar_bg": "#303030",
    "card_bg": "#363636",
    "text": "#ffffff",
    "text_dim": "#77767b",
    "text_link": "#62a0ea",
    "accent": "#62a0ea",
    "accent_text": "#ffffff",
    "danger": "#ff7b6b",
    "border": "#3d3846",
    "border_focus": "#62a0ea",
    "button_bg": "#3d3846",
    "button_text": "#ffffff",
    "button_hover": "#4a4458",
    "button_border": "#4a4458",
    "suggested_bg": "#62a0ea",
    "suggested_text": "#ffffff",
    "suggested_hover": "#5090d0",
    "nav_selected": "#383838",
    "nav_hover": "#3d3d3d",
    "scrollbar_handle": "#4a4458",
    "scrollbar_hover": "#5e5c64",
    "star": "#f8e45c",
    "star_empty": "#4a4458",
    "table_header": "#363636",
    "table_alt": "#2a2a2a",
    "table_select_bg": "#62a0ea",
    "table_select_text": "#ffffff",
    "badge_bg": "#62a0ea",
    "badge_text": "#ffffff",
    "card_hover": "rgba(255,255,255,0.06)",
}


def _adwaita_fallback_tokens() -> dict:
    """Build the token dict for the Adwaita fallback stylesheet."""
    p = _AWAITA_PALETTE_DARK if _current == DARK else _AWAITA_PALETTE_LIGHT
    tokens = {**p, **shape.METRICS}
    tokens["chevron"] = _chevron(p["text_dim"])
    return tokens


def adwaita_stylesheet() -> str:
    """The libadwaita look, rendered as a Qt stylesheet."""
    return _ADWAITA_TEMPLATE % _adwaita_fallback_tokens()


_ADWAITA_TEMPLATE = """
/* ---- base ----
   libadwaita: window_bg_color, window_fg_color, card_bg_color */
QWidget {
    background: %(window_bg)s;
    color: %(text)s;
    font-size: %(t_body_lg)dpx;
}
QLabel { background: transparent; }

/* ---- fields ----
   libadwaita: entry bg = view_bg_color, border = borders,
   border-radius: 8px ($br_window), focus ring = accent_color */
QLineEdit, QTextEdit, QComboBox, QSpinBox {
    background: %(view_bg)s;
    border: 1px solid %(border)s;
    border-radius: 8px;
    color: %(text)s;
    padding: 7px 12px;
    selection-background-color: %(accent)s;
    selection-color: %(accent_text)s;
}
QLineEdit { min-height: 20px; }
QComboBox {
    min-height: 20px;
    padding: 6px 12px;
}
QLineEdit:focus, QComboBox:focus, QComboBox:on {
    border: 2px solid %(border_focus)s;
    padding: 6px 11px;
}
QSpinBox { min-height: 20px; padding: 6px 10px; }
QTextEdit { border-radius: 8px; padding: 8px 10px; }
QSpinBox:focus { border: 2px solid %(border_focus)s; padding: 5px 9px; }
QTextEdit:focus { border: 2px solid %(border_focus)s; padding: 7px 9px; }
QComboBox::drop-down {
    border: none;
    width: 28px;
    subcontrol-origin: padding;
    subcontrol-position: center right;
}
QComboBox::down-arrow { image: url(%(chevron)s); width: 16px; height: 16px; }
QComboBox QAbstractItemView {
    background: %(view_bg)s;
    border: 1px solid %(border)s;
    border-radius: 8px;
    color: %(text)s;
    outline: none;
    padding: 4px;
    selection-background-color: %(accent)s;
    selection-color: %(accent_text)s;
}
QSpinBox::up-button, QSpinBox::down-button {
    border: none;
    background: transparent;
    width: 18px;
}

/* ---- buttons ----
   libadwaita: border-radius: 8px ($br_window), flat bg = button_bg_color */
QPushButton {
    background: %(button_bg)s;
    border: 1px solid %(button_border)s;
    border-radius: 8px;
    color: %(button_text)s;
    font-weight: %(w_medium)d;
    min-height: 20px;
    padding: 7px 18px;
}
QPushButton:hover { background: %(button_hover)s; }
QPushButton:pressed { background: %(button_bg)s; }
QPushButton:disabled {
    background: %(button_bg)s;
    color: %(text_dim)s;
    border-color: %(border)s;
}
/* suggested-action (primary) button */
#primaryButton, QPushButton:default {
    background: %(suggested_bg)s;
    color: %(suggested_text)s;
    border: none;
}
#primaryButton:hover, QPushButton:default:hover {
    background: %(suggested_hover)s;
}
#primaryButton:pressed, QPushButton:default:pressed {
    background: %(suggested_bg)s;
}
/* destructive button */
#dangerButton {
    background: transparent;
    color: %(danger)s;
    border: none;
}
#dangerButton:hover { background: %(danger)s; color: %(accent_text)s; }

/* ---- search ---- */
#searchField {
    background: %(view_bg)s;
    border: 1px solid %(border)s;
    border-radius: 999px;
    min-height: 20px;
    padding: 7px 14px;
}
#searchField:focus { border-color: %(border_focus)s; }

QCheckBox { color: %(text)s; }
QScrollArea { border: none; background: transparent; }

/* ---- scrollbars ----
   libadwaita: thin, rounded, overlay style */
QScrollBar:vertical {
    background: transparent;
    width: 12px;
    margin: 0;
    border: none;
}
QScrollBar::handle:vertical {
    background: %(scrollbar_handle)s;
    border-radius: 6px;
    min-height: 36px;
    margin: 3px;
}
QScrollBar::handle:vertical:hover { background: %(scrollbar_hover)s; }
QScrollBar:horizontal {
    background: transparent;
    height: 12px;
    margin: 0;
    border: none;
}
QScrollBar::handle:horizontal {
    background: %(scrollbar_handle)s;
    border-radius: 6px;
    min-width: 36px;
    margin: 3px;
}
QScrollBar::handle:horizontal:hover { background: %(scrollbar_hover)s; }
QScrollBar::add-line, QScrollBar::sub-line {
    height: 0; width: 0; border: none;
}
QScrollBar::add-page, QScrollBar::sub-page { background: none; }

/* ---- sidebar ----
   libadwaita: headerbar bg, right border, nav rows with rounded bg */
#sidebar {
    background: %(sidebar_bg)s;
    border: none;
    border-right: 1px solid %(border)s;
}
#brandLabel {
    color: %(text)s;
    font-size: %(t_title_lg)dpx;
    font-weight: %(w_bold)d;
}
#navButton {
    background: transparent;
    border: none;
    border-radius: 8px;
    color: %(text)s;
    font-weight: %(w_medium)d;
    min-height: 20px;
    padding: 9px 16px;
    text-align: left;
}
#navButton:hover { background: %(nav_hover)s; }
#navButton:checked {
    background: %(nav_selected)s;
    font-weight: %(w_bold)d;
}

/* ---- pages ---- */
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
    color: %(text_dim)s;
    font-size: %(t_body_md)dpx;
}
#detailFieldLabel {
    color: %(text)s;
    font-size: %(t_label_lg)dpx;
    font-weight: %(w_bold)d;
    padding-top: 8px;
}

/* ---- cards ----
   libadwaita: card_bg_color, border-radius: 12px ($br_rounded) */
#bookCard {
    background: %(card_bg)s;
    border: 1px solid %(border)s;
    border-radius: 12px;
}
#bookCard:hover { background: %(card_hover)s; }
#cardName {
    color: %(text)s;
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
    background: %(card_bg)s;
    border: 1px solid %(border)s;
    border-radius: 12px;
}
#metricValue {
    color: %(text)s;
    font-size: %(t_headline)dpx;
    font-weight: %(w_bold)d;
}
#metricCaption {
    color: %(text_dim)s;
    font-size: %(t_label_lg)dpx;
}

/* ---- tables ----
   libadwaita: flat, no heavy border, row separators via gridline */
QTableWidget, QTableView {
    background: %(view_bg)s;
    alternate-background-color: %(table_alt)s;
    border: 1px solid %(border)s;
    border-radius: 8px;
    color: %(text)s;
    gridline-color: %(border)s;
}
QTableWidget::item, QTableView::item { padding: 6px 8px; }
QTableWidget::item:selected, QTableView::item:selected {
    background: %(table_select_bg)s;
    color: %(table_select_text)s;
}
QHeaderView::section {
    background: transparent;
    border: none;
    border-bottom: 1px solid %(border)s;
    color: %(text)s;
    font-weight: %(w_bold)d;
    padding: 8px 8px;
}
QTableCornerButton::section {
    background: transparent;
    border: none;
}

/* ---- progress ----
   libadwaita: thin track, accent fill */
QProgressBar {
    background: %(view_bg)s;
    border: 1px solid %(border)s;
    border-radius: 6px;
    color: %(text)s;
    text-align: center;
    min-height: 20px;
}
QProgressBar::chunk {
    background: %(accent)s;
    border-radius: 5px;
}
#emptyLabel {
    color: %(text_dim)s;
    font-size: %(t_body_lg)dpx;
    padding: 60px 0;
}
"""
