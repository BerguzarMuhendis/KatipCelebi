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

"""Where a book is in the reading of it, and how long that took.

No Qt: what a status means and how long a book took are worked out here, and
tested here.
"""

from dataclasses import replace
from datetime import datetime

from books.model import Book
from shared.texts import text

NOT_READ = "not_read"
WANT_TO_READ = "want_to_read"
READING = "reading"
READ = "read"

STATUSES = (NOT_READ, WANT_TO_READ, READING, READ)
STATUS_ANY = "any"  # for the filter row


def now() -> str:
    # Wall-clock time, deliberately naive: the stamps are local records, and
    # parse_stamp strips any offset on the way back in.
    return datetime.now().isoformat(timespec="seconds")  # noqa: DTZ005


def parse_stamp(stamp: str) -> datetime | None:
    """A stored timestamp, or None. The file can be edited by hand.

    The offset is dropped if one is there. The app writes naive stamps, but a
    hand-editor might put a UTC offset on one date and not another, and
    comparing an aware datetime with a naive one raises -- which used to take
    the whole statistics page down over one edited book.
    """
    try:
        parsed = datetime.fromisoformat((stamp or "").strip())
    except (TypeError, ValueError):
        return None
    return parsed.replace(tzinfo=None) if parsed.tzinfo else parsed


def as_date(stamp: str) -> str:
    return (stamp or "")[:10]


def status_of(book: Book) -> str:
    """The book's status, defaulting to not-read for anything unrecognised."""
    value = book.status.strip()
    return value if value in STATUSES else NOT_READ


# ------------------------------------------------------------ the buttons ---
def start_reading(book: Book) -> Book:
    """Begin a book: today, and the finish line cleared.

    Starting again after finishing is a re-read, so the old finish date goes --
    otherwise the book would read as started today and finished last year.
    """
    return replace(book, status=READING, started_date=now(), finished_date="")


def finish_reading(book: Book) -> Book:
    """Finish a book. A book finished without ever being started gets both
    stamps, because "I read this" is true whether or not the app was watching.
    """
    started = book.started_date or now()
    return replace(book, status=READ, started_date=started, finished_date=now())


def next_step(book: Book) -> str:
    """What the one button on the book's page should do next."""
    status = status_of(book)
    if status == READING:
        return READ
    if status == READ:
        return READING  # read it again
    return READING


# ------------------------------------------------------------ how long it ---
def reading_days(book: Book) -> float | None:
    """How long the book took, in days. None when we cannot say."""
    started = parse_stamp(book.started_date)
    finished = parse_stamp(book.finished_date)
    if started is None or finished is None or finished < started:
        return None
    return (finished - started).total_seconds() / 86400.0


def duration_parts(days: float) -> tuple[int, int, int]:
    """A span in days, as whole days, hours and minutes."""
    total_minutes = round(days * 24 * 60)
    return (
        total_minutes // 1440,
        (total_minutes % 1440) // 60,
        total_minutes % 60,
    )


def format_duration(days: float | None) -> str:
    """How long a book took, said the way a person would say it.

    At most two units, largest first: "5 days", "2 days 6 hours", "45 minutes".
    This answers "how long did it take", which is not a stopwatch reading -- it
    never counts seconds, and it never rounds 45 minutes up to a day.
    """
    if days is None:
        return text("duration_unknown")
    whole_days, hours, minutes = duration_parts(days)
    if whole_days == 0 and hours == 0 and minutes == 0:
        return text("duration_under_minute")

    parts = []
    if whole_days:
        parts.append(text("duration_days").format(n=whole_days))
    if hours and len(parts) < 2:
        parts.append(text("duration_hours").format(n=hours))
    if minutes and len(parts) < 2 and not whole_days:
        # Minutes next to days is noise: nobody says "5 days and 3 minutes"
        # about a book.
        parts.append(text("duration_minutes").format(n=minutes))
    return " ".join(parts)
  01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001

# 01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001
