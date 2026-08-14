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

"""What your library adds up to.

Every number the statistics page shows is worked out here, from the books
themselves. Nothing is stored and nothing is cached: a total that is kept
somewhere is a total that can be wrong, and this way correcting a book
corrects the figures at once.

No Qt in this file. The page draws what these functions return.
"""

from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime

from books.model import Book
from books.reading import (
    READ,
    READING,
    WANT_TO_READ,
    parse_stamp,
    reading_days,
    status_of,
)
from shared.texts import text

TOP_HOW_MANY = 5

# How far back the time chart can look. A year is the everyday question; a
# month is for when the year is mostly one long book and hides the rest.
WINDOW_YEAR = 365
WINDOW_MONTH = 30
RECENT_WINDOWS = (WINDOW_YEAR, WINDOW_MONTH)


def _finished(books: list[Book]) -> list[Book]:
    """Books that were actually finished, and say when."""
    return [b for b in books if status_of(b) == READ and parse_stamp(b.finished_date)]


def counts_by_status(books: list[Book]) -> dict:
    """How many books are at each stage."""
    tally = Counter(status_of(book) for book in books)
    return {
        READ: tally.get(READ, 0),
        READING: tally.get(READING, 0),
        WANT_TO_READ: tally.get(WANT_TO_READ, 0),
        "not_read": tally.get("not_read", 0),
    }


def finished_in_year(books: list[Book], year: int) -> int:
    return len(
        [b for b in _finished(books) if parse_stamp(b.finished_date).year == year]
    )


def finished_in_month(books: list[Book], year: int, month: int) -> int:
    return len(
        [
            b
            for b in _finished(books)
            if parse_stamp(b.finished_date).year == year
            and parse_stamp(b.finished_date).month == month
        ]
    )


def average_days_to_finish(books: list[Book]) -> float | None:
    """How long a book usually takes. None when nothing can be measured yet.

    Only books with both stamps count: a book finished without the app watching
    has no span, and counting it as zero would flatter the average.
    """
    spans = [
        days for days in (reading_days(b) for b in _finished(books)) if days is not None
    ]
    return sum(spans) / len(spans) if spans else None


def time_spent(
    books: list[Book],
    window_days: int = WINDOW_YEAR,
    today: date | None = None,
) -> list[tuple[str, float]]:
    """Which books your reading time went into, longest first.

    Only books finished inside the window, and only ones that say when they
    were started: a book with no start date took an unknown time, and guessing
    would put a made-up number in a chart about real ones.
    """
    day = today or date.today()  # noqa: DTZ011 - the app's day is wall-clock
    out = []
    for book in _finished(books):
        finished = parse_stamp(book.finished_date)
        if (day - finished.date()).days > window_days or finished.date() > day:
            continue
        days = reading_days(book)
        if days is None or days <= 0:
            continue
        out.append((book.title or text("chart_untitled"), days))
    out.sort(key=lambda pair: (-pair[1], pair[0].casefold()))
    return out


def _split_names(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(",") if part.strip()]


def top_authors(
    books: list[Book], how_many: int = TOP_HOW_MANY
) -> list[tuple[str, int]]:
    """The authors you own most of. A book by two authors counts for both."""
    tally: Counter = Counter()
    for book in books:
        tally.update(_split_names(book.authors))
    return tally.most_common(how_many)


def top_publishers(
    books: list[Book], how_many: int = TOP_HOW_MANY
) -> list[tuple[str, int]]:
    tally: Counter = Counter()
    for book in books:
        tally.update(_split_names(book.publishers))
    return tally.most_common(how_many)


def tag_spread(
    books: list[Book], how_many: int = TOP_HOW_MANY
) -> list[tuple[str, int]]:
    """What you read, by tag."""
    from books import tags

    tally: Counter = Counter()
    for book in books:
        tally.update(tags.split_tags(book.tags))
    return tally.most_common(how_many)


@dataclass(frozen=True)
class Goal:
    """How many books you meant to read, and how many you have."""

    target: int
    done: int

    @property
    def reached(self) -> bool:
        return self.target > 0 and self.done >= self.target

    @property
    def fraction(self) -> float:
        """How far along, from 0 to 1. No target is no progress to show."""
        if self.target <= 0:
            return 0.0
        return min(1.0, self.done / self.target)


def year_goal(books: list[Book], target: int, today: date | None = None) -> Goal:
    today = today or datetime.now().date()  # noqa: DTZ005 - wall-clock, like the stamps
    return Goal(target=target, done=finished_in_year(books, today.year))


def month_goal(books: list[Book], target: int, today: date | None = None) -> Goal:
    today = today or datetime.now().date()  # noqa: DTZ005 - wall-clock, like the stamps
    return Goal(target=target, done=finished_in_month(books, today.year, today.month))
# 01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001
