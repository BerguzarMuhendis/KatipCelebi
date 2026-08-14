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

"""Where the app writes down what happened.

The log lives in the library's own folder, beside the books it is about --
so that when somebody asks what went wrong with their library, the answer is
in the same place as the library, and moving one moves the other.

It is rotated. A log nobody ever looks at is a log that grows until it is the
biggest file the user owns.
"""

import logging
import logging.handlers
import sys
from pathlib import Path

from shared.paths import LOG_FILENAME

logger = logging.getLogger("katipcelebi")

# A megabyte is a long day's use, and three of them is enough history to see
# what happened before the thing the user is asking about.
MAX_BYTES = 1_000_000
KEEP = 3

FORMAT = "%(asctime)s %(levelname)-8s %(message)s"

_file_handler = None
_console_handler = None


def point_at(folder: Path) -> bool:
    """Write the log into `folder` from now on. False if it could not.

    Safe to call again: the library can move, and the log follows it. The old
    handler is closed first, or Windows would keep the old file open and the
    folder it sits in could not be moved.
    """
    global _file_handler

    logger.setLevel(logging.INFO)
    _close_file()

    try:
        Path(folder).mkdir(parents=True, exist_ok=True)
        handler = logging.handlers.RotatingFileHandler(
            Path(folder) / LOG_FILENAME,
            maxBytes=MAX_BYTES,
            backupCount=KEEP,
            encoding="utf-8",
        )
    except OSError:
        # Nowhere to write. Say it on the console rather than lose every
        # diagnostic the app has to offer.
        _use_console()
        return False

    handler.setFormatter(logging.Formatter(FORMAT))
    logger.addHandler(handler)
    _file_handler = handler
    _drop_console()
    return True


def release() -> None:
    """Let go of the log file.

    Windows will not move a folder holding an open file, and the log sits in
    the folder the user is asking us to move.
    """
    _close_file()


def _close_file() -> None:
    global _file_handler
    if _file_handler is not None:
        logger.removeHandler(_file_handler)
        _file_handler.close()
        _file_handler = None


def _use_console() -> None:
    global _console_handler
    if _console_handler is not None:
        return
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(FORMAT))
    logger.addHandler(handler)
    _console_handler = handler


def _drop_console() -> None:
    global _console_handler
    if _console_handler is not None:
        logger.removeHandler(_console_handler)
        _console_handler.close()
        _console_handler = None
# 01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001
