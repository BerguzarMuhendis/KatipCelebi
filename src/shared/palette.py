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

"""One colour in, a whole Material Design 3 palette out.

The seed is the desktop's own accent colour -- the one Windows calls "Accent
colour" and a Linux desktop sets for itself. Nobody is asked to pick it.
Everything else -- every surface, every text colour, the chart wedges -- is
worked out from it by M3's own rules, for the light theme and the dark one
separately. Nothing here is a colour somebody chose by eye, which is the
point: this is what Material You does on a phone, where the wallpaper is the
seed.

The scheme is TonalSpot, M3's everyday variant, and it deliberately calms the
seed down rather than using it raw -- #6750A4 arrives as #655789. That is not
a bug to fix; it is what makes an arbitrary accent liveable across a whole
window.

The one Qt in this file is reading that accent, which only Qt knows.
"""

import os
import re
import sys

from materialyoucolor.dynamiccolor.material_dynamic_colors import (
    MaterialDynamicColors,
)
from materialyoucolor.hct import Hct
from materialyoucolor.scheme.scheme_tonal_spot import SchemeTonalSpot

# Material 3 Expressive, Google's 2025 revision. Said out loud rather than
# left to the library's default, because the two specs are visibly different
# things and a silent change of default would repaint the whole app.
#
# It reads with less contrast than the 2021 spec did -- body text lands at
# about 12:1 on a light surface where it used to be 16:1 -- which is still
# well clear of what anyone needs to read it.
SPEC = "2025"

# M3's own baseline seed, for when there is no desktop to ask. An app with no
# answer looks like Material does.
DEFAULT_SEED = "#6750A4"

# An accent this grey has no hue worth building on: M3 would read one out of
# the rounding and paint the whole app a colour nobody chose. Below this, the
# desktop is treated as having no answer.
MIN_CHROMA = 5.0

# Our name for a colour -> the M3 role it comes from. Written out rather than
# used inline so that the whole mapping can be read at once, and so that a role
# used twice is visible as such.
ROLES = {
    "window": "surface",
    "sidebar": "surfaceContainerLow",
    "panel": "surfaceContainerLowest",
    "panel_hover": "surfaceContainerHigh",
    "border": "outlineVariant",
    "text": "onSurface",
    "text_body": "onSurface",
    "text_soft": "onSurfaceVariant",
    "accent": "primary",
    "accent_text": "onPrimary",
    "heading": "primary",
    "danger": "error",
    "cover": "surfaceContainerHigh",
    "cover_edge": "outline",
    "star_empty": "outlineVariant",
    # The stars are the one thing M3 has no role for: a rating is not a
    # surface, a text or an error. Tertiary is M3's own answer to "another
    # accent, still in the family", and it is already readable on the surface
    # it sits on in both themes.
    "star": "tertiary",
    # --- the roles the Material look is actually built from --------------
    # A filled button and the app's one main action per screen.
    "primary_container": "primaryContainer",
    "on_primary_container": "onPrimaryContainer",
    # The signature of Material navigation and the everyday "tonal" button:
    # the selected sidebar item and every ordinary button are a secondary
    # container, which is the calm, in-family fill M3 reaches for by default.
    "secondary_container": "secondaryContainer",
    "on_secondary_container": "onSecondaryContainer",
    # The five surface containers are how M3 shows depth without a shadow: the
    # further from the background, the more toned. Cards and fields sit on the
    # higher ones so they lift off the page.
    "surface_container": "surfaceContainer",
    "surface_container_high": "surfaceContainerHigh",
    "surface_container_highest": "surfaceContainerHighest",
    # The one line colour for an outlined control, distinct from the fainter
    # outline_variant used for dividers.
    "outline": "outline",
}

HEX = re.compile(r"^#?([0-9a-fA-F]{6})$")

# How many wedges a pie can want, and how far apart to put them. Primary,
# secondary and tertiary are all near neighbours under TonalSpot, so a pie
# drawn from them would be five shades of the same colour. These are the
# seed's own hue, walked around the wheel.
SLICE_COUNT = 5
SLICE_CHROMA = 48.0
SLICE_TONE_LIGHT = 45.0
SLICE_TONE_DARK = 70.0


def is_seed(text: str) -> bool:
    """Whether a person has typed something we can use as a colour."""
    return bool(HEX.match((text or "").strip()))


def clean_seed(text: str) -> str:
    """A typed colour as we store it, or the default if it is not one."""
    match = HEX.match((text or "").strip())
    return ("#" + match.group(1).upper()) if match else DEFAULT_SEED


def has_a_desktop() -> bool:
    """Whether there is a desktop with an opinion about colour.

    Windows and macOS always have one. A Linux box might be running a bare
    window manager and no desktop at all, and then Qt's "highlight" is Qt's
    own idea rather than anybody's accent -- so it is not asked.
    """
    if sys.platform in ("win32", "darwin"):
        return True
    return bool(os.environ.get("XDG_CURRENT_DESKTOP"))


def system_seed(app) -> str:
    """The desktop's accent colour, or ours when there is nobody to ask.

    This is the colour Windows shows under Personalisation > Colours, and the
    one a Linux desktop sets for itself. Qt hands it over as the palette's
    highlight, which is the same thing by another name.
    """
    if not has_a_desktop():
        return DEFAULT_SEED

    from PyQt6.QtGui import QPalette

    accent = app.palette().color(QPalette.ColorRole.Highlight).name()
    if not is_seed(accent):
        return DEFAULT_SEED
    # A grey accent is not a colour to build a palette from.
    if _hct(accent).chroma < MIN_CHROMA:
        return DEFAULT_SEED
    return clean_seed(accent)


def _hct(seed: str) -> Hct:
    return Hct.from_int(0xFF000000 | int(clean_seed(seed)[1:], 16))


def _hex(argb: int) -> str:
    return "#%06x" % (argb & 0xFFFFFF)


def build(seed: str, dark: bool) -> dict:
    """Every colour the app uses, from one seed."""
    scheme = SchemeTonalSpot(_hct(seed), dark, 0.0, spec_version=SPEC)
    return {
        name: _hex(getattr(MaterialDynamicColors, role).get_hct(scheme).to_int())
        for name, role in ROLES.items()
    }


def slices(seed: str, dark: bool) -> tuple:
    """The wedge colours for a pie, walked around the wheel from the seed."""
    start = _hct(seed).hue
    tone = SLICE_TONE_DARK if dark else SLICE_TONE_LIGHT
    step = 360.0 / SLICE_COUNT
    return tuple(
        _hex(Hct.from_hct((start + step * n) % 360.0, SLICE_CHROMA, tone).to_int())
        for n in range(SLICE_COUNT)
    )
  01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001

# 01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001
