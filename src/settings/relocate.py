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

"""Moving a library from one folder to another.

All of it or none of it. The old version moved the files one at a time and
merely reported which ones failed -- so a library that stopped half way was a
library in two places, with the app still reading the half-empty one and
writing a second, diverging copy into it. Anything that fails here is put back
before this function returns.
"""

import logging
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from shared import logs
from shared.paths import (
    LIBRARY_FILENAME,
    LOANS_FILENAME,
    LOG_FILENAME,
    PEOPLE_FILENAME,
)
from stats.goals import GOALS_FILENAME

logger = logging.getLogger("katipcelebi")

# The files that are the user's library. A rescue copy travels with them: it is
# the way back to a library as it was, and worth nothing in a folder they have
# just moved out of.
DATA_FILENAMES = (
    LIBRARY_FILENAME,
    PEOPLE_FILENAME,
    LOANS_FILENAME,
    GOALS_FILENAME,
)
# Not in DATA_FILENAMES, and deliberately: neither a rescue copy nor a log
# makes a folder "already a library" -- that question is about somebody's
# books. But both travel, because a log is about the library it sits next to,
# and the rotated ones are the history.
EXTRA_PATTERNS = ("*.bak", LOG_FILENAME + "*")


@dataclass(frozen=True)
class MoveResult:
    """What happened. ``moved`` is empty whenever ``failed`` is not."""

    moved: list
    failed: list

    @property
    def ok(self) -> bool:
        return not self.failed


def files_in(folder: Path) -> list:
    """Which of our files are in this folder already."""
    return [name for name in DATA_FILENAMES if (Path(folder) / name).exists()]


def _movable(src: Path) -> list:
    names = [name for name in DATA_FILENAMES if (src / name).exists()]
    for pattern in EXTRA_PATTERNS:
        names += [p.name for p in sorted(src.glob(pattern)) if p.name not in names]
    return names


def _move_one(src: Path, dst: Path, name: str) -> None:
    # shutil.move refuses to clobber on some platforms; replace() behaves the
    # same everywhere. move() is the fallback for a different filesystem, where
    # replace() cannot work at all.
    try:
        os.replace(src / name, dst / name)
    except OSError:
        # Across filesystems move() copies then deletes; a copy that fails half
        # way (a full disk) leaves a stub at dst while the original still sits
        # at src. Left there, that stub makes the folder look like it holds a
        # library and sends the log to the wrong place. Clear it, so a failed
        # move leaves the file only where it started.
        try:
            shutil.move(str(src / name), str(dst / name))
        except OSError:
            (dst / name).unlink(missing_ok=True)
            raise


def move_library(src: Path, dst: Path) -> MoveResult:
    """Move the library. On any failure, nothing has moved.

    The log is let go of first and picked up again afterwards, wherever the
    library ended up: Windows will not move a folder that holds an open file,
    and the log is a file we are holding open in the folder being moved.
    """
    src, dst = Path(src), Path(dst)
    if src == dst:
        return MoveResult([], [])

    names = _movable(src)
    if not names:
        return MoveResult([], [])

    logs.release()
    result = MoveResult([], list(names))
    try:
        result = _move_all(src, dst, names)
    finally:
        # Point at where the library actually is, which is what the move says,
        # not what happens to be sitting in the destination folder. A move that
        # failed is put back at src -- even if a rolled-back stub lingered, the
        # log must follow the books, not the debris.
        logs.point_at(dst if result.ok else src)
    return result


def _move_all(src: Path, dst: Path, names: list) -> MoveResult:

    try:
        dst.mkdir(parents=True, exist_ok=True)
    except OSError:
        logger.exception("Could not make %s", dst)
        return MoveResult([], list(names))

    moved = []
    for name in names:
        try:
            _move_one(src, dst, name)
            moved.append(name)
        except OSError:
            logger.exception("Could not move %s to %s", name, dst)
            _put_back(moved, dst, src)
            return MoveResult([], [name])

    logger.info("Moved %d file(s) from %s to %s", len(moved), src, dst)
    return MoveResult(moved, [])


def _put_back(names: list, dst: Path, src: Path) -> None:
    """Undo the moves made so far, so a half-done move leaves no trace."""
    for name in names:
        try:
            _move_one(dst, src, name)
        except OSError:
            # Nothing left to try. Say exactly which file is where, because
            # this is the one case the user may have to sort out by hand.
            logger.exception("Could not put %s back into %s", name, src)
