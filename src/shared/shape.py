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

"""How round things are, and how big the words are.

The other half of Material 3 Expressive. The colour engine gives us the
palette; the shape scale and the type scale are Google's too, but they live in
a stylesheet rather than in a library, so they are written out here.

Named rather than typed in place. The old stylesheet had 5px, 6px and 8px
corners and font sizes of 11, 12, 14, 15, 19, 22 and 34 -- numbers nobody
chose so much as arrived at. M3 has a scale with seven steps and a reason for
each; using it means a shape can be asked for by what it is.

No Qt in this file: it is a list of numbers and the names for them.
"""

# ------------------------------------------------------------ the corners ---
# Default spacing and radius choices: crisp, compact, and lightly rounded.
NONE = 0
EXTRA_SMALL = 4
SMALL = 6
MEDIUM = 8
LARGE = 12
EXTRA_LARGE = 16
PILL = 12
BUTTON_HEIGHT = 32
FULL = 999

# -------------------------------------------------------------- the words ---
# Default desktop type sizing: compact text with stronger hierarchy for titles.
DISPLAY_SMALL = 28
HEADLINE_SMALL = 20
TITLE_LARGE = 18
TITLE_MEDIUM = 14
BODY_LARGE = 13
BODY_MEDIUM = 12
LABEL_LARGE = 11
LABEL_SMALL = 10

# Default design leans on a strong semantic hierarchy: regular body text, medium for
# labels, semibold for headings and emphasis.
REGULAR = 400
MEDIUM = 500
BOLD = 600

METRICS = {
    "r_none": NONE,
    "r_xs": EXTRA_SMALL,
    "r_sm": SMALL,
    "r_md": MEDIUM,
    "r_lg": LARGE,
    "r_xl": EXTRA_LARGE,
    "r_pill": PILL,
    "button_h": BUTTON_HEIGHT,
    "r_full": FULL,
    "t_display": DISPLAY_SMALL,
    "t_headline": HEADLINE_SMALL,
    "t_title_lg": TITLE_LARGE,
    "t_title_md": TITLE_MEDIUM,
    "t_body_lg": BODY_LARGE,
    "t_body_md": BODY_MEDIUM,
    "t_label_lg": LABEL_LARGE,
    "t_label_sm": LABEL_SMALL,
    "w_regular": REGULAR,
    "w_medium": MEDIUM,
    "w_bold": BOLD,
}
# 01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001
