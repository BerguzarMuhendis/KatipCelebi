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

"""How many books you meant to read.

Kept with the books, not with the settings.

A goal is something the user decided, like the books themselves -- so it lives
in the library's folder and travels with it. Put in the settings file it would
be left behind the first time somebody moved their library to another machine.
"""

import logging
from pathlib import Path

from shared.storage import DataFileDamaged, read_rows, write_rows

logger = logging.getLogger("katipcelebi")

GOALS_FILENAME = "goals.json"


class Goals:
    """The yearly and monthly targets."""

    def __init__(self, folder: Path):
        self.folder = Path(folder)
        self.yearly = 0
        self.monthly = 0

    @property
    def path(self) -> Path:
        return self.folder / GOALS_FILENAME

    def load(self) -> None:
        self.yearly = 0
        self.monthly = 0
        try:
            result = read_rows(self.path)
        except DataFileDamaged:
            # A goal is the least of what the user would miss; the file has
            # been set aside, and starting at zero is honest.
            logger.error("Could not read the goals; starting from none")
            return
        for row in result.rows:
            self.yearly = _whole(row.get("yearly"), self.yearly)
            self.monthly = _whole(row.get("monthly"), self.monthly)

    def save(self) -> bool:
        # A list of one, so this file looks like every other one the app writes
        # and goes through the same careful reader and writer.
        return write_rows(self.path, [{"yearly": self.yearly, "monthly": self.monthly}])

    def set_yearly(self, target: int) -> bool:
        before = self.yearly
        self.yearly = max(0, int(target))
        if self.save():
            return True
        self.yearly = before
        return False

    def set_monthly(self, target: int) -> bool:
        before = self.monthly
        self.monthly = max(0, int(target))
        if self.save():
            return True
        self.monthly = before
        return False


def _whole(value, fallback: int) -> int:
    """A number out of the file. Anything else means the user hasn't said."""
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return fallback
# 01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001
