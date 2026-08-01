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

"""Reading and writing the user's files, without ever losing what is in them.

Everything the app owns is a JSON list of objects in a folder the user picked.
Two rules hold this together, and both were bought the hard way:

Writing is all-or-nothing. A half-written file is how a library gets destroyed,
so a write goes to a temp file next door and is then swapped in with one atomic
rename.

A file we cannot read is NOT an empty file. The two are indistinguishable to
everything downstream, and the app saves as it goes -- so an unreadable file is
about to be overwritten with nothing. It is moved aside first, under a name
that says what happened, and the caller is told.
"""

import json
import logging
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("katipcelebi")


class DataFileDamaged(Exception):
    """The file exists, but it is not something we can read.

    Carries where the original bytes were put, so the user can be told where
    their data went rather than just shown an empty window.
    """

    def __init__(self, path: Path, rescued_to: Path | None):
        super().__init__(f"{path} could not be read")
        self.path = path
        self.rescued_to = rescued_to


@dataclass(frozen=True)
class LoadResult:
    """What came out of a file, and what was wrong with it.

    `rows` is what could be read. `skipped` counts entries that were there but
    unusable -- reported rather than silently dropped, because a save would
    prune them for good.
    """

    rows: list[dict]
    skipped: int = 0


def rescue_file(path: Path) -> Path | None:
    """Move a file out of the way, never overwriting an earlier rescue.

    Returns where it went, or None if even that failed.
    """
    for suffix in [".damaged.bak"] + [
        f".damaged.{n}.bak" for n in range(1, 100)
    ]:
        candidate = path.with_name(path.name + suffix)
        if candidate.exists():
            continue  # an older rescue: it may be the better copy, leave it be
        try:
            path.rename(candidate)
            logger.error(
                "Could not read %s; moved it aside to %s", path, candidate.name
            )
            return candidate
        except OSError:
            logger.exception("Could not move the unreadable %s aside", path)
            return None
    return None


def backup_file(path: Path) -> Path | None:
    """Keep a copy of a file next to itself before we rewrite it."""
    target = path.with_name(path.name + ".bak")
    try:
        shutil.copy2(path, target)
        return target
    except OSError:
        logger.exception("Could not back up %s", path)
        return None


def read_rows(path: Path) -> LoadResult:
    """Load a JSON list of objects.

    Raises DataFileDamaged if the file is there but unreadable, having first
    moved the original somewhere safe. A file that simply isn't there is an
    empty list -- that one is not an error, it is a new library.
    """
    if not path.exists():
        return LoadResult([])
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (
        json.JSONDecodeError,
        OSError,
        ValueError,
        UnicodeDecodeError,
    ) as exc:
        logger.error("Could not read %s: %s", path, exc)
        raise DataFileDamaged(path, rescue_file(path)) from exc
    if not isinstance(data, list):
        logger.error("%s is not a JSON list", path)
        raise DataFileDamaged(path, rescue_file(path))

    rows = [item for item in data if isinstance(item, dict)]
    skipped = len(data) - len(rows)
    if skipped:
        # Entries we cannot read are still entries somebody put there. Keep the
        # file as it stands before the next save quietly prunes them.
        logger.error("%s holds %d unreadable entr(ies)", path, skipped)
        backup_file(path)
    return LoadResult(rows, skipped)


def write_atomically(path: Path, payload: str) -> None:
    """Write `payload` to `path` so a crash leaves the old file or the new one.

    Two things make that true, and both are needed:

    - the temp-file-then-rename, so a reader never sees a half-written file;
    - fsync of the temp file *before* the rename, and of the directory after,
      so the bytes are actually on the platter before the rename that points
      at them is. Without the fsync the rename can reach disk first and a
      power cut leaves a zero-length file -- the very "damaged file" the rest
      of this module is built to survive. The docstrings promised this; now it
      is delivered.

    Raises OSError on failure; the caller decides what a failed write means.
    """
    tmp_path = path.with_name(path.name + ".tmp")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(tmp_path, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    except OSError:
        # A write that dies between opening the temp and the rename -- a full
        # disk during fsync -- must not leave a half-written .tmp for the next
        # reader to trip over. The real file, if there was one, is untouched.
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    _fsync_dir(path.parent)


def _fsync_dir(folder: Path) -> None:
    """Flush a directory entry to disk, where the platform lets us.

    Windows cannot open a directory as a file descriptor and raises; there the
    rename is durable enough on its own, so a failure here is nothing to worry
    about.
    """
    try:
        fd = os.open(folder, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def write_rows(path: Path, rows: list[dict]) -> bool:
    """Write a JSON list of objects. True when it is safely on disk."""
    try:
        payload = json.dumps(rows, ensure_ascii=False, indent=2)
        write_atomically(path, payload)  # cleans up its own temp on failure
        return True
    except (OSError, TypeError, ValueError):
        logger.exception("Could not write %s", path)
        return False
